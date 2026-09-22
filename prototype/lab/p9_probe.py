"""Phase 9 probe battery — WHY does the micro LLM refuse, and what stops it?

Systematic A/B over orthogonal factors believed to drive refusals by a
0.6 B instruct model on lookup/extraction tasks:

  A. context rendering   json (raw evidence rows) | nl (natural sentences,
                         same facts) | answer (answer-framed assertions)
  B. prompt contract     lookup (refusal-bust) | cli (authoritative tool)
                         | fewshot (2 in-context examples)
  C. thinking            think=False | think=True

Every answer is classified as reject / empty / answer; answer rows are also
scored (entity-level F1 vs the deterministic facts gold). The output grid
decides whether Phase 9 closes or the context system gets improved.

Usage:
  python lab/p9_probe.py --questions=q2,q3,q5 --variants=all
  python lab/p9_probe.py --all --variants=json_lookup,answer_lookup
"""

import json
import os
import re
import statistics
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "lab"))

from ssrl import cli, extract, index as indexmod, semantics

from p9_lab import SEED_QUESTIONS, baseline_context, extract_evidence
from p9_study import (raw_chat, gold_for, score, _norm, tokens_of,
                      AGENT_SYSTEM as AGENT_LOOKUP)

ENDPOINT = "http://localhost:11434"
MODEL = "qwen3:0.6b"

REFUSAL_PATTERNS = [
    r"insufficient", r"cannot answer", r"can'?t answer", r"unable",
    r"not (enough|sufficient)", r"none of the", r"no (information|context|evidence|data)",
    r"does not (contain|allow|provide|have)", r"do ?n'?t (have|contain)",
    r"only (contain|provide)", r"no relevant", r"cannot (determine|find|infer)",
    r"missing ", r"doesn'?t (provide|contain|include)",
]

AGENT_CLI = (
    "You are a deterministic code-analysis tool. The context below is "
    "authoritative — it is auto-generated from the code index of a real "
    "repository and it always contains the exact answer to the question. "
    "Extract it and reproduce the identifiers verbatim, exactly as written, "
    "one per line. Do not summarize, do not refuse, do not add commentary, "
    "do not mention the context."
)

AGENT_FEWSHOT = (
    "Extract the exact answer to the question from the context and list only "
    "the requested identifiers, verbatim, one per line.\n"
    "Example 1:\nQuestion: who calls func::db::connect\nContext:\n"
    "The functions that call func::db::connect are: func::ingest::read_file, "
    "func::retriever::search.\n"
    "Answer:\nfunc::ingest::read_file\nfunc::retriever::search\n"
    "Example 2:\nQuestion: list the entry points\nContext:\n"
    "The repository entry points are: main, search, index_scripts.\n"
    "Answer:\nmain\nsearch\nindex_scripts\n"
    "Example 3:\nQuestion: what does the flow from search do\nContext:\n"
    "The flow flow::search executes these steps in order: func::db::connect, "
    "func::db::init_db, func::retriever::search.\n"
    "Answer:\nfunc::db::connect\nfunc::db::init_db\nfunc::retriever::search\n"
    "Now answer the real question below, same format: identifiers only, "
    "one per line, exact spelling. The context always contains the answer."
)

AGENT_FEWSHOT_CLI = (
    "You are a deterministic code-analysis tool. " + AGENT_FEWSHOT
)

VARIANTS = {
    "json_lookup":   {"ctx": "json",   "system": AGENT_LOOKUP, "think": False},
    "nl_lookup":     {"ctx": "nl",     "system": AGENT_LOOKUP, "think": False},
    "answer_lookup": {"ctx": "answer", "system": AGENT_LOOKUP, "think": False},
    "json_think":    {"ctx": "json",   "system": AGENT_LOOKUP, "think": True},
    "nl_think":      {"ctx": "nl",     "system": AGENT_LOOKUP, "think": True},
    "answer_think":  {"ctx": "answer", "system": AGENT_LOOKUP, "think": True},
    "json_cli":      {"ctx": "json",   "system": AGENT_CLI,    "think": False},
    "answer_cli":    {"ctx": "answer", "system": AGENT_CLI,    "think": False},
    "json_fewshot":  {"ctx": "json",   "system": AGENT_FEWSHOT, "think": False},
    "answer_fewshot": {"ctx": "answer", "system": AGENT_FEWSHOT, "think": False},
    "cli_fewshot":   {"ctx": "answer", "system": AGENT_FEWSHOT_CLI, "think": False},
}


def classify(answer):
    if not answer or len(answer.strip()) < 3:
        return "empty"
    low = answer.lower()
    if any(re.search(p, low) for p in REFUSAL_PATTERNS):
        return "reject"
    return "answer"


def render_json(rows):
    return p9_fmt_evidence(rows)


def _items(row):
    for k in ("callers", "imports", "entry_points", "steps", "deps", "entities", "locations"):
        v = row.get(k)
        if v:
            return v
    return []


def render_nl(rows):
    """Same facts as the JSON rows, but as plain sentences (no synthesis)."""
    if not rows:
        return "(no structural evidence found)"
    lines = []
    for r in rows:
        if "note" in r:
            continue
        parts = []
        for k, v in r.items():
            if isinstance(v, list) and v:
                parts.append(f"{k}: {', '.join(v)}")
            elif isinstance(v, str) and k in ("node", "module", "flow", "target", "loc"):
                parts.append(f"{k}: {v}")
        if parts:
            lines.append("Evidence row: " + "; ".join(parts) + ".")
    return "Facts extracted from the code index:\n" + "\n".join(lines) + "\n"


def render_answer(rows):
    """Answer-framed assertions: the deterministic layer states the answer.",
    """
    if "where is" in rows[0].get("question", ""):
        out = []
        for r in rows:
            if r.get("node") and r.get("loc"):
                out.append(f"The symbol {r['node']} is defined at: {r['loc']}.")
        return "\n".join(out) + "\n" if out else render_nl(rows)
    if "who calls" in rows[0].get("question", ""):
        out = []
        for r in rows:
            if r.get("callers"):
                out.append(f"The functions that call {r.get('target', '?')} are: "
                           + ", ".join(r["callers"]) + ".")
        return "\n".join(out) + "\n" if out else render_nl(rows)
    if "import" in rows[0].get("question", ""):
        importers = sorted({r["module"].split("::")[-1]
                            for r in rows
                            if any("module::db" == t or t.endswith("::db")
                                   for t in r.get("imports", []))})
        return f"The modules that import module::db are: {', '.join(importers) or '(none)'}.\n"
    if "entry" in rows[0].get("question", ""):
        eps = sorted({e for r in rows for e in r.get("entry_points", [])})
        return f"The repository entry points are: {', '.join(eps)}.\n"
    if "flow" in rows[0].get("question", ""):
        out = []
        for r in rows:
            if r.get("steps"):
                out.append(f"The flow {r['flow']} executes these steps in order: "
                           + ", ".join(r["steps"]) + ".")
        return "\n".join(out) + "\n" if out else render_nl(rows)
    if "depend" in rows[0].get("question", ""):
        for r in rows:
            if r.get("deps"):
                return f"The module {r['module']} depends on these modules: " \
                       + ", ".join(r["deps"]) + ".\n"
        return render_nl(rows)
    return render_nl(rows)


def p9_fmt_evidence(rows):
    """Identical to p9_study.fmt_evidence (JSON rendering). Non-mutating: the
    same evidence rows are re-rendered by several variants (json runs first),
    and the answer-framed render reads the 'question' key back."""
    if not rows:
        return "(no structural evidence found)"
    lines = []
    for r in rows:
        r = dict(r)
        r.pop("question", None)
        r.pop("note", None)
        lines.append("  " + json.dumps(r, ensure_ascii=False))
    return "Evidence (SSRL layer, deterministic facts):\n" + "\n".join(lines)


def main():
    argv = [a for a in sys.argv[1:] if a]
    corpus = "C:\\Users\\joaog\\Downloads\\JG-CODE\\doc_rag"
    flags = set(argv)
    qsel = next((a.split("=", 1)[1] for a in argv if a.startswith("--questions=")), None)
    vsel = next((a.split("=", 1)[1] for a in argv if a.startswith("--variants=")), "all")

    art = extract.build(corpus, cache_dir=cli._cache_dir_for(corpus))
    art = semantics.enrich(art, verbose=False)
    idx = indexmod.Index(art)
    names = {n["name"].lower() for n in art["nodes"]}
    names |= {_norm(n["name"]) for n in art["nodes"]}
    names |= {"insufficient", "unknown", "none", "context"}

    pairs = [("q%d" % i, q) for i, q in enumerate(SEED_QUESTIONS, 1)]
    if qsel:
        wanted = {w.strip() for w in qsel.split(",")}
        pairs = [p for p in pairs if p[0] in wanted]
    variants = list(VARIANTS.items()) if vsel == "all" else \
        [(n, VARIANTS[n]) for n in vsel.split(",") if n in VARIANTS]
    print(f"=== probe battery: {MODEL} @ {ENDPOINT} — {len(pairs)} questions x "
          f"{len(variants)} variants = {len(pairs)*len(variants)} calls ===")

    rows = []
    for qid, q in pairs:
        gg = gold_for(idx, art, q)
        ev = extract_evidence(idx, art, q)
        rendered = None
        for vname, v in variants:
            if v["ctx"] == "json":
                ctx = render_json(list(ev))
            elif v["ctx"] == "nl":
                ctx = render_nl(list(ev))
            else:
                ctx = render_answer(list(ev))
            rendered = ctx
            body = {"think": v["think"], "num_predict": 700}
            sysmsg = v["system"]
            if v["think"]:
                sysmsg = "Think step by step, then answer. " + sysmsg
            answer, usage, elapsed = raw_chat(MODEL, ENDPOINT, sysmsg,
                                              f"Question: {q}\n\nContext:\n{ctx}",
                                              num_predict=body["num_predict"])
            outcome = classify(answer)
            sc = score(answer, gg, names) if outcome == "answer" else {"f1": 0.0, "recall": 0.0,
                                                                       "precision": 0.0}
            rows.append({"id": qid, "question": q, "variant": vname, "ctx_chars": len(ctx),
                         "outcome": outcome, "answer": answer, "tokens_prompt": usage["prompt"],
                         "tokens_eval": usage["eval"], "elapsed_s": round(elapsed, 3),
                         "f1": sc.get("f1", 0.0), "recall": sc.get("recall", 0.0),
                         "gold": gg["text"]})
            print(f"  {qid} {vname:14} {outcome:6} f1={rows[-1]['f1']:.2f} "
                  f"tok={usage['prompt']}/{usage['eval']} t={elapsed:.1f}s :: "
                  f"{answer[:70]!r}")

    write(rows, pairs)


def write(rows, pairs):
    out_pre = os.path.join(ROOT, "lab", "p9_probe")
    with open(out_pre + "_results.json", "w", encoding="utf-8") as f:
        json.dump({"model": MODEL, "endpoint": ENDPOINT, "rows": rows}, f,
                  ensure_ascii=False, indent=1)
    vorder = list(VARIANTS)
    md = ["# Phase 9 probe battery — refusals of qwen3:0.6b",
          "",
          f"Model `{MODEL}` @ `{ENDPOINT}` · {len(pairs)} questions x "
          f"{len(vorder)} variants · temp 0.",
          "",
          "Legend: `reject`=refusal phrase detected · `empty`=no output · "
          "`answer`=responded (F1 vs facts gold shown).",
          "",
          "## Matrix",
          "",
          "| | " + " | ".join(v for v in vorder) + " |",
          "| --- |" + " --- |" * len(vorder),
          ]
    qids = [qid for qid, _ in pairs]
    for qid in qids:
        sub = [r for r in rows if r["id"] == qid]
        rd = {r["variant"]: r for r in sub}
        line = [qid]
        for v in vorder:
            r = rd.get(v)
            if r is None:
                line.append("—")
            else:
                a, f = r["outcome"], r["f1"]
                line.append(f"{a}({f:.2f})" if a == "answer" else f"**{a}**")
        md.append("| " + " | ".join(line) + " |")
    md.append("")
    byv = {}
    for r in rows:
        d = byv.setdefault(r["variant"], {"reject": 0, "empty": 0, "answer": 0, "f1s": []})
        d[r["outcome"]] += 1
        if r["outcome"] == "answer":
            d["f1s"].append(r["f1"])
    md.append("## Aggregates per variant")
    md.append("")
    md.append("| variant | reject | empty | answer | answer f1 mean |")
    md.append("| --- | --- | --- | --- | --- |")
    for v in vorder:
        d = byv.get(v, {})
        f1m = round(statistics.mean(d.get("f1s") or [0.0]), 3)
        md.append(f"| {v} | {d.get('reject', 0)} | {d.get('empty', 0)} | "
                  f"{d.get('answer', 0)} | {f1m} |")
    md.append("")
    md.append("## Detail")
    md.append("")
    for r in rows:
        md.append(f"### {r['id']} · {r['variant']} — {r['outcome']} (f1 {r['f1']:.2f})")
        md.append(f"- tokens {r['tokens_prompt']}/{r['tokens_eval']} · "
                  f"ctx {r['ctx_chars']} chars · {r['elapsed_s']}s")
        md.append(f"- gold: `{r['gold']}`")
        md.append(f"- answer: `{r['answer'][:400]}`")
        md.append("")
    with open(out_pre + "_results.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"\nwrote {out_pre}_results.json/.md ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())