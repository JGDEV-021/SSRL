"""SSRL impact report (Phase 8) — "what does this PR affect?".

Supporting surface deferred from ADR-006.3: given a set of changed files (e.g.
from `git diff --name-only`), compute the blast radius over the artifact:

  - affected modules (the changed file(s), mapped back to their module nodes)
  - importers (who imports a changed module — direct)
  - callers of changed functions/methods (who may break)
  - entry points touched (public API surface of the PR)
  - flows affected (Flow hypotheses whose entry/steps pass through changed code)
  - reverse dependency closure (transitive, IMPORTS + CALLS)

Fully deterministic: every list is sorted; node ids are stable (ADR-003).
Consumed by the MCP `impact` tool and the CLI `impact` command.
"""

from .extract import module_id
from .index import Index


def _node_ids(nodes):
    return sorted({n["id"] for n in nodes})


def impact_changed(artifact, changed_files, index=None):
    """Compute the impact report for `changed_files` (repo-relative paths).

    Returns a JSON-safe dict (deterministic ordering everywhere).
    """
    index = index or Index(artifact)
    changed = sorted(set(changed_files or []))
    ignored = [f for f in changed if not f.endswith(".py")]
    py_files = [f for f in changed if f.endswith(".py")]

    entry_ids = {n["id"] for n in index.entry_points()}
    flow_nodes = [n for n in index.nodes if n["type"] == "Flow"]

    affected = {}          # mid -> {"path": rel, "symbols": [...]}
    importers = {}         # mid -> [importer ids]
    callers = {}           # fid -> [caller ids]
    entries_touched = set()
    flows_touched = set()
    missing = []

    changed_mids = []
    for rel in py_files:
        mid = module_id(rel)
        nid = f"module::{mid}"
        node = index.node(nid)
        if node is None:
            missing.append(rel)
            continue
        changed_mids.append(mid)
        symbols = _node_ids([n for e in index.children(nid, "CONTAINS")
                             for n in [index.by_id.get(e["target"])] if n])
        affected[mid] = {"path": rel, "symbols": symbols}
        imp = _node_ids(index.imported_by(nid))
        if imp:
            importers[mid] = imp
        for fid in symbols:
            if index.node(fid):
                c = _node_ids(index.callers_of(fid))
                if c:
                    callers[fid] = c
                if fid in entry_ids:
                    entries_touched.add(fid)
        for fn in flow_nodes:
            steps = fn.get("metadata", {}).get("steps") or []
            ep = fn.get("metadata", {}).get("entry")
            if (ep in symbols) or any(s in symbols for s in steps):
                flows_touched.add(fn["id"])

    reverse_mods = []
    rev = index.reverse_deps([f"module::{m}" for m in changed_mids])
    reverse_mods = sorted(m for m in rev
                          if m.startswith("module::")
                          and m not in {f"module::{m}" for m in changed_mids})

    counts = {
        "files": len(changed),
        "modules": len(affected),
        "importers": sum(len(v) for v in importers.values()),
        "callers": sum(len(v) for v in callers.values()),
        "entries": len(entries_touched),
        "flows": len(flows_touched),
        "missing": len(missing),
    }
    pieces = [f"{counts['files']} changed file(s)"]
    if counts["modules"]:
        pieces.append(f"{counts['modules']} module(s) affected")
    if counts["importers"]:
        pieces.append(f"{counts['importers']} direct importer(s)")
    if counts["callers"]:
        pieces.append(f"{counts['callers']} caller(s) may break")
    if counts["entries"]:
        pieces.append(f"{counts['entries']} entry point(s) touched")
    if counts["flows"]:
        pieces.append(f"{counts['flows']} flow(s) affected")
    if counts["missing"]:
        pieces.append(f"{counts['missing']} changed file(s) without a module node "
                      f"(new/deleted: {', '.join(missing)})")
    summary = "; ".join(pieces) + "."

    return {
        "changed_files": changed,
        "ignored": sorted(ignored),
        "missing_modules": sorted(missing),
        "affected_modules": {k: affected[k] for k in sorted(affected)},
        "importers": {k: importers[k] for k in sorted(importers)},
        "callers_of_changed": {k: callers[k] for k in sorted(callers)},
        "entry_points_touched": sorted(entries_touched),
        "flows_affected": sorted(flows_touched),
        "reverse_dependent_modules": reverse_mods,
        "counts": counts,
        "summary": summary,
    }


def render_impact(report):
    """Human-readable text for the CLI (also used by the MCP impact tool)."""
    L = [report["summary"]]
    if report["ignored"]:
        L.append("  ignored (non-python): " + ", ".join(report["ignored"]))
    for mid in sorted(report["affected_modules"]):
        info = report["affected_modules"][mid]
        L.append(f"  module {mid} ({info['path']}): id module::{mid} "
                 f"({len(info['symbols'])} symbol(s))")
    for mid in sorted(report["importers"]):
        L.append(f"  imports {mid}: " + ", ".join(report["importers"][mid]))
    for fid in sorted(report["callers_of_changed"]):
        L.append(f"  callers of {fid}: " + ", ".join(report["callers_of_changed"][fid]))
    for fid in report["entry_points_touched"]:
        L.append(f"  entry point touched: {fid}")
    for fid in report["flows_affected"]:
        L.append(f"  flow affected: {fid}")
    for mid in report["reverse_dependent_modules"]:
        L.append(f"  reverse dependency: {mid}")
    if report["missing_modules"]:
        L.append("  missing module nodes: " + ", ".join(report["missing_modules"]))
    return "\n".join(L)