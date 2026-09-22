"""SSRL grounded Q&A engine (Phase 4 primary projection, H1).

Deterministic, instruction-free routing: a small intent parser maps
natural-language-ish questions to fact queries. No LLM. Every answer
reports FACTS vs HYPOTHESES with evidence (FR-6a).

Intent inventory (v1):
  - "what calls X" / "callers of X"          -> callers
  - "what does X call" / "callees"           -> callees
  - "where is X" / "defined"?                 -> definition + evidence
  - "what does module X do" / "summary"       -> module summary
  - "imports of X" / "what imports X"         -> imports / importers
  - "dependencies of X"                       -> transitive closure
  - "what depends on X" / "reverse deps"       -> reverse closure
  - "entry points" / "where do I start"       -> entry points
  - "functions in X" / "classes in X"         -> containment listing
  - "flows" / "intents" / "services"          -> hypotheses browse (calibrated)
"""

import re

from . import confidence as confmod


def _extract_target(q):
    """Best-effort: pull the entity name out of the question."""
    q = q.strip()
    stop = ["what", "does", "do", "the", "define", "defined", "call", "calls",
            "called", "in", "of", "to", "and", "where", "is", "are", "this",
            "that", "which", "who", "module", "function", "class", "method",
            "import", "imports", "dependency", "dependencies", "depend",
            "depends", "on", "entry", "point", "points", "start", "all",
            "list", "show", "me", "give", "its", "it", "? ", "give me", "tell",
            "o", "a", "e", "que", "quem", "como", "onde", "qual", "quais",
            "para", "por", "de", "da", "do", "das", "dos", "em", "com",
            "chama", "chamam", "chamar", "chamado", "chamada", "chamados",
            "chamadas", "importa", "importam", "importar", "importado",
            "importada", "usa", "usam", "usar", "usado", "usada",
            "depende", "dependem", "depender", "faz", "fazem", "fazer",
            "esta", "est\u00e1", "fica", "ficam", "serve"]
    # remove trailing '?' and contractions
    q = q.replace("?", " ").replace("'", " ")
    # target is last meaningful token(s) — try longest suffix match first in Index.
    tokens = [t for t in re.split(r"[^A-Za-z0-9_.:/]+", q) if t and t not in stop]
    if not tokens:
        return None
    # prefer a found entity: return the longest token sequence the index can find.
    candidates = tokens[::-1]  # from end
    return candidates[0] if candidates else None


INTENTS = [
    ("callers",    re.compile(r"who\s+calls\s+(\w+)|what\s+calls\s+(\w+)|callers?\s+of\s+(\w+)|(\w+)\s+called\s+by|quem\s+chama\w*\s+(\w+)|(\w+)\s+chamad\w+\s+por", re.I)),
    ("callees",    re.compile(r"what\s+does\s+(\w+)\s+call|does\s+(\w+)\s+call|callees?\s+of\s+(\w+)|o\s+que\s+(\w+)\s+chama\w*", re.I)),
    ("where",      re.compile(r"where\s+is\s+(\w+)|where\s+are\s+(\w+)|location\s+of\s+(\w+)|onde\s+(?:esta|est\u00e1|fica)\s+(\w+)", re.I)),
    ("summary",    re.compile(r"what\s+does\s+(\w+)\s+do|summary\s+of\s+(\w+)|overview\s+of\s+(\w+)|describe\s+(\w+)|about\s+(\w+)|o\s+que\s+(\w+)\s+faz|para\s+que\s+serve\s+(\w+)", re.I)),
    ("imports",    re.compile(r"imports?\s+of\s+(\w+)|what\s+does\s+(\w+)\s+import|o\s+que\s+(\w+)\s+importa\w*", re.I)),
    ("importers",  re.compile(r"who\s+imports\s+(\w+)|(\w+)\s+imported\s+by|imports?\s+by\s+(\w+)|quem\s+importa\w*\s+(\w+)", re.I)),
    ("deps",       re.compile(r"dependencies?\s+of\s+(\w+)|what\s+does\s+(\w+)\s+need|(\w+)\s+depends\s+on|(\w+)\s+depende\w*\s+de", re.I)),
    ("revdeps",    re.compile(r"what\s+depends\s+on\s+(\w+)|reverse\s+dependencies?\s+of\s+(\w+)|needs?\s+(\w+)\s+by|o\s+que\s+depende\w*\s+de\s+(\w+)", re.I)),
    ("entry",      re.compile(r"entry\s+points|where\s+.*start|start\s+here|public\s+api|pontos?\s+de\s+entrada|por\s+onde\s+come\w*", re.I)),
    ("functions",  re.compile(r"functions?\s+in\s+(\w+)|methods?\s+in\s+(\w+)|fun\w*s?\s+em\s+(\w+)", re.I)),
    ("classes",    re.compile(r"classes?\s+in\s+(\w+)|classes?\s+em\s+(\w+)", re.I)),
    ("flows",      re.compile(r"\bflows?\b|\bfluxo\w*", re.I)),
    ("intents",    re.compile(r"\bintents?\b", re.I)),
    ("services",   re.compile(r"\bservices?\b|\bdomain\s+concepts?\b|\bservi\w*\s+de\s+dom\w*", re.I)),
    ("help",       re.compile(r"\bhelp\b|what\s+can\s+you\b|how\s+do\s+i\s+use|\bajuda\b|o\s+que\s+voce\s+faz", re.I)),
]


def _match_intent(q):
    for name, rx in INTENTS:
        if rx.search(q):
            return name
    return "summary"


BARE = {
    "entry points": "entry",
    "where do i start": "entry",
    "public api": "entry",
    "entrypoints": "entry",
}


def answer(index, question, verbose=False):
    """Answer a question with a structured result.

    Returns {"intent": str, "target": str|None, "facts": [{...}],
             "hypotheses": [{...}], "answer_text": str}
    """
    q = question.strip().lower()
    if q in BARE:
        intent = BARE[q]
    else:
        intent = _match_intent(q)

    if intent == "help":
        return _help()
    if intent == "entry":
        return _entry(index)

    target = _extract_target(question)
    if target:
        hits = index.find(target)
    else:
        hits = []

    if intent in ("flows", "intents", "services"):
        return _browse_hypotheses(index, intent)

    if not hits:
        return _notfound(intent, target, q)

    # prefer a Function over everything for call/method questions
    preferred = _pick(hits, intent)
    return _dispatch(index, intent, preferred, target)


def _pick(hits, intent):
    typerank = {"Function": 0, "Method": 1, "Module": 2, "Class": 3,
                "Repository": 4, "Flow": 5, "Intent": 6}
    best = None
    for h in hits:
        rank = typerank.get(h["type"], 10)
        if best is None or rank < typerank.get(best["type"], 10):
            best = h
    return best


def _dispatch(index, intent, node, target):
    nid = node["id"]
    if intent == "where":
        return _where(index, node)
    if intent == "callers":
        return _callers(index, node)
    if intent == "callees":
        return _callees(index, node)
    if intent == "summary":
        return _summary(index, node)
    if intent == "importers":
        return _importers(index, node)
    if intent == "imports":
        return _imports(index, node)
    if intent == "deps":
        return _deps(index, nid)
    if intent == "revdeps":
        return _revdeps(index, nid)
    if intent in ("functions", "classes"):
        return _contained(index, node, intent)
    return _summary(index, node)


# ---- answer builders (each returns the standard dict) ----------------------

def _result(intent, target, facts, hypotheses, text):
    return {"intent": intent, "target": target,
            "facts": facts, "hypotheses": hypotheses, "answer_text": text}


def _fact(label, nodes, extra=None):
    return {"label": label, "rows": [_row(n) for n in nodes], "extra": extra}

def _row(n):
    loc = n["evidence"][0]["source"] if n.get("evidence") else "?"
    return {"id": n["id"], "name": n["name"], "type": n["type"], "loc": loc}

def _hyp(node):
    conf, note = confmod.calibrate(node)
    return {"id": node["id"], "name": node["name"], "type": node["type"],
            "confidence": conf, "note": note, "evidence": node.get("evidence", [])}


def _where(index, node):
    ev = node.get("evidence", [])
    locs = [f"{e['source']} (confidence 1.0)" for e in ev]
    text = f"{node['type']} `{node['name']}` defined at " + ", ".join(locs) + "."
    return _result("where", node["name"], [_fact("evidence", [node])], [], text)


def _callers(index, node):
    c = index.callers_of(node["id"])
    text = (f"Callers of `{node['name']}`: {', '.join(n['name'] for n in c) if c else 'none found in this repo'} "
            f"({len(c)} facts, confidence 1.0).")
    return _result("callers", node["name"], [_fact("callers (facts)", c)], [], text)


def _callees(index, node):
    c = index.callees_of(node["id"])
    text = (f"`{node['name']}` calls: {', '.join(n['name'] for n in c) if c else 'none in this repo'} "
            f"({len(c)} facts, confidence 1.0).")
    return _result("callees", node["name"], [_fact("callees (facts)", c)], [], text)


def _summary(index, node):
    f = []
    text_parts = []
    if node["type"] == "Module":
        ms = index.module_summary(node["id"])
        f.append(_fact("classes in module", ms["classes"]))
        f.append(_fact("functions in module", ms["functions"]))
        imp = [n["name"] for n in ms["imports"]]
        f.append({"label": "imports (facts)", "rows": [{"id": n["id"], "name": n["name"],
                  "type": n["type"], "loc": n["evidence"][0]["source"] if n.get("evidence") else "?"}
                 for n in ms["imports"]], "extra": None})
        text_parts.append(f"Module `{node['name']}`: {len(ms['classes'])} class(es), "
                          f"{len(ms['functions'])} top-level function(s), {len(ms['imports'])} import(s).")
        doc = node.get("metadata", {}).get("docstring")
        if doc:
            text_parts.append(f"Module docstring: {doc[:300]}")
    else:
        doc = node.get("metadata", {}).get("doc")
        f.append(_fact("definition", [node]))
        if doc:
            text_parts.append(f"`{node['name']}` — {doc[:200]}")
        text_parts.append(f"Defined at {node['evidence'][0]['source'] if node.get('evidence') else '?'} (fact).")
    # hypotheses touching this entity
    hyps = []
    for e in index.artifact["edges"]:
        if (e["source"] == node["id"] and e["metadata"].get("hypothesis")
                and e["target"] in index.by_id):
            hyps.append(_hyp(index.by_id[e["target"]]))
        elif (e["target"] == node["id"] and e["metadata"].get("hypothesis")
              and e["source"] in index.by_id):
            hyps.append(_hyp(index.by_id[e["source"]]))
        if e["metadata"].get("hypothesis"):
            pass
    text = "\n".join(text_parts) or f"`{node['name']}`: see details below."
    return _result("summary", node["name"], f, hyps, text)


def _importers(index, node):
    imp = index.imported_by(node["id"]) if node["type"] == "Module" else []
    text = (f"Importers of `{node['name']}`: {', '.join(n['name'] for n in imp) if imp else 'none'} "
            f"({len(imp)} facts, confidence 1.0).")
    return _result("importers", node["name"], [_fact("importers (facts)", imp)], [], text)


def _imports(index, node):
    imp = index.imports_of(node["id"]) if node["type"] == "Module" else []
    text = (f"`{node['name']}` imports: {', '.join(n['name'] for n in imp) if imp else 'none'} "
            f"({len(imp)} facts, confidence 1.0).")
    return _result("imports", node["name"], [_fact("imports (facts)", imp)], [], text)


def _deps(index, nid):
    d = index.deps_closure([nid])
    deps = [index.by_id[x] for x in d if x in index.by_id]
    text = (f"Transitive dependencies of `{nid}`: {len(deps)} nodes "
            f"({', '.join(n['name'] for n in deps[:15])}{'...' if len(deps) > 15 else ''}).")
    return _result("deps", nid, [_fact("dependency closure (facts)", deps)], [], text)


def _revdeps(index, nid):
    d = index.reverse_deps([nid])
    deps = [index.by_id[x] for x in d if x in index.by_id]
    text = (f"Nodes that depend on `{nid}`: {len(deps)} ({', '.join(n['name'] for n in deps[:15])}).")
    return _result("revdeps", nid, [_fact("reverse dependency closure (facts)", deps)], [], text)


def _contained(index, node, which):
    kids = index.children(node["id"])
    ns = [index.by_id[e["target"]] for e in kids if e["target"] in index.by_id and e["relationship"] == "CONTAINS"]
    ns = [n for n in ns if n["type"].lower() == which[:-1]]  # functions -> Function
    text = (f"{which.title()} in `{node['name']}`: {', '.join(n['name'] for n in ns) if ns else 'none'}.")
    return _result(which, node["name"], [_fact(f"{which} (facts)", ns)], [], text)


def _entry(index):
    eps = index.entry_points()
    text = (f"Entry points (no callers in repo): {', '.join(n['name'] for n in eps[:15]) if eps else 'none found'}.")
    return _result("entry", None, [_fact("entry points (facts)", eps)], [], text)


def _browse_hypotheses(index, which):
    """Browse all hypotheses of a kind, calibrated."""
    kindmap = {"flows": "Flow", "intents": "Intent", "services": "Service"}
    kind = kindmap[which]
    hyp_nodes = [n for n in index.nodes if n["type"] == kind]
    hyps = [_hyp(n) for n in hyp_nodes]
    text = f"{len(hyps)} {kind} hypotheses (calibrated confidence):\n" + "\n".join(
        f"  - {h['id']} conf={h['confidence']} — {h['note']}" for h in hyps[:20])
    return _result(which, None, [], hyps, text)


def _notfound(intent, target, q):
    text = (f"I couldn't find `{target or q}` in the index. "
            f"Tip: try 'what does X do', 'calls X', 'where is X', 'imports of X', 'entry points'.")
    return _result(intent, target, [], [], text)


def _help():
    text = ("SSRL grounded Q&A (deterministic, evidence-backed). Example questions:\n"
            "  - what does retriever do / what is context\n"
            "  - who calls search | what does search call\n"
            "  - where is build\n"
            "  - imports of cli | what imports indexer\n"
            "  - dependencies of benchmark\n"
            "  - entry points\n"
            "  - flows | intents | services\n"
            "Answers split FACTS (confidence 1.0) from HYPOTHESES (calibrated).")
    return _result("help", None, [], [], text)