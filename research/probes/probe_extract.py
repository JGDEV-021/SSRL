# W4 Probe — Cheap Deterministic Extraction on a Real Python Codebase
#
# Purpose (per research/plan.md W4): validate that a *cheap*, dependency-free
# structural fact layer is feasible on real Python code using only the stdlib
# `ast` module. This is a THROWAWAY probe, NOT the SSRL prototype. It only reads.
#
# Questions it answers:
#   Q1. Can stdlib-only parsing extract modules/classes/functions/imports/calls?
#   Q2. What fraction of calls resolve to project-local functions (call graph)?
#   Q3. How fast / robust is it on a real (messy, non-idealized) codebase?
#   Q4. Does the {nodes, edges} output shape survive contact with reality?
#
# Usage:
#   python probe_extract.py <repo_dir> [--out out.json] [--stats]

import ast
import json
import os
import sys
import time
from collections import Counter

EXCLUDE_DIRS = {".venv", "venv", "__pycache__", "node_modules", ".git", ".idea", ".vscode", "dist", "build"}


def iter_pyfiles(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def parse_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src = f.read()
    try:
        tree = ast.parse(src)
        return tree, None
    except SyntaxError as e:
        return None, f"SyntaxError@{e.lineno}: {e.msg}"


class Collector(ast.NodeVisitor):
    def __init__(self, module_id, module_path):
        self.module_id = module_id
        self.module_path = module_path
        self.functions = []      # (name, lineno, kind: module|class)
        self.call_names = []
        self.imports = []
        self._stack = []

    def _qual(self, name):
        return f"{self.module_id}::{name}"

    def visit_Import(self, node):
        for a in node.names:
            self.imports.append(("import", a.name, a.asname))

    def visit_ImportFrom(self, node):
        base = node.module or ""
        for a in node.names:
            target = a.asname or a.name
            self.imports.append(("from", f"{base}.{a.name}" if base else a.name, target))

    def visit_ClassDef(self, node):
        self._stack.append(("class", node.name))
        self.generic_visit(node)
        self._stack.pop()

    def record(self, node):
        scope = self._stack[-1] if self._stack else None
        kind = "method" if scope and scope[0] == "class" else "function"
        self.functions.append((node.name, node.lineno, kind))
        self._stack.append((kind, node.name))
        self.generic_visit(node)
        self._stack.pop()

    def visit_FunctionDef(self, node):
        self.record(node)

    def visit_AsyncFunctionDef(self, node):
        self.record(node)

    def visit_Call(self, node):
        name = None
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        elif isinstance(node.func, ast.Call):  # decorator factories like @router.get(...)
            name = "<decorator-factory>"
        self.call_names.append(name or "<expr>")
        self.generic_visit(node)


def main():
    root = sys.argv[1]
    out_path = None
    if "--out" in sys.argv:
        out_path = sys.argv[sys.argv.index("--out") + 1]

    t0 = time.time()
    files = list(iter_pyfiles(root))
    nodes, edges = [], []
    module_imports = {}   # module_id -> [ (rel_target, kind) ]
    fn_index = {}         # qualified function id -> {name, module}
    parse_errors = []
    all_calls = Counter()
    resolved_count = 0
    unresolved_samples = Counter()

    for path in files:
        rel = os.path.relpath(path, root).replace("\\", "/")
        module_id = rel[:-3].replace("/", ".")
        tree, err = parse_file(path)
        if err:
            parse_errors.append((rel, err))
            continue
        coll = Collector(module_id, rel)
        coll.visit(tree)

        nodes.append({"id": f"module::{module_id}", "type": "Module", "name": rel[:-3], "path": rel})
        for name, lineno, kind in coll.functions:
            fid = f"{module_id}::{name}"
            fn_index[fid] = {"name": name, "module": module_id}
            nodes.append({"id": f"func::{fid}", "type": "Function" if kind != "method" else "Method",
                          "name": name, "module": module_id, "line": lineno})
            edges.append({"source": f"module::{module_id}", "target": f"func::{fid}",
                          "relationship": "CONTAINS" if kind == "function" else "CONTAINS", "confidence": 1.0})

        for kind, target, alias in coll.imports:
            module_imports.setdefault(module_id, []).append((target, alias, kind))
            edges.append({"source": f"module::{module_id}", "target": f"import::{target}",
                          "relationship": "IMPORTS", "confidence": 1.0})
        all_calls.update(coll.call_names)

    # Resolve CALLS: a call name resolves to a project-local function if the
    # (unqualified) name is defined in the same module, or imported from it.
    local_names = {}
    for fid, info in fn_index.items():
        local_names.setdefault(info["name"], set()).add(info["module"])
    local_fns = {info["name"]: fid for fid, info in fn_index.items() if "::" + info["name"] + "::" in fid or True}

    # simpler: map qualified name, def-only set, plus same-module mapping
    def_map = {}   # module -> set of function names defined there
    for fid, info in fn_index.items():
        def_map.setdefault(info["module"], set()).add(info["name"])

    # second pass: link calls to targets (import-alias + cross-module resolution)
    imported_byself = {}   # module -> {call_name -> (target_module, target_symbol or None)}
    def resolve_import(target, alias, kind):
        # from X.Y import Z -> (prefix_module, symbol_Z)
        if kind == "from" and alias:
            parts = target.split(".")
            mod, sym = ".".join(parts[:-1]), parts[-1]
            return (mod, sym)
        # from X.Y import Z (alias None uses bare name)
        if kind == "from":
            parts = target.split(".")
            mod, sym = ".".join(parts[:-1]), parts[-1]
            return (mod, sym)
        # import X.Y (alias) -> first segment
        return ("", "imported:" + target)

    for path in files:
        rel = os.path.relpath(path, root).replace("\\", "/")
        module_id = rel[:-3].replace("/", ".")
        tree, _ = parse_file(path)
        if not tree:
            continue
        coll = Collector(module_id, rel)
        coll.visit(tree)
        mapping = {}
        for kind, target, alias in coll.imports:
            if kind == "from":
                parts = target.split(".")
                mod, sym = ".".join(parts[:-1]), parts[-1]
                name = alias if alias else sym
                res = (mod, sym)
                # resolve relative imports by joining with this module's package root
                if target.startswith("."):
                    depth = len(target) - len(target.lstrip("."))
                    pkg_parts = module_id.split(".")[:-1][: max(0, len(module_id.split(".")) - depth)]
                    res = (".".join(pkg_parts) + (("." + target.lstrip(".").replace("/", ".")) if target.lstrip(".") else ""), sym)
                mapping[name] = res
            else:  # import X
                bare = target.split(".")[0]
                mapping[alias if alias else bare] = ("", "imported:" + target)
        imported_byself[module_id] = mapping

        local_defined = def_map.get(module_id, set())
        for name, cnt in Counter(coll.call_names).most_common():
            if name in local_defined:
                fid = next((f for f, i in fn_index.items() if i["module"] == module_id and i["name"] == name), None)
                if fid:
                    resolved_count += cnt
                    edges.append({"source": f"module::{module_id}", "target": f"func::{fid}",
                                  "relationship": "CALLS", "confidence": 1.0})
                continue
            # cross-module: is this call an imported project symbol?
            imp = mapping.get(name)
            if imp:
                tmod, tsym = imp
                if tmod.startswith("imported:"):
                    pass  # external (stdlib/3rd-party)
                elif tsym in def_map.get(tmod, set()):
                    fid = next((f for f, i in fn_index.items() if i["module"] == tmod and i["name"] == tsym), None)
                    if fid:
                        resolved_count += cnt
                        edges.append({"source": f"module::{module_id}", "target": f"func::{fid}",
                                      "relationship": "CALLS", "confidence": 1.0})
                        continue
            unresolved_samples[name] += cnt

    dt = time.time() - t0
    stats = {
        "files": len(files),
        "parse_ok": len(files) - len(parse_errors),
        "parse_errors": parse_errors[:10],
        "nodes": len(nodes),
        "edges": len(edges),
        "functions": len(fn_index),
        "imports": sum(len(v) for v in module_imports.values()),
        "elapsed_s": round(dt, 3),
        "calls_total": sum(all_calls.values()),
        "calls_resolved_local": resolved_count,
        "calls_unresolved": sum(unresolved_samples.values()),
        "top_unresolved": unresolved_samples.most_common(15),
        "parse_error_count": len(parse_errors),
    }

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"stats": stats, "nodes": nodes, "edges": edges}, f, indent=1)
        print(f"wrote {out_path}")
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()