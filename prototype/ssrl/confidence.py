"""SSRL confidence & evidence engine (Phase 6).

RQ-3 / FR-4: hypotheses carry calibrated confidence; facts are 1.0.
Three components (deterministic, zero deps):

  1. calibrate(kind, conf, evidence)  — clamp/adjust for hypothesis kind.
  2. why(node_id)                     — human-readable evidence explanation.
  3. aggregate(evidence)              — weighted agreement across sources.

Calibration policy (v1, conservative):
  - facts:        1.0 always.
  - hypotheses:   conf is clamped to [0.55, 0.95]; if the hypothesis has no
                  evidence, it is demoted to 0.5 (indicates "guess").
  - naming-only hypotheses cannot reach above their source weight.
"""

# maximum confidence achievable by evidence source type
SOURCE_CEILING = {
    "NamingPattern": 0.9,
    "CallGraph": 0.88,
    "Documentation": 0.92,
    "parser": 1.0,
    "call-graph": 1.0,
    "Structure": 0.9,
    "LLMProposal": 0.5,
}

# hypothesis kinds allowed to become facts? none (FR-3).
HYPOTHESIS_KINDS = {"DomainConcept", "Flow", "Intent", "Service"}


def aggregate(evidence):
    """Weighted agreement across evidence sources (RN-3 baseline).

    Simple scheme: combine by noisy-OR of source weights, capped by the
    strongest single source's ceiling. Deterministic regardless of order.
    """
    if not evidence:
        return 0.5
    weights = []
    for ev in evidence:
        w = ev.get("weight", 0.0)
        if w <= 0:
            continue
        # respect per-source ceiling
        cap = SOURCE_CEILING.get(ev.get("type", ""), 0.95)
        weights.append(min(w, cap))
    if not weights:
        return 0.5
    noisy_or = 1.0
    for w in sorted(weights, reverse=True):
        noisy_or *= (1.0 - w)
    comb = 1.0 - noisy_or
    top = max(weights)
    # combined never exceeds the strongest single source
    return round(min(comb, top), 3)


def calibrate(node, artifact_nodes=None):
    """Return (confidence, note) for a node given its type and evidence."""
    ntype = node.get("type")
    conf = float(node.get("confidence", 0.5))
    evidence = node.get("evidence", [])

    if ntype not in HYPOTHESIS_KINDS:
        # facts
        return 1.0, "fact"

    if not evidence:
        return 0.5, "no-evidence (demoted)"

    top = max((e.get("weight", 0.0) for e in evidence if e.get("weight")), default=0.0)
    if top <= 0:
        return 0.5, "unweighted evidence (demoted)"

    combined = aggregate(evidence)
    if ntype == "Flow":
        combined = min(combined, 0.9)
    combined = min(combined, top)

    if combined < 0.55:
        note = "weak hypothesis — treat as suggestive"
    elif combined < 0.75:
        note = "moderate hypothesis"
    elif combined < 0.95:
        note = "strong hypothesis"
    else:
        note = "very strong hypothesis"
    return round(combined, 3), note


def why(node, artifact_nodes=None):
    """Human-readable explanation of a node's confidence."""
    ntype = node.get("type")
    conf, note = calibrate(node)
    if ntype not in HYPOTHESIS_KINDS:
        return (f"[FACT] {node.get('id')}: deterministic, confidence 1.0, "
                f"evidence {node.get('evidence', [])}")
    lines = [f"[HYPOTHESIS] {node.get('id')} type={ntype} confidence={conf} ({note})"]
    for ev in node.get("evidence", []):
        src = ev.get("source", "?")
        w = ev.get("weight", "?")
        lines.append(f"  - evidence[{ev.get('type')}] weight={w} source={src}")
    return "\n".join(lines)


def audit(hypothesis_nodes):
    """Calibration audit table (RQ-3). Deterministic. Returns list of dicts."""
    rows = []
    for n in sorted(hypothesis_nodes, key=lambda x: x["id"]):
        conf, note = calibrate(n)
        rows.append({
            "id": n["id"],
            "type": n["type"],
            "confidence": conf,
            "note": note,
            "evidence_sources": [e.get("type") for e in n.get("evidence", [])],
            "is_hypothesis": n["type"] in HYPOTHESIS_KINDS,
        })
    return rows