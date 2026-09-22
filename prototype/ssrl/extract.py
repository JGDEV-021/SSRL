"""SSRL extractor — deterministic structural facts from Python source (ADR-002).

stdlib `ast` only. Facts: Repository, Module, Class, Function, Method +
CONTAINS / IMPORTS / CALLS relationships. Every fact carries evidence to
`file:line`. Deterministic: same commit -> same facts (NFR-4).

Includes the incremental cache (D-8): files are re-parsed only when their
sha256 content hash changes; unchanged modules contribute cached facts.
"""

import ast
import hashlib
import json
import os
import sys
import time
from collections import Counter

from . import model

SKIP_DIRS = {".venv", "venv", "__pycache__", "node_modules", ".git", "dist", "build",
             "site-packages", ".mypy_cache", ".pytest_cache"}
SKIP_NAMES = {"conftest.py"}
CACHE_VERSION = 2

BUILTINS = set(dir("__builtins__")) | {
    "print", "len", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
    "open", "range", "enumerate", "zip", "map", "filter", "sum", "min", "max",
    "round", "abs", "type", "isinstance", "issubclass", "getattr", "setattr",
    "hasattr", "repr", "format", "sorted", "reversed", "any", "all",
    "next", "iter", "super", "property", "classmethod", "staticmethod", "vars",
    "globals", "locals", "hash", "id", "callable", "ValueError", "KeyError",
    "Exception", "RuntimeError", "TypeError", "NotImplemented",
    "dataclass", "field", "abstractmethod", "asyncio",
    "__name__", "__file__", "__version__", "__all__", "__doc__",
}


class CollectVisitor(ast.NodeVisitor):
    """Per-module pass: classes, functions/methods, scoped call names, imports."""

    def __init__(self, module_id):
        self.module_id = module_id
        self.functions = []   # (name, lineno, kind, parent_name, doc)
        self.classes = []     # (name, lineno, bases)
        self.calls = []       # (enclosing_func_id or None, call_name)
        self.imports = []     # (kind, target, alias)
        self.docstring = None
        self._stack = []      # scopes: ("class", name) | ("function"/"method", name)

    def enters(self, kind, name):
        self._stack.append((kind, name))

    def leaves(self):
        self._stack.pop()

    def _scope_name(self):
        # innermost function/method scope name, else module
        for kind, name in reversed(self._stack):
            if kind in ("function", "method"):
                return name
        return None

    def visit_Module(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) \
                and isinstance(node.body[0].value.value, str):
            self.docstring = node.body[0].value.value.strip()
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        bases = []
        for b in node.bases:
            if isinstance(b, ast.Name):
                bases.append(b.id)
            elif isinstance(b, ast.Attribute):
                bases.append(b.attr)
        self.classes.append((node.name, node.lineno, bases))
        self.enters("class", node.name)
        self.generic_visit(node)
        self.leaves()

    def _func_first_statement(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) \
                and isinstance(node.body[0].value.value, str):
            return node.body[0].value.value.strip()
        return None

    def _record_func(self, node):
        enclosing = self._stack[-1][0] if self._stack else "module"
        kind = "method" if enclosing == "class" else "function"
        parent_name = self._stack[-1][1] if enclosing == "class" else "module"
        doc = self._func_first_statement(node)
        self.functions.append((node.name, node.lineno, kind, parent_name, doc))
        self.enters(kind, node.name)
        self.generic_visit(node)
        self.leaves()

    def visit_FunctionDef(self, node):
        self._record_func(node)

    def visit_AsyncFunctionDef(self, node):
        self._record_func(node)

    def visit_Call(self, node):
        scope = self._scope_name()
        name = None
        base = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
            if isinstance(node.func.value, ast.Name):
                base = node.func.value.id
            elif isinstance(node.func.value, ast.Attribute):
                root = node.func.value
                while isinstance(root, ast.Attribute):
                    root = root.value
                if isinstance(root, ast.Name):
                    base = root.id
        elif isinstance(node.func, ast.Call):
            name = "<factory>"
        self.calls.append((scope, name or "<expr>", base))
        self.generic_visit(node)

    def visit_Import(self, node):
        for a in node.names:
            self.imports.append(("import", a.name, a.asname))
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module if node.module is not None else ""
        for a in node.names:
            if module:
                target = f"{module}.{a.name}"
            else:
                target = f".{a.name}"
            self.imports.append(("from", target, a.asname))
        self.generic_visit(node)


def module_id(rel_path):
    return rel_path[:-3].replace("\\", "/").replace("/", ".")


def index_corpus(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if not fn.endswith(".py") or fn in SKIP_NAMES:
                continue
            files.append(os.path.join(dirpath, fn))
    return sorted(files)


def _sha256(raw):
    return hashlib.sha256(raw).hexdigest()[:16]


def _read(path):
    with open(path, "rb") as f:
        raw = f.read()
    return _sha256(raw), raw.decode("utf-8", errors="replace")


def _module_source(root, rel):
    with open(os.path.join(root, rel), "rb") as f:
        raw = f.read()
    return _sha256(raw), raw.decode("utf-8", errors="replace")


def _extract_module(root, rel, mid, repo_id, known_modules=None):
    """Extract one module. Returns (nodes, edges, extra)
    where extra = {"imports": [...], "calls": [...], "docstring": str|None}."""
    known_modules = known_modules or set()
    digest, text = _module_source(root, rel)
    ev = {"type": "parser", "source": f"{rel}:1"}
    try:
        tree = ast.parse(text, filename=rel)
    except SyntaxError as e:
        nodes = [{
            "id": f"module::{mid}", "type": "Module", "name": rel,
            "confidence": 1.0, "evidence": [ev],
            "metadata": {"parse_error": {"msg": e.msg, "lineno": getattr(e, "lineno", 1)}, "sha256": digest},
        }]
        edges = [model.make_edge(repo_id, f"module::{mid}", "CONTAINS", [ev])]
        return nodes, edges, {"imports": [], "calls": [], "docstring": None}

    nodes = []
    edges = []
    mid_node = f"module::{mid}"
    v = CollectVisitor(mid)
    v.visit(tree)
    nodes.append({
        "id": mid_node, "type": "Module", "name": rel,
        "confidence": 1.0, "evidence": [ev],
        "metadata": {"sha256": digest, "docstring": v.docstring},
    })
    edges.append(model.make_edge(repo_id, mid_node, "CONTAINS", [ev]))

    for kind, target, alias in v.imports:
        t_node = f"import::{kind}:{target}"
        if target.startswith("."):
            resolved = _resolve_local_import(mid, target, kind)
            t_node = f"module::{resolved}" if resolved else t_node
        elif kind == "from":
            parts = target.split(".")
            base = ".".join(parts[:-1]) if len(parts) > 1 else ""
            # local sibling module (e.g. `from db import X` where db.py exists)
            if base in known_modules:
                t_node = f"module::{base}"
            elif target in known_modules and "." not in target:
                t_node = f"module::{target}"
            else:
                # last-segment heuristics: from config import X -> config module
                first = parts[0]
                if first in known_modules:
                    t_node = f"module::{first}"
        line = next((n.lineno for n in ast.walk(tree)
                     if (isinstance(n, ast.ImportFrom) and n.module and target.startswith(n.module))
                     or (isinstance(n, ast.Import) and any(a.name == target for a in n.names))), 1)
        edges.append(model.make_edge(
            mid_node, t_node, "IMPORTS",
            [{"type": "parser", "source": f"{rel}:{line}"}], {"alias": alias}))

    for cname, cline, bases in v.classes:
        cid = model.new_id("class", mid, cname)
        nodes.append({
            "id": cid, "type": "Class", "name": cname, "confidence": 1.0,
            "evidence": [{"type": "parser", "source": f"{rel}:{cline}"}], "metadata": {"bases": bases},
        })
        edges.append(model.make_edge(mid_node, cid, "CONTAINS",
                                     [{"type": "parser", "source": f"{rel}:{cline}"}]))

    for fname, fline, kind, parent, doc in v.functions:
        fid = model.new_id("func", mid, fname)
        node_type = "Method" if kind == "method" else "Function"
        nodes.append({
            "id": fid, "type": node_type, "name": fname, "confidence": 1.0,
            "evidence": [{"type": "parser", "source": f"{rel}:{fline}"}],
            "metadata": {"kind": kind, "scope": parent, "doc": doc},
        })
        parent_node = f"class::{mid}::{parent}" if parent != "module" else mid_node
        edges.append(model.make_edge(parent_node, fid, "CONTAINS",
                                     [{"type": "parser", "source": f"{rel}:{fline}"}]))

    extra = {"imports": v.imports, "calls": v.calls, "docstring": v.docstring}
    return nodes, edges, extra


def _resolve_local_import(mid, target, kind):
    if kind != "from":
        return None
    if target.startswith("."):
        depth = len(target) - len(target.lstrip("."))
        pkg = mid.split(".")[: max(0, len(mid.split(".")) - depth)]
        rest = target.lstrip(".")
        return ".".join([*pkg, rest.split(".")[0]])
    return None


def load_cache(cache_dir):
    try:
        with open(os.path.join(cache_dir, "cache.json"), encoding="utf-8") as f:
            c = json.load(f)
        if c.get("version") == CACHE_VERSION and isinstance(c.get("files"), dict):
            return c["files"]
    except (OSError, ValueError):
        pass
    return {}


def save_cache(cache_dir, entries):
    os.makedirs(cache_dir, exist_ok=True)
    with open(os.path.join(cache_dir, "cache.json"), "w", encoding="utf-8") as f:
        json.dump({"version": CACHE_VERSION, "files": entries}, f, ensure_ascii=False)


def build(root, cache_dir=None, verbose=False):
    """Extract the full fact model (deterministic artifact). Cards:
    - nodes: Repository/Module/Class/Function/Method (confidence 1.0, evidence)
    - edges: CONTAINS/IMPORTS/CALLS (confidence 1.0)
    Uses incremental cache when cache_dir provided (D-8)."""
    start = time.time()
    files = index_corpus(root)
    repo_file = os.path.basename(os.path.normpath(root))
    repo_id = model.new_id("repo", os.path.normpath(root).replace(os.sep, "/"))

    cached = load_cache(cache_dir) if cache_dir else {}
    entries = {}
    nodes = []
    edges = []
    modules = {}          # mid -> {"imports":[...], "calls":[...], "docstring":..., "rel":rel}

    known_modules = {module_id(os.path.relpath(p, root).replace("\\", "/"))
                     for p in files}

    nodes.append({
        "id": repo_id, "type": "Repository", "name": repo_file,
        "confidence": 1.0, "evidence": [{"type": "parser", "source": os.path.normpath(root)}],
        "metadata": {"files": len(files)},
    })

    n_from_cache = 0
    n_parsed = 0
    for path in files:
        rel = os.path.relpath(path, root).replace("\\", "/")
        mid = module_id(rel)
        digest, text = _module_source(root, rel)

        hit = cached.get(rel)
        if hit and hit.get("digest") == digest:
            nodes.extend([dict(n) for n in hit["nodes"]])
            edges.extend([dict(e) for e in hit["edges"]])
            modules[mid] = hit["extra"]
            n_from_cache += 1
            entries[rel] = hit
        else:
            mn, me, extra = _extract_module(root, rel, mid, repo_id, known_modules)
            nodes.extend(mn)
            edges.extend(me)
            modules[mid] = extra
            n_parsed += 1
            entries[rel] = {"digest": digest, "nodes": mn, "edges": me, "extra": extra}

    if cache_dir:
        save_cache(cache_dir, entries)

    seen_imports = set()
    clean, dup = [], 0
    for e in edges:
        if e["relationship"] == "IMPORTS":
            key = (e["source"], e["target"])
            if key in seen_imports:
                dup += 1
                continue
            seen_imports.add(key)
        clean.append(e)
    if dup:
        edges = clean

    _link_calls(nodes, edges, modules)

    elapsed = time.time() - start
    stats = {
        "files": len(files),
        "from_cache": n_from_cache,
        "parsed": n_parsed,
        "parse_ok": sum(1 for n in nodes if n["type"] == "Module" and "parse_error" not in n["metadata"]),
        "parse_errors": sum(1 for n in nodes if n["type"] == "Module" and "parse_error" in n["metadata"]),
        "nodes": len(nodes),
        "edges": len(edges),
        "functions": sum(1 for n in nodes if n["type"] in ("Function", "Method")),
        "imports": sum(1 for e in edges if e["relationship"] == "IMPORTS"),
        "calls": sum(1 for e in edges if e["relationship"] == "CALLS"),
        "elapsed_s": round(elapsed, 3),
    }
    artifact = {"graph_version": "0.4", "generated_by": "ssrl-prototype-phase3",
                "nodes": nodes, "edges": edges, "stats": stats}
    return artifact


def _link_calls(nodes, edges, modules):
    fn_local = {}      # (mid, name) -> sorted list of node ids (module-level first)
    for n in nodes:
        if n["type"] in ("Function", "Method"):
            mid = n["id"].split("::", 2)[1]
            fn_local.setdefault((mid, n["name"]), []).append(n["id"])

    # import aliases per module
    import_targets = {}   # mid -> alias-or-name -> (target_mid, symbol|None)
    for mid, extra in modules.items():
        for kind, target, alias in extra["imports"]:
            if kind == "from":
                if target.startswith("."):
                    tmid = _resolve_local_import(mid, target, kind)
                    sym = target.lstrip(".").split(".")[-1]
                else:
                    parts = target.split(".")
                    tmid = ".".join(parts[:-1]) if len(parts) > 1 else ""
                    sym = parts[-1]
                import_targets.setdefault(mid, {})[alias if alias else sym] = (tmid, sym)
            else:
                tmid = target.split(".")[0]
                import_targets.setdefault(mid, {})[alias if alias else tmid] = (tmid, None)

    existing = {(e["source"], e["target"], e["relationship"]) for e in edges}
    resolved = 0
    unresolved = Counter()

    def resolve_call(mid, name, base=None):
        """Return (func_node_id, resolution_kind) or None."""
        if name in BUILTINS:
            return None
        local_ids = fn_local.get((mid, name))
        if local_ids:
            return local_ids[0], "same-module"
        if mid in import_targets and name in import_targets[mid]:
            tmid, sym = import_targets[mid][name]
            if sym is None:
                return None
            tid = fn_local.get((tmid, sym))
            if tid:
                return tid[0], "cross-module"
        if base and mid in import_targets and base in import_targets[mid]:
            tmid, _sym = import_targets[mid][base]
            tid = fn_local.get((tmid, name))
            if tid:
                return tid[0], "cross-module"
        return None

    for mid, extra in modules.items():
        for call in extra["calls"]:
            scope_name, name = call[0], call[1]
            base = call[2] if len(call) > 2 else None
            # caller: function node id, or module id if at module level
            if scope_name:
                src = fn_local.get((mid, scope_name))
                if not src:
                    continue
                mem = src[0]
            else:
                mem = f"module::{mid}"
            hit = resolve_call(mid, name, base)
            if hit is None:
                if name not in BUILTINS:
                    unresolved[name] += 1
                continue
            fid, res = hit
            key = (mem, fid, "CALLS")
            if key not in existing:
                edges.append(model.make_edge(
                    mem, fid, "CALLS",
                    [{"type": "call-graph", "source": "linker"}],
                    {"resolution": res}))
                existing.add(key)
            resolved += 1