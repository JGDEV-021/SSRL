"""SSRL semantic enrichment (Phase 5) — produces HYPOTHESES over facts.

RN-4 / ADR-007 layering:
  1. structural evidence first (deterministic),
  2. naming/structure heuristics second,
  3. LLM last (never here — MVP is fully deterministic).

Everything this module creates is a HYPOTHESIS: confidence in [0,1),
explicit evidence, and never conflated with facts (FR-3).

Hypotheses produced (v1):
- DomainConcept  : modules/classes whose name signals a domain role.
- Service        : modules/classes that orchestrate (call many project funcs).
- Flow           : a chain of CALLS from an entry function (breadth-limited).
- Intent         : derived from entry-point naming + docstring signal.
"""

import os
import re
from collections import Counter

from . import model

# naming heuristics: suffix -> (kind, base_confidence, label)
SNIFF = [
    (re.compile(r"(service|services)$", re.I), "Service", 0.86, "service"),
    (re.compile(r"(repository|repositories|store|dao)$", re.I), "DomainConcept", 0.84, "repository"),
    (re.compile(r"(controller|router|endpoint)$", re.I), "DomainConcept", 0.84, "controller"),
    (re.compile(r"(manager|engine|pipeline|flow)$", re.I), "DomainConcept", 0.8, "engine"),
    (re.compile(r"(model[s]?|entity|entities|schema)$", re.I), "DomainConcept", 0.8, "model"),
    (re.compile(r"(util|utils|helpers?|common|base|core)$", re.I), "DomainConcept", 0.74, "infra"),
    (re.compile(r"(config|settings|constants)$", re.I), "DomainConcept", 0.7, "config"),
    (re.compile(r"(db|database|storage|persist)" , re.I), "DomainConcept", 0.82, "persistence"),
    (re.compile(r"(cli|cmd|main|runner|bootstrap)$", re.I), "DomainConcept", 0.8, "entrypoint"),
]

DOC_INTENTS = [
    ("validate", re.compile(r"valid|check|assert", re.I), 0.78),
    ("transform", re.compile(r"convert|transform|normalize|clean|parse", re.I), 0.76),
    ("persist", re.compile(r"save|store|write|commit|upsert|insert|update", re.I), 0.76),
    ("retrieve", re.compile(r"load|fetch|read|query|search|get|find|retrieve", re.I), 0.72),
    ("compute", re.compile(r"calcu|compute|aggregate|stat|metric|score|rank", re.I), 0.7),
]


def enrich(artifact, flow_depth=4, flow_breadth=12, verbose=False):
    """Add hypothesis nodes/edges into a copy of the artifact.

    Deterministic. Returns a new artifact dict with added nodes/edges.
    Existing facts are never modified.
    """
    import copy as _copy
    art = _copy.deepcopy(artifact)
    nodes = art["nodes"]
    edges = art["edges"]

    by_id = {n["id"]: n for n in nodes}
    # structural indices
    modules = [n for n in nodes if n["type"] == "Module"]
    functions = [n for n in nodes if n["type"] in ("Function", "Method")]
    fn_id = {n["id"]: n for n in functions}

    calls = [e for e in edges if e["relationship"] == "CALLS"]
    outgoing = {}
    for e in calls:
        if e["target"] in by_id:
            outgoing.setdefault(e["source"], []).append((e["target"], e))

    new_ids = set()
    for n in nodes:
        new_ids.add(n["id"])

    # ---- hypothesis: Service / DomainConcept labels on modules & classes ----
    counter = Counter()
    for n in modules + [n for n in nodes if n["type"] == "Class"]:
        name = n["name"]
        # use final path segment for modules (rel file or dotted mid), minus extension
        seg = os.path.basename(name).replace(".py", "").split(".")
        name_seg = seg[0].split("/")[-1] if seg else name
        for rx, kind, conf, label in SNIFF:
            if rx.search(name_seg):
                hid = model.new_id("hyp", kind.lower(), n["id"].replace("::", ":"), label)
                if hid in new_ids:
                    break
                new_ids.add(hid)
                nodes.append({
                    "id": hid, "type": kind, "name": label, "confidence": conf,
                    "evidence": [{"type": "NamingPattern", "source": name, "weight": conf}],
                    "metadata": {"target": n["id"], "hypothesis": True},
                })
                edges.append(model.make_edge(
                    n["id"], hid, "SUPPORTS_INTENT" if kind == "Service" else "RELATED_TO",
                    [{"type": "NamingPattern", "source": name, "weight": conf}],
                    {"hypothesis": True}))
                counter[label] += 1
                break

    # ---- hypothesis: Flow = CALLS chain from entry points ----
    def bfs_flow(start_id, limit_nodes, depth):
        """Return list of node ids reachable via outgoing CALLS."""
        seen = set()
        frontier = [start_id]
        for _ in range(depth):
            nxt = []
            for fid in frontier:
                for (t, _e) in outgoing.get(fid, [])[: limit_nodes]:
                    if t not in seen:
                        seen.add(t)
                        nxt.append(t)
                        if len(seen) >= limit_nodes:
                            return seen
            frontier = nxt
            if not frontier:
                break
        return seen

    entry_points = _entry_points(functions, outgoing)
    n_flows = 0
    for ep in entry_points[: 20]:  # cap for determinism of scale, not randomness
        reach = bfs_flow(ep, flow_breadth, flow_depth)
        if len(reach) < 2:
            continue
        fid = model.new_id("flow", ep.split("::", 2)[1].split("::")[0] if "::" in ep else ep, ep.split("::")[-1] if "::" in ep else ep)
        fid = f"flow::{ep}"
        if fid in new_ids:
            continue
        new_ids.add(fid)
        name = ep.split("::")[-1]
        conf = _flow_confidence(ep, reach)
        nodes.append({
            "id": fid, "type": "Flow", "name": name, "confidence": conf,
            "evidence": [{"type": "CallGraph", "source": ep, "weight": conf},
                          {"type": "CallGraph", "source": "chain", "weight": 1.0}],
            "metadata": {"entry": ep, "steps": sorted(reach), "hypothesis": True},
        })
        edges.append(model.make_edge(
            ep, fid, "PARTICIPATES_IN",
            [{"type": "CallGraph", "source": ep, "weight": conf}], {"hypothesis": True}))
        n_flows += 1

    # ---- hypothesis: Intent from entry-point/docstring naming ----
    n_intents = 0
    for n in functions:
        name = n["name"]
        doc = (n["metadata"].get("doc") or "").strip()
        haystack = f"{name} {doc}"
        best = None
        for tag, rx, conf in DOC_INTENTS:
            if rx.search(haystack):
                if best is None or conf > best[1]:
                    best = (tag, conf)
        if best:
            tag, conf = best
            iid = f"intent::{n['id']}:{tag}"
            if iid in new_ids:
                continue
            new_ids.add(iid)
            nodes.append({
                "id": iid, "type": "Intent", "name": tag, "confidence": conf,
                "evidence": [{"type": "NamingPattern", "source": name, "weight": conf}],
                "metadata": {"target": n["id"], "hypothesis": True},
            })
            edges.append(model.make_edge(
                n["id"], iid, "SUPPORTS_INTENT",
                [{"type": "NamingPattern", "source": name, "weight": conf}], {"hypothesis": True}))
            n_intents += 1

    art["stats"]["hypotheses"] = {
        "services_domain": sum(counter.values()),
        "flows": n_flows,
        "intents": n_intents,
    }
    art["stats"]["nodes"] = len(nodes)
    art["stats"]["edges"] = len(edges)
    return art


def _entry_points(functions, outgoing):
    """Public functions (no caller edges). Deterministic order (sorted)."""
    called = set()
    for outs in outgoing.values():
        for (t, _e) in outs:
            called.add(t)
    eps = [n["id"] for n in functions if n["id"] not in called and not n["name"].startswith("_")]
    return sorted(eps)


def _flow_confidence(entry, reach):
    # more steps & more structure -> slightly more confidence, capped
    base = 0.62 + min(0.15, 0.01 * len(reach))
    return round(min(base, 0.9), 3)