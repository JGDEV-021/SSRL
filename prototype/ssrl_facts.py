"""SSRL prototype — facts-first structural extractor (Phase 3).

Spec: docs/architecture.md v1.0 (ADR-001 Python, ADR-002 stdlib ast,
ADR-003 derived artifact). No AI. No semantics. Only facts.

Deterministic: same commit -> same artifact (NFR-4). Every node/edge
traces to a code location (NFR-2). Facts carry confidence 1.0.
"""

import ast
import hashlib
import json
import os
import sys
import time
import uuid
from collections import Counter


SKIP_DIRS = {".venv", "venv", "__pycache__", "node_modules", ".git", "dist", "build", "site-packages"}
SKIP_NAMES = {"conftest.py"}
NODE_TYPES = {"Repository", "Module", "Class", "Function", "Method", "Import"}
REL = {"CONTAINS", "IMPORTS", "CALLS"}


class CollectVisitor(ast.NodeVisitor):
    """First pass: collect nodes (modules, classes, funcs, methods) + raw calls."""

    def __init__(self, module_id):
        self.module_id = module_id
        self.node_id = f"module::{module_id}"
        self.functions = []      # (name, lineno, kind)
        self.classes = []        # (name, lineno)
        self.call_names = []     # call-name occurrences in this module
        self._stack = []         # "class" | "function"/"method"

    def enters(self, kind, name, lineno):
        self._stack.append((kind, name, lineno))

    def leaves(self):
        self._stack.pop()

    def visit_ClassDef(self, node):
        self.classes.append((node.name, node.lineno))
        self.enters("class", node.name, node.lineno)
        self.generic_visit(node)
        self.leaves()

    def _record_func(self, node):
        enclosing = self._stack[-1][0] if self._stack else "module"
        kind = "method" if enclosing == "class" else "function"
        parent_name = self._stack[-1][1] if enclosing == "class" else "module"
        self.functions.append((node.name, node.lineno, kind, parent_name))
        self.enters(kind, node.name, node.lineno)
        self.generic_visit(node)
        self.leaves()

    def visit_FunctionDef(self, node):
        self._record_func(node)

    def visit_AsyncFunctionDef(self, node):
        self._record_func(node)

    def visit_Call(self, node):
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Call):
            name = "<decorator-factory>"
        self.call_names.append(name or "<expr>")
        self.generic_visit(node)


def _module_id(rel_path):
    return rel_path[:-3].replace("\\", "/").replace("/", ".")


def read_module(path):
    with open(path, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()[:16]
    text = raw.decode("utf-8", errors="replace")
    return raw, digest, text


def index_corpus(root):
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if not fn.endswith(".py") or fn in SKIP_NAMES:
                continue
            full = os.path.join(dirpath, fn)
            files.append(full)
    return sorted(files)


def build_graph(root, verbose=False):
    start = time.time()
    files = index_corpus(root)
    if verbose:
        print(f"[scan] {len(files)} python files under {root}", file=sys.stderr)

    nodes = []
    edges = []
    fn_index = {}       # (module_id, name, kind) -> node id
    class_index = {}    # (module_id, name) -> node id
    module_nodes = {}   # module_id -> node id
    module_imports = {}  # module_id -> list of (kind, target, alias)
    module_calls = {}    # module_id -> list of call names

    repo_file = os.path.basename(os.path.normpath(root))
    repo_id = f"repo::{os.path.normpath(root).replace(os.sep, '/')}"
    nodes.append({
        "id": repo_id, "type": "Repository", "name": repo_file,
        "confidence": 1.0, "evidence": [{"type": "parser", "source": root}],
        "metadata": {"files": len(files)},
    })

    for path in files:
        rel = os.path.relpath(path, root).replace("\\", "/")
        mid = _module_id(rel)
        raw, digest, text = read_module(path)
        try:
            tree = ast.parse(text, filename=rel)
        except SyntaxError as e:
            nodes.append({
                "id": f"module::{mid}", "type": "Module", "name": rel,
                "confidence": 1.0,
                "evidence": [{"type": "parser", "source": f"{rel}:1"}],
                "metadata": {"parse_error": {"msg": e.msg, "lineno": e.lineno}, "sha256": digest},
            })
            edges.append({
                "id": f"e:{uuid.uuid4().hex[:8]}", "source": repo_id, "target": f"module::{mid}",
                "relationship": "CONTAINS", "confidence": 1.0,
                "evidence": [{"type": "parser", "source": f"{rel}:1"}], "metadata": {},
            })
            continue

        mid_node = f"module::{mid}"
        module_nodes[mid] = mid_node
        nodes.append({
            "id": mid_node, "type": "Module", "name": rel,
            "confidence": 1.0,
            "evidence": [{"type": "parser", "source": f"{rel}:1"}],
            "metadata": {"sha256": digest},
        })
        edges.append({
            "id": f"e:{uuid.uuid4().hex[:8]}", "source": repo_id, "target": mid_node,
            "relationship": "CONTAINS", "confidence": 1.0,
            "evidence": [{"type": "parser", "source": f"{rel}:1"}], "metadata": {},
        })

        v = CollectVisitor(mid)
        v.visit(tree)

        imports = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    imports.append(("import", a.name, a.asname))
            elif isinstance(n, ast.ImportFrom):
                base = n.module or ""
                for a in n.names:
                    imports.append(("from", f"{base}.{a.name}" if base else a.name, a.asname))
        module_imports[mid] = imports
        for kind, target, alias in imports:
            edges.append({
                "id": f"e:{uuid.uuid4().hex[:8]}",
                "source": mid_node,
                "target": f"import::{kind}:{target}" if not _is_local_prefix(target) else f"module::{_resolve_import(mid, target, kind)}",
                "relationship": "IMPORTS", "confidence": 1.0,
                "evidence": [{"type": "parser", "source": f"{rel}:{_import_line(tree, kind, target) or 1}"}],
                "metadata": {"alias": alias},
            })

        for cname, cline in v.classes:
            cid = f"class::{mid}:{cname}"
            class_index[(mid, cname)] = cid
            nodes.append({
                "id": cid, "type": "Class", "name": cname, "confidence": 1.0,
                "evidence": [{"type": "parser", "source": f"{rel}:{cline}"}], "metadata": {},
            })
            edges.append({
                "id": f"e:{uuid.uuid4().hex[:8]}", "source": mid_node, "target": cid,
                "relationship": "CONTAINS", "confidence": 1.0,
                "evidence": [{"type": "parser", "source": f"{rel}:{cline}"}], "metadata": {},
            })

        for fname, fline, kind, parent in v.functions:
            fid = f"func::{mid}:{fname}"
            fn_index[(mid, fname, kind)] = fid
            if kind == "method":
                node_type = "Method"
            elif kind == "function":
                node_type = "Function"
            else:
                node_type = kind
            nodes.append({
                "id": fid, "type": node_type, "name": fname, "confidence": 1.0,
                "evidence": [{"type": "parser", "source": f"{rel}:{fline}"}],
                "metadata": {"scope": parent, "kind": kind},
            })
            parent_node = class_index[(mid, parent)] if parent != "module" else mid_node
            edges.append({
                "id": f"e:{uuid.uuid4().hex[:8]}", "source": parent_node, "target": fid,
                "relationship": "CONTAINS", "confidence": 1.0,
                "evidence": [{"type": "parser", "source": f"{rel}:{fline}"}], "metadata": {},
            })

        module_calls[mid] = v.call_names

    link_calls(nodes, edges, fn_index, module_imports, module_calls, root, verbose)

    elapsed = time.time() - start
    stats = {
        "files": len(files),
        "parse_ok": sum(1 for n in nodes if n["type"] == "Module" and "parse_error" not in n["metadata"]),
        "parse_errors": sum(1 for n in nodes if n["type"] == "Module" and "parse_error" in n["metadata"]),
        "nodes": len(nodes),
        "edges": len(edges),
        "functions": sum(1 for n in nodes if n["type"] in ("Function", "Method")),
        "imports": sum(1 for e in edges if e["relationship"] == "IMPORTS"),
        "calls": sum(1 for e in edges if e["relationship"] == "CALLS"),
        "elapsed_s": round(elapsed, 3),
    }

    artifact = {
        "graph_version": "0.3",
        "generated_by": "ssrl-prototype-phase3",
        "nodes": nodes,
        "edges": edges,
        "stats": stats,
    }
    return artifact


def _is_local_prefix(target):
    return target.startswith(".")


def _resolve_import(mid, target, kind):
    if kind == "from":
        return mid  # placeholder, refined in link_calls
    return target.split(".")[0]


def _import_line(tree, kind, target):
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name == target for a in n.names):
            return n.lineno
        if isinstance(n, ast.ImportFrom):
            base = n.module or ""
            if kind == "from" and base and target.startswith(base):
                return n.lineno
    return None


def link_calls(nodes, edges, fn_index, module_imports, module_calls, root, verbose=False):
    """Third pass: resolve calls to project-local functions (same-module + cross-module)."""
    resolved = 0
    unresolved = Counter()
    builtins = set(dir("__builtins__")) | {
        "print", "len", "str", "int", "float", "bool", "list", "dict", "set", "tuple",
        "open", "range", "enumerate", "zip", "map", "filter", "sum", "min", "max",
        "round", "abs", "type", "isinstance", "issubclass", "getattr", "setattr",
        "hasattr", "len", "repr", "format", "sorted", "reversed", "any", "all",
        "next", "iter", "super", "property", "classmethod", "staticmethod", "vars",
        "globals", "locals", "hash", "id", "callable", "ValueError", "KeyError",
        "Exception", "RuntimeError", "TypeError", "NotImplemented",
    }

    def module_for(mid, target, kind):
        """Return (module_id, symbol) the import resolves to, or None if external."""
        if kind == "import":
            return (target.split(".")[0], None)
        if kind == "from":
            if target.startswith("."):
                return (None, None)  # relative imports of project modules
            parts = target.split(".")
            mod = ".".join(parts[:-1]) if len(parts) > 1 else ""
            return (mod, parts[-1])
        return None

    # Actually simpler: build alias -> (module_id, symbol) per module.
    for mid, imports in module_imports.items():
        local_defs = {(m, n) for (m, n, _k) in fn_index} if False else set()
        for (cmid, cname, kind), fid in fn_index.items():
            if cmid == mid:
                local_defs.add(cname)
        aliases = {}
        for kind, target, alias in imports:
            if kind == "from":
                if target.startswith("."):
                    # relative import — resolve package prefix from this module
                    depth = len(target) - len(target.lstrip("."))
                    base = ".".join(mid.split(".")[:-depth])
                    rest = target.lstrip(".")
                    full_mod = ".".join(x for x in (base, rest) if x)
                    aliases[alias if alias else rest.split(".")[-1]] = (full_mod, rest.split(".")[-1])
                else:
                    parts = target.split(".")
                    mod, sym = ".".join(parts[:-1]), parts[-1]
                    aliases[alias if alias else sym] = (mod, sym)
            else:
                aliases[alias if alias else target.split(".")[0]] = (None, target)

        for name in module_calls.get(mid, []):
            if name in local_defs:
                fid = fn_index.get((mid, name, "function")) or fn_index.get((mid, name, "method"))
                if fid:
                    resolved += 1
                    edges.append({
                        "id": f"e:{uuid.uuid4().hex[:8]}",
                        "source": f"module::{mid}", "target": fid,
                        "relationship": "CALLS", "confidence": 1.0,
                        "evidence": [], "metadata": {"resolution": "same-module"},
                    })
                    continue
            elif name in aliases:
                mod, sym = aliases[name]
                if sym in {s for (m, s, _k) in fn_index if m == mod}:
                    fid = fn_index.get((mod, sym, "function")) or fn_index.get((mod, sym, "method"))
                    if fid:
                        resolved += 1
                        edges.append({
                            "id": f"e:{uuid.uuid4().hex[:8]}",
                            "source": f"module::{mid}", "target": fid,
                            "relationship": "CALLS", "confidence": 1.0,
                            "evidence": [], "metadata": {"resolution": "cross-module"},
                        })
                        continue
            if name not in builtins:
                unresolved[name] += 1

    if verbose:
        print(f"[calls] resolved {resolved}; top unresolved {list(unresolved.most_common(5))}", file=sys.stderr)


def main(argv):
    if len(argv) < 2:
        print("usage: python src/ssrl_facts.py <repo> [--out out.json] [--verbose]", file=sys.stderr)
        return 2
    root = os.path.abspath(argv[1])
    out = None
    verbose = False
    for i, a in enumerate(argv[2:], start=2):
        if a == "--out" and i + 1 < len(argv):
            out = os.path.abspath(argv[i + 1])
        elif a == "--verbose":
            verbose = True

    artifact = build_graph(root, verbose=verbose)
    if out:
        with open(out, "w", encoding="utf-8") as f:
            json.dump(artifact, f, ensure_ascii=False, indent=1)
        print(f"wrote {out}")
    else:
        json.dump(artifact, sys.stdout, ensure_ascii=False, indent=1)
    print(json.dumps({"stats": artifact["stats"]}), file=sys.stderr) if not verbose else None
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))