"""SSRL Explainable AI surface (Phase 10, ADR-009).

External coding AIs (Claude, Codex, ...) self-explain in natural language;
the layer is the notary. This module provides the two deterministic surfaces:

  1. explain_node / explain_changed  — grounded WHAT / WHY / HOW with citations
     (node mode: one artifact node; change mode: an impact bundle for a change set).
  2. verify_explanation              — the auditor: cross-checks a free-text
     narration (the coding AI's why/how) against the artifact.

Audit contract (ADR-009):
  - Quoted identifiers (`x`, "x", 'x') are explicit citations.
      resolved to an artifact identifier -> present
      matched to an external import     -> external (not invented)
      resolved to nothing               -> invented  (fabricated reference)
  - Identifier-shaped unquoted tokens that resolve add "hits"; those that do
    not resolve are reported as unresolved/ignored, never counted invented.
  - Sentences are atomic claims. A claim that cites nothing is "unsupported".
    A claim that asserts a relation (calls/imports/contains/...) is checked
    for structural consistency against the artifact.
  - Semantics are NOT judged: we verify grounding + structural consistency,
    not whether the stated reason is the right reason (ADR-009 §6).

Rules: the AI is the witness, the layer is the notary. Everything is
deterministic, stdlib-only, no model. Output dicts are JSON-safe and sorted.
"""

import re

from . import confidence as confmod
from . import impact as impactmod
from .index import Index

_PIPELINE_STAGE = {
    "parser": "build (AST extract, deterministic)",
    "NamingPattern": "enrich (naming heuristic, deterministic)",
    "CallGraph": "enrich (call-graph, deterministic)",
    "Documentation": "enrich (docstring signal, deterministic)",
    "LLMProposal": "propose (micro-LLM proponent, ADR-008; capped 0.5)",
}

_RELATIONSTEPS = {"CALLS", "IMPORTS", "CONTAINS", "RELATED_TO",
                  "SUPPORTS_INTENT", "PARTICIPATES_IN"}

QUOTE_RE = re.compile(r"`([^`]+)`|\"([^\"]+)\"|'([^']+)'")
_IDENT_RE = re.compile(
    r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+|[a-z][a-z0-9_]*_[a-z0-9_]+|[A-Z][A-Za-z0-9]{2,}")

# relation assertion patterns, most specific first
_REL_PATTERNS = [
    ("called_by", re.compile(r"called by|invoked by|called from|referenced by", re.I)),
    ("imported_by", re.compile(r"imported by", re.I)),
    ("used_by", re.compile(r"used by|relied on by|consumed by", re.I)),
    ("depends_on", re.compile(r"depends? on|dependent on", re.I)),
    ("calls_out", re.compile(r"\binvokes?\b|\bcalls?\b|\bcall to\b", re.I)),
    ("imports_out", re.compile(r"\bimport\w*", re.I)),
    ("uses_out", re.compile(r"\buses?\b", re.I)),
    ("contains", re.compile(r"contain(s|ed|ing)?\b|owns?\b", re.I)),
    ("depends", re.compile(r"\bdepend\w*", re.I)),
]

CLAIM_VERBS = re.compile(
    r"\b(added|changed|removed|deleted|rewrote|rewritten|refactored|renamed|fixed|updated|"
    r"moved|extracted|implemented|wrapped|introduced|replaced|hooked|wired|migrated|"
    r"simplified|inlined|split)\b", re.I)


def _ids(nodes):
    return sorted({n["id"] for n in nodes if n})


def _loc(node, fallback=""):
    for ev in node.get("evidence", []):
        src = ev.get("source")
        if src:
            return src
    return fallback


def _resolve(idx, cand):
    """Resolve a cited candidate to an artifact node, external target, or None."""
    c = cand.strip()
    if not c:
        return None
    if "::" in c:
        n = idx.node(c)
        if n:
            return n
    # external import targets look like  import::kind:name
    for e in idx.edges:
        t = e.get("target", "")
        if t.startswith("import::") and (c in t or c == t.rsplit(":", 1)[-1]):
            return {"external": True, "name": c, "target": t}
    # dotted func/class path (db.save -> func::db::save; models.validate -> func::models::validate)
    for pref in ("func", "class"):
        n = idx.node(f"{pref}::{c}")
        if n:
            return n
        n = idx.node(f"{pref}::{c.replace('.', '::')}")
        if n:
            return n
    # module forms (dotted mid or slashed path, with/without .py)
    raw = c.replace(".py", "")
    dotted = raw.replace("/", ".")
    slashed = raw.replace(".", "/")
    for form in sorted({c, c.replace(".py", ""), dotted, slashed,
                        f"module::{dotted}"}):
        n = idx.node(form if form.startswith("module::") else f"module::{form}")
        if n:
            return n
    # bare exact name
    for n in idx.nodes:
        if n.get("name") == c:
            return n
    return None


def node_what(idx, node):
    """Structural description of a node (the WHAT)."""
    rels = {}
    if node["type"] in ("Function", "Method"):
        rels["callers"] = _ids(idx.callers_of(node["id"]))
        rels["callees"] = _ids(idx.callees_of(node["id"]))
    elif node["type"] == "Module":
        rels["children"] = len(idx.children(node["id"], "CONTAINS"))
        rels["imports"] = _ids(idx.imports_of(node["id"]))
        rels["imported_by"] = _ids(idx.imported_by(node["id"]))
    elif node["type"] == "Class":
        rels["members"] = _ids([e["target"] for e in idx.children(node["id"], "CONTAINS")])
    elif node["type"] in ("Flow", "Intent", "Service", "DomainConcept"):
        rels["target"] = (node.get("metadata") or {}).get("target")
        if node["type"] == "Flow":
            meta = node.get("metadata") or {}
            rels["steps"] = sorted(meta.get("steps", []))
    return {
        "type": node["type"], "name": node["name"], "id": node["id"],
        "loc": _loc(node), "confidence": node.get("confidence"),
        "relations": {k: v for k, v in rels.items() if v or k in ("children",)},
    }


def node_how(node):
    """Derivation trail (the HOW): pipeline stages + evidence + edges."""
    evidence = sorted(node.get("evidence", []),
                      key=lambda e: (e.get("type", ""), e.get("source", ""),
                                     str(e.get("weight", ""))))
    stages = sorted({_PIPELINE_STAGE.get(e.get("type", ""), f"unknown ({e.get('type', '')})")
                     for e in evidence}) or ["unknown"]
    return {"stages": stages, "evidence": evidence}


def explain_node(idx, node):
    """Grounded WHAT/WHY/HOW for one artifact node (deterministic dict)."""
    return {
        "what": node_what(idx, node),
        "why": confmod.why(node),
        "how": node_how(node),
    }


def explain_changed(artifact, changed_files, index=None):
    """Grounded WHAT/WHY/HOW for a change set (the impact bundle)."""
    idx = index or Index(artifact)
    rep = impactmod.impact_changed(artifact, changed_files, index=idx)
    c = rep["counts"]
    what = {
        "changed_files": rep["changed_files"],
        "ignored": rep["ignored"],
        "missing_modules": rep["missing_modules"],
        "affected_modules": rep["affected_modules"],
        "entry_points_touched": rep["entry_points_touched"],
        "flows_affected": rep["flows_affected"],
    }
    why = {
        "counts": c,
        "importers": rep["importers"],
        "callers_of_changed": rep["callers_of_changed"],
        "reverse_dependent_modules": rep["reverse_dependent_modules"],
    }
    steps = [f"{c['files']} changed file(s) -> {c['modules']} module(s) affected"]
    if c["importers"]:
        steps.append(f"{c['importers']} direct importer(s) -> may break")
    if c["callers"]:
        steps.append(f"{c['callers']} caller(s) of changed symbols -> may break")
    if c["entries"]:
        steps.append(f"{c['entries']} entry point(s) touched -> public API surface")
    if c["flows"]:
        steps.append(f"{c['flows']} flow(s) affected -> behavior hypotheses crossing the change")
    if c["missing"]:
        steps.append(f"{c['missing']} changed file(s) without a module node -> new/deleted code")
    how = {
        "pipeline": ["changed files -> module nodes (impact)",
                     "direct importers -> callers -> entry points -> flows -> reverse closure"],
        "steps": steps,
    }
    return {"what": what, "why": why, "how": how}


def _relation_keyword(sentence):
    """Return the relation asserted by a sentence, or None."""
    for name, rx in _REL_PATTERNS:
        if rx.search(sentence):
            return name
    return None


def _surface(idx, nid, direction, kinds):
    for e in idx._out.get(nid, []) if direction == "out" else idx._in.get(nid, []):
        if e["relationship"] in kinds:
            return True
    return False


def _single_consistent(idx, nid, kw):
    if kw == "called_by":
        return _surface(idx, nid, "in", {"CALLS"})
    if kw == "imported_by":
        return _surface(idx, nid, "in", {"IMPORTS"})
    if kw == "used_by":
        return _surface(idx, nid, "in", {"CALLS", "IMPORTS"})
    if kw == "depends_on" or kw == "depends":
        return (_surface(idx, nid, "out", {"CALLS", "IMPORTS"})
                or _surface(idx, nid, "in", {"CALLS", "IMPORTS"}))
    if kw == "calls_out":
        return _surface(idx, nid, "out", {"CALLS"})
    if kw == "imports_out":
        return _surface(idx, nid, "out", {"IMPORTS"})
    if kw == "uses_out":
        return _surface(idx, nid, "out", {"CALLS", "IMPORTS"})
    if kw == "contains":
        return (_surface(idx, nid, "out", {"CONTAINS"})
                or _surface(idx, nid, "in", {"CONTAINS"}))
    return None


_KW_KINDS = {
    "called_by": {"CALLS"},
    "imported_by": {"IMPORTS"},
    "used_by": {"CALLS", "IMPORTS"},
    "depends_on": {"CALLS", "IMPORTS"},
    "depends": {"CALLS", "IMPORTS"},
    "calls_out": {"CALLS"},
    "imports_out": {"IMPORTS"},
    "uses_out": {"CALLS", "IMPORTS"},
    "contains": {"CONTAINS"},
}


def _edges_between(idx, a, b):
    rels = set()
    for e in idx._out.get(a, []):
        if e["target"] == b:
            rels.add(e["relationship"])
    for e in idx._out.get(b, []):
        if e["target"] == a:
            rels.add(e["relationship"])
    return rels


def _pair_consistent(idx, ids, kw):
    kinds = _KW_KINDS.get(kw)
    if not kinds:
        return None
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if _edges_between(idx, ids[i], ids[j]) & kinds:
                return True
    return False


def verify_explanation(artifact, changed_files, narration, index=None):
    """Audit a coding AI's self-explanation against the artifact.

    Deterministic. Grounding + structural consistency only (ADR-009).
    """
    idx = index or Index(artifact)
    rep = impactmod.impact_changed(artifact, changed_files, index=idx)
    scope = set(rep["entry_points_touched"])
    scope.update(rep["flows_affected"])
    scope.update(rep["reverse_dependent_modules"])
    for mid, info in rep["affected_modules"].items():
        scope.add(f"module::{mid}")
        scope.update(info["symbols"])

    text = (narration or "").replace("``", "`")  # tolerate pasted markdown double-backticks
    citations = []
    for raw in (g for m in QUOTE_RE.finditer(text) for g in m.groups() if g is not None):
        r = _resolve(idx, raw)
        if r is None:
            citations.append({"raw": raw, "kind": "invented", "id": None, "in_scope": False})
        elif r.get("external"):
            citations.append({"raw": raw, "kind": "external", "id": r["target"], "in_scope": False})
        else:
            cid = r["id"]
            citations.append({"raw": raw, "kind": "present", "id": cid,
                              "in_scope": cid in scope})

    body = QUOTE_RE.sub(" ", text)
    unquoted_hits = {}
    for tok in sorted(set(_IDENT_RE.findall(body))):
        if any(tok == c["raw"] for c in citations if c["kind"] == "present"):
            continue
        n = _resolve(idx, tok)
        if n and not n.get("external"):
            unquoted_hits[tok] = n["id"]

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9`\"'])|\n+", text)
                 if s.strip()]
    unsupported, consistency_failures, claims_checked = [], [], 0
    cited = {c["raw"].lower(): c["id"] for c in citations if c["kind"] == "present"}
    unq_lookup = {}
    for tok, uid in unquoted_hits.items():
        word = tok.rsplit(".", 1)[-1].lower()
        if word and len(word) >= 3:
            unq_lookup.setdefault(word, uid)

    for sent in sentences:
        sl = sent.lower()
        syms = [cid for raw, cid in cited.items() if raw and raw in sl]
        for word, uid in unq_lookup.items():
            if word and word in sl and uid not in syms:
                syms.append(uid)
        syms = sorted(set(syms))
        if not syms:
            if len(sent) >= 20 and (CLAIM_VERBS.search(sent) or sent.endswith(".")):
                unsupported.append(sent)
            continue
        kw = _relation_keyword(sent)
        if kw is None:
            continue
        claims_checked += 1
        ok = _pair_consistent(idx, syms, kw) if len(syms) >= 2 \
            else _single_consistent(idx, syms[0], kw)
        if ok is False:
            consistency_failures.append({
                "claim": sent,
                "reason": f"asserts '{kw}' but no {kw} relation found for "
                          f"{' / '.join(syms)} in the artifact",
            })

    present = [c for c in citations if c["kind"] == "present"]
    invented = [c for c in citations if c["kind"] == "invented"]
    external = [c for c in citations if c["kind"] == "external"]
    denom = len(present) + len(invented)
    groundedness = round(len(present) / denom, 3) if denom else 1.0
    if denom and groundedness >= 0.8 and not invented:
        verdict = "PASS"
    else:
        verdict = "REVIEW"

    return {
        "groundedness": groundedness,
        "verdict": verdict,
        "citations": {
            "count": len(citations), "present": len(present), "invented": len(invented),
            "external": len(external), "in_scope": sum(1 for c in present if c["in_scope"]),
            "unquoted_hits": len(unquoted_hits),
            "unresolved_tokens": max(0, len(set(_IDENT_RE.findall(body))) - len(unquoted_hits)),
            "invented_details": [c["raw"] for c in invented],
        },
        "claims": {
            "checked": claims_checked,
            "unsupported": unsupported,
            "consistency_failures": consistency_failures,
        },
        "change_scope": rep["counts"],
        "narration": text,
    }


def render_explain_node(d):
    w, h = d["what"], d["how"]
    L = ["WHAT"]
    L.append(f"  {w['type']} '{w['name']}' (id {w['id']})"
             + (f" at {w['loc']}" if w["loc"] else "")
             + (f" conf={w['confidence']}" if w.get("confidence") is not None else ""))
    for k, v in sorted((w.get("relations") or {}).items()):
        L.append(f"  relations[{k}]: {', '.join(v) if isinstance(v, list) else v}")
    L.append("WHY")
    L.append("  " + d["why"].replace("\n", "\n  "))
    L.append("HOW")
    for s in h["stages"]:
        L.append(f"  stage: {s}")
    for e in h["evidence"]:
        L.append(f"  evidence[{e.get('type')}] weight={e.get('weight')} source={e.get('source')}")
    return "\n".join(L)


def render_explain_changed(d):
    w, h = d["what"], d["how"]
    L = ["WHAT"]
    L.append("  " + ", ".join(sorted(w["changed_files"])))
    for mid in sorted(w["affected_modules"]):
        info = w["affected_modules"][mid]
        L.append(f"  module {mid} ({info['path']}): {len(info['symbols'])} symbol(s)")
    if w["entry_points_touched"]:
        L.append("  entry points touched: " + ", ".join(sorted(w["entry_points_touched"])))
    if w["flows_affected"]:
        L.append("  flows affected: " + ", ".join(sorted(w["flows_affected"])))
    if w["missing_modules"]:
        L.append("  missing module nodes: " + ", ".join(sorted(w["missing_modules"])))
    if w["ignored"]:
        L.append("  ignored (non-python): " + ", ".join(sorted(w["ignored"])))
    L.append("WHY")
    c = d["why"]["counts"]
    L.append(f"  {c['files']} file(s), {c['modules']} module(s) affected, "
             f"{c['importers']} importer(s), {c['callers']} caller(s) may break, "
             f"{c['entries']} entry point(s), {c['flows']} flow(s), {c['missing']} missing")
    if d["why"]["reverse_dependent_modules"]:
        L.append("  reverse dependencies: " + ", ".join(d["why"]["reverse_dependent_modules"]))
    L.append("HOW")
    for s in h["steps"]:
        L.append(f"  step: {s}")
    return "\n".join(L)


def render_verify(d):
    cit = d["citations"]
    L = [f"VERDICT: {d['verdict']}  groundedness={d['groundedness']}",
         f"citations: count={cit['count']} present={cit['present']} "
         f"invented={cit['invented']} external={cit['external']} in_scope={cit['in_scope']} "
         f"unquoted_hits={cit['unquoted_hits']} unresolved_tokens={cit['unresolved_tokens']}"]
    c = d["change_scope"]
    L.append(f"change scope: {c['files']} file(s), {c['modules']} module(s), "
             f"{c['importers']} importer(s), {c['callers']} caller(s), "
             f"{c['entries']} entry point(s), {c['flows']} flow(s)")
    if cit["invented_details"]:
        L.append("invented citations (fabricated references): "
                 + ", ".join(sorted(set(cit["invented_details"]))))
    elif cit["invented"] == 0:
        L.append("invented citations: none")
    cl = d["claims"]
    if cl["unsupported"]:
        L.append(f"unsupported claims (sentences citing nothing, {len(cl['unsupported'])}): "
                 + " | ".join(cl["unsupported"][:3])
                 + (f" (+{len(cl['unsupported']) - 3} more)" if len(cl["unsupported"]) > 3 else ""))
    if cl["consistency_failures"]:
        for f in cl["consistency_failures"]:
            L.append(f"consistency failure: {f['claim']}  ({f['reason']})")
    else:
        L.append("consistency failures: none")
    return "\n".join(L)