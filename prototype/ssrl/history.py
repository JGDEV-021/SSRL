"""SSRL history — the deleted-symbols view (auditable removals, Phase 10).

ADR-003 keeps node ids stable across commits, so a snapshot of the previous
artifact's structural manifest can be diffed against the current one to answer
"what was deleted or replaced since the last build?". This is the view that
makes narrations about removals (*"I deleted `X`"*) audit-able against the
layer instead of REVIEW noise from invented citations (REPORT-P10 open item,
now shipped).

For every `extract.build(root, cache_dir=...)` the layer stores a snapshot next
to the D-8 cache (`<cache_dir>/snapshot.json`) and attaches a `deleted` report
to the returned artifact. Watch regeneration rolls the snapshot forward for
free, so "deleted since last build" tracks the same no-manual-sync baseline as
the incremental cache.

Deterministic, stdlib-only. Only structural facts are kept in the manifest
(hypotheses are excluded so enrich/no-enrich runs stay comparable).
"""

import json
import os

from . import model

SNAPSHOT_VERSION = 1
SNAPSHOT_FILENAME = "snapshot.json"

_STRUCTURAL = model.STRUCTURAL_NODES - {"Repository"}
_REL_STRUCTURAL = model.STRUCTURAL_EDGES


def _node_ref(n):
    return {"id": n["id"], "type": n["type"], "name": n["name"]}


def _module_of(nid):
    """Parent module id (mid) of a node id, e.g. func::db::save -> db."""
    parts = nid.split("::")
    return parts[1] if len(parts) >= 2 else None


def snapshot(artifact):
    """Minimal structural manifest of an artifact (ids only, versioned)."""
    modules = []
    nodes = []
    for n in artifact["nodes"]:
        if n["type"] not in _STRUCTURAL:
            continue
        if n["type"] == "Module":
            modules.append({"id": n["id"], "path": n["name"]})
        nodes.append(_node_ref(n))
    edges = sorted(
        [e["source"], e["target"], e["relationship"]]
        for e in artifact["edges"] if e["relationship"] in _REL_STRUCTURAL)
    return {
        "version": SNAPSHOT_VERSION,
        "modules": sorted(modules, key=lambda m: m["id"]),
        "nodes": sorted(nodes, key=lambda r: r["id"]),
        "edges": edges,
    }


def save_snapshot(cache_dir, artifact):
    """Persist the manifest so the NEXT build can diff against it."""
    with open(os.path.join(cache_dir, SNAPSHOT_FILENAME), "w", encoding="utf-8") as f:
        json.dump(snapshot(artifact), f, ensure_ascii=False)


def load_snapshot(cache_dir):
    try:
        with open(os.path.join(cache_dir, SNAPSHOT_FILENAME), encoding="utf-8") as f:
            s = json.load(f)
        if s.get("version") == SNAPSHOT_VERSION:
            return s
    except (OSError, ValueError):
        pass
    return None


def _empty_report():
    return {
        "has_history": False,
        "modules_removed": [],
        "symbols_removed": [],
        "relations_removed": [],
        "counts": {"modules": 0, "symbols": 0, "relations": 0},
    }


def deleted_symbols(prev, artifact):
    """Diff a previous snapshot against the current artifact.

    Returns the deleted-symbols view: modules/symbols/relations present in the
    previous build but absent now. Empty (has_history False) when there is no
    previous snapshot. Deterministic ordering throughout.
    """
    if not prev or not prev.get("nodes"):
        return _empty_report()
    if prev.get("version") != SNAPSHOT_VERSION:
        return _empty_report()

    cur_node_ids = {n["id"] for n in artifact["nodes"]}
    cur_module_ids = {n["id"] for n in artifact["nodes"] if n["type"] == "Module"}

    modules_removed = [
        {"id": m["id"], "path": m["path"]}
        for m in prev["modules"] if m["id"] not in cur_module_ids]
    symbols_removed = [
        {**r, "module": _module_of(r["id"])}
        for r in prev["nodes"]
        if r["type"] in ("Function", "Method", "Class") and r["id"] not in cur_node_ids]

    cur_edges = {(e["source"], e["target"], e["relationship"]) for e in artifact["edges"]}
    prev_edges = {tuple(e) for e in prev["edges"]}
    relations_removed = [
        {"source": s, "target": t, "relationship": r}
        for (s, t, r) in sorted(prev_edges - cur_edges)]

    modules_removed.sort(key=lambda m: m["id"])
    symbols_removed.sort(key=lambda s: s["id"])
    return {
        "has_history": True,
        "modules_removed": modules_removed,
        "symbols_removed": symbols_removed,
        "relations_removed": relations_removed,
        "counts": {
            "modules": len(modules_removed),
            "symbols": len(symbols_removed),
            "relations": len(relations_removed),
        },
    }


def render_deleted(report):
    """Human-readable text for the CLI and the MCP `deleted` tool."""
    if not report.get("has_history"):
        return ("no history snapshot — the deleted-symbols view needs a previous "
                "build with the D-8 cache (`--cache` or `mcp --repo`)")
    c = report["counts"]
    if not any(c.values()):
        return "no deleted symbols (structure unchanged since previous build)"
    L = [f"deleted since previous build: {c['modules']} module(s), "
         f"{c['symbols']} symbol(s), {c['relations']} relation(s)"]
    for m in report["modules_removed"]:
        L.append(f"  module removed: {m['id']} ({m['path']})")
    by_mod = {}
    for s in report["symbols_removed"]:
        by_mod.setdefault(s["module"] or "-", []).append(s)
    for mod in sorted(by_mod):
        names = ", ".join(f"{s['type']} {s['id']}" for s in by_mod[mod])
        L.append(f"  symbol(s) removed from {mod}: {names}")
    if c["relations"]:
        L.append(f"  relation(s) removed: {c['relations']} "
                 "(see --json for the full list)")
    return "\n".join(L)