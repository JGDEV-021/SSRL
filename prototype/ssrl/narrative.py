"""SSRL living narrative (Phase 4 co-surface H3, ADR-005).

A deterministic, structure-derived report explaining how the repository
works. Rebuilt from the fact layer on demand — never a stale artifact.

Sections:
  1. Overview (repo, size, parse health)
  2. Entry points (no-caller public functions)
  3. Module map (each module: purpose from docstring, classes/functions,
     imports) — with evidence
  4. Key flows (Flow hypotheses, calibrated)
  5. Hypothesis caveat (confidence reminder, FR-3)
"""

from . import confidence as confmod


def narrative(index, max_modules=100):
    art = index.artifact
    stats = art["stats"]
    repo = next(n for n in index.nodes if n["type"] == "Repository")
    modules = [n for n in index.nodes if n["type"] == "Module"]
    classes = [n for n in index.nodes if n["type"] == "Class"]
    funcs = [n for n in index.nodes if n["type"] in ("Function", "Method")]
    flows = sorted((n for n in index.nodes if n["type"] == "Flow"),
                   key=lambda n: -n.get("confidence", 0))
    intents = [n for n in index.nodes if n["type"] == "Intent"]
    services = [n for n in index.nodes if n["type"] == "Service"]

    L = []
    L.append(f"# Living Narrative — {repo['name']}")
    L.append("")
    L.append(f"*Generated at {art.get('generated_at', 'build-time')} from the fact layer "
             f"(graph v{art['graph_version']}). All structural claims are facts (confidence 1.0); "
             f"semantic claims are labeled hypotheses.*")
    L.append("")

    # 1. Overview
    L.append("## 1. Overview")
    L.append("")
    L.append(f"- **Scale:** {stats.get('files', 0)} Python files, {len(modules)} modules, "
             f"{len(classes)} classes, {len(funcs)} functions/methods, "
             f"{stats.get('imports', 0)} imports, {stats.get('calls', 0)} call edges.")
    L.append(f"- **Parse health:** {stats.get('parse_ok', 0)} parsed cleanly, "
             f"{stats.get('parse_errors', 0)} syntax errors.")
    L.append("")

    # 2. Entry points
    L.append("## 2. Entry points")
    L.append("")
    eps = index.entry_points()
    if eps:
        L.append("Public functions with no in-repo callers — likely where execution starts:")
        for n in eps[:20]:
            loc = n["evidence"][0]["source"] if n.get("evidence") else "?"
            L.append(f"- `{n['name']}` (`{n['id']}`) — {loc}")
    else:
        L.append("No entry points identified (functionality is called internally).")
    L.append("")

    # 3. Module map
    L.append("## 3. Module map")
    L.append("")
    for m in modules[:max_modules]:
        rel = m["name"]
        doc = m.get("metadata", {}).get("docstring")
        kids = index.children(m["id"])
        child_ids = [e["target"] for e in kids if e["relationship"] == "CONTAINS" and e["target"] in index.by_id]
        import_edges = [e for e in kids if e["relationship"] == "IMPORTS"]
        if doc:
            L.append(f"### `{rel}` — *{doc[:300]}*")
            L.append(f"- {len(child_ids)} contained symbol(s); {len(import_edges)} import(s).")
        else:
            L.append(f"### `{rel}`")
            L.append(f"- {len(child_ids)} contained symbol(s); {len(import_edges)} import(s).")
        L.append("")
    L.append("")

    # 4. Flows
    L.append("## 4. Key flows (hypotheses)")
    L.append("")
    if flows:
        for f in flows[:15]:
            conf, note = confmod.calibrate(f)
            entry = f.get("metadata", {}).get("entry", "?")
            steps = f.get("metadata", {}).get("steps", [])
            L.append(f"- **`{f['name']}`** conf **{conf}** ({note}) — entry `{entry}`, "
                     f"{len(steps)} steps. Evidence: {[e['source'] for e in f.get('evidence', [])]}.")
    else:
        L.append("No flows inferred (set `enrich()` before generating narrative, or the repo is small).")
    L.append("")

    # 5. Hypothesis caveat
    L.append("## 5. Confidence & evidence (RQ-3)")
    L.append("")
    L.append(f"- {len(flows)} Flow, {len(intents)} Intent, {len(services)} Service/DomainConcept hypotheses "
             f"were produced by naming/structure heuristics (RN-4).")
    L.append("- Facts (structural claims) are confidence 1.0. Hypotheses carry calibrated confidence "
             f"between 0.55 and 0.95; inspect `ssrl ask --why` for per-item evidence.")
    L.append("")
    L.append("---")
    L.append("*Narrative is a projection of the fact layer, not new knowledge. "
             "Regenerate after each commit.*")
    return "\n".join(L)