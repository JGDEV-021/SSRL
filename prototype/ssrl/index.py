"""SSRL index (Phase 4) — query/base over a built artifact.

Fully deterministic. Answers are split into FACTS (confidence 1.0, off the
structural layer) and HYPOTHESES (calibrated confidence, off enrichment).

Provides the query primitives used by the Q&A projection (ADR-005 H1):
  - find(node-ish name)             locate entities by name/prefix
  - callers/callees of a function
  - imports/exports of a module
  - dependency closure (transitive)
  - reverse dependencies (what depends on me)
"""

from . import confidence as confmod


class Index:
    def __init__(self, artifact):
        self.artifact = artifact
        self.nodes = artifact["nodes"]
        self.edges = artifact["edges"]
        self.by_id = {n["id"]: n for n in self.nodes}

        # relation buckets
        self._out = {}
        self._in = {}
        for e in self.edges:
            self._out.setdefault(e["source"], []).append(e)
            self._in.setdefault(e["target"], []).append(e)

        # search by last path segment / bare name
        self._by_name = {}
        self._by_suffix = {}
        for n in self.nodes:
            if n["type"] == "Module":
                key = n["name"].rsplit("/", 1)[-1].replace(".py", "").replace(".", "/")
            else:
                key = n["name"]
            self._by_name.setdefault(key, []).append(n)

    # ---- lookups ----------------------------------------------------------

    def node(self, nid):
        return self.by_id.get(nid)

    def find(self, q, limit=20):
        """Find nodes matching a user query by name/substring (case-insensitive)."""
        ql = q.lower()
        exact = self._by_name.get(q, []) or self._by_name.get(ql, [])
        if exact:
            return exact[:limit]
        out = []
        for key, nodes in self._by_name.items():
            if ql in key.lower():
                out.extend(nodes)
                if len(out) >= limit:
                    break
        # suffix matches too
        if not out:
            for key, nodes in self._by_name.items():
                if key.lower().endswith(ql) or key.lower().startswith(ql):
                    out.extend(nodes)
                    if len(out) >= limit:
                        break
        return out[:limit]

    def children(self, nid, rel=None):
        es = self._out.get(nid, [])
        if rel:
            es = [e for e in es if e["relationship"] == rel]
        return es

    def parents(self, nid, rel=None):
        es = self._in.get(nid, [])
        if rel:
            es = [e for e in es if e["relationship"] == rel]
        return es

    def callers_of(self, nid):
        """Functions (or modules) that call nid."""
        out = []
        for e in self._in.get(nid, []):
            if e["relationship"] == "CALLS":
                out.append(self.by_id.get(e["source"]))
        return [n for n in out if n]

    def callees_of(self, nid):
        outs = []
        for e in self._out.get(nid, []):
            if e["relationship"] == "CALLS":
                t = self.by_id.get(e["target"])
                if t:
                    outs.append(t)
        return outs

    def imports_of(self, nid, include_external=True):
        """Import edges of a module. External targets ('import::...') are
        returned as synthetic rows when no node exists."""
        out = []
        for e in self._out.get(nid, []):
            if e["relationship"] != "IMPORTS":
                continue
            t = self.by_id.get(e["target"])
            if t:
                out.append(t)
            elif include_external and e["target"].startswith("import::"):
                out.append({"id": e["target"], "name": e["target"].split("::", 1)[1], "type": "Import",
                            "evidence": [{"type": "parser", "source": "external"}]})
        return out

    def imported_by(self, nid):
        return [self.by_id.get(e["source"]) for e in self._in.get(nid, [])
                if e["relationship"] == "IMPORTS" and self.by_id.get(e["source"])]

    def has_call_edge(self, src, tgt):
        for e in self._out.get(src, []):
            if e["target"] == tgt and e["relationship"] == "CALLS":
                return True
        return False

    # ---- transitive -------------------------------------------------------

    def deps_closure(self, start_ids, hops=5):
        """Transitive dependency closure via IMPORTS + CALLS."""
        seen = set(start_ids)
        frontier = list(start_ids)
        for _ in range(hops):
            nxt = []
            for fid in frontier:
                for e in self._out.get(fid, []):
                    if e["relationship"] in ("CALLS", "IMPORTS") and e["target"] not in seen:
                        target_id = e["target"]
                        # import targets may be external placeholders
                        if target_id.startswith("import::"):
                            continue
                        seen.add(target_id)
                        nxt.append(target_id)
            frontier = nxt
            if not frontier:
                break
        return seen - set(start_ids)

    def reverse_deps(self, start_ids, hops=5):
        """Reverse transitive closure: what depends on these nodes."""
        seen = set(start_ids)
        frontier = list(start_ids)
        for _ in range(hops):
            nxt = []
            for fid in frontier:
                for e in self._in.get(fid, []):
                    if e["relationship"] in ("CALLS", "IMPORTS"):
                        s = e["source"]
                        if s not in seen and s in self.by_id:
                            seen.add(s)
                            nxt.append(s)
            frontier = nxt
            if not frontier:
                break
        return seen - set(start_ids)

    # ---- module-level summary ---------------------------------------------

    def module_summary(self, mid):
        m = self.by_id.get(mid)
        if not m:
            return None
        children = [self.by_id.get(e["target"]) for e in self._out.get(mid, [])]
        classes = [n for n in children if n and n["type"] == "Class"]
        funcs = [n for n in children if n and n["type"] in ("Function", "Method")]
        imports = self.imports_of(mid)
        return {"module": m, "classes": classes, "functions": funcs, "imports": imports}

    def entry_points(self):
        """Public functions with no callers, excluding tests and private helpers."""
        called = set()
        for e in self.edges:
            if e["relationship"] == "CALLS":
                called.add(e["target"])
        eps = []
        for n in self.nodes:
            if n["type"] not in ("Function", "Method") or n["id"] in called:
                continue
            if n["name"].startswith("_"):
                continue
            loc = n["evidence"][0]["source"] if n.get("evidence") else ""
            if loc.startswith("tests/") or "/tests/" in loc or loc.startswith("test_"):
                continue
            if n["name"].startswith("test_"):
                continue
            eps.append(n)
        return eps