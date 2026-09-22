"""Phase 9 study execution (draft pass) — context gradient, micro-LLM agent.

For each seeded question the SAME micro model (qwen3:0.6b by default) answers
under TWO conditions:

  baseline  — naive "ask-the-agent" context: raw unit names, no structure
              (roadmap Phase 9 threat plaintext: agent has only a name soup)
  ssrl      — grounded context: evidence bundles derived from the SSRL layer
              (facts + flows, importers, callers, entry points, deps closure)

Answers are scored against a GOLD STANDARD computed deterministically from the
layer facts (callers/importers/deps/entry-point/flow steps/locations), so the
draft pilot is reproducible offline. Metrics per condition: recall, precision,
F1 (entity-level against repo names), elapsed_s, prompt/eval tokens.

Outputs (lab/):
  p9_study_results.json  — machine-readable rows + aggregates
  p9_study_results.md    — human-readable report
  p9_study_graded.jsonl  — the experiment seed with answers + draft grade fields

Usage:
    python lab/p9_study.py [corpus-root] [--model qwen3:0.6b] [--real] [--out PREFIX]
    Default: probes Ollama; --real requires a reachable model (else exit 2);
    offline without --real uses the deterministic MockProvider (smoke only).
"""

import json
import os
import re
import statistics
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(ROOT)
sys.path.insert(0, SRC)
sys.path.insert(0, ROOT)
if os.name == "nt":
    os.environ.setdefault("PYTHONUTF8", "1")

from ssrl import cli, extract, index as indexmod, llm, qa, semantics
from p9_lab import DEFAULT_CORPUS, SEED_QUESTIONS, baseline_context, extract_evidence

AGENT_SYSTEM = (
    "You are a deterministic code-analysis tool. The context below is "
    "authoritative — it is auto-generated from the code index of a real "
    "repository and it always contains the exact answer to the question. "
    "Extract it and reproduce the identifiers verbatim, exactly as written, "
    "one per line. Do not summarize, do not refuse, do not add commentary, "
    "do not mention the context."
)

STOP_WORDS = {"the", "do", "does", "is", "on", "of", "to", "and", "list", "all",
              "depend", "depends", "dependency", "dependencies", "files", "which",
              "what", "who", "where", "from", "for", "are", "you"}


def _norm(e):
    tail = e.split("::")[-1]
    if tail.endswith(".py"):
        tail = tail[:-3]
    return tail.split(":")[0].lower()


def word_for(idx, q):
    for w in re.split(r"[^A-Za-z0-9_.]+", q):
        if len(w) < 3 or w.lower() in STOP_WORDS:
            continue
        hits = idx.find(w) or []
        exact = [h for h in hits if h["name"] == w]
        if exact:
            return exact[0]["id"]
        last = [h for h in hits if h["id"].split("::")[-1] == w]
        if last:
            return last[0]["id"]
    for n in idx.artifact["nodes"]:
        if n["id"].split("::")[-1] == w:
            return n["id"]
    return None


def module_id_for(idx, q):
    for w in re.split(r"[^A-Za-z0-9_.]+", q):
        if len(w) < 3 or w.lower() in STOP_WORDS:
            continue
        hits = idx.find(w) or []
        mods = [h["id"] for h in hits if h.get("type") == "Module"]
        if mods:
            return mods[0]
        direct = [n["id"] for n in idx.artifact["nodes"]
                  if n.get("type") == "Module" and n["id"].split("::")[-1] == w]
        if direct:
            return direct[0]
    return None


def module_importers(idx, mid):
    out = []
    for n in idx.artifact["nodes"]:
        if n["type"] != "Module":
            continue
        for e in idx.children(n["id"], "IMPORTS"):
            if e["target"] == mid:
                out.append(_norm(n["id"]))
    return sorted(set(out))


def gold_for(idx, art, question):
    q = question.lower()
    if "who calls" in q:
        target = word_for(idx, q)
        callers = sorted({idx.node(c["id"])["name"]
                          for c in idx.callers_of(target)}) if target else []
        return {"kind": "callers", "target": target,
                "entities": [c for c in callers if c],
                "text": f"callers of {target or '?'}: {', '.join(sorted(callers))}"}
    if "where is" in q:
        target = word_for(idx, q)
        locs = [n["evidence"][0]["source"] for n in [idx.node(target)] if n and n.get("evidence")]
        return {"kind": "location", "target": target, "entities": [_norm(l) for l in locs],
                "text": f"locations: {', '.join(locs) or '(none)'}"}
    if "import" in q:
        mid = module_id_for(idx, q) or (word_for(idx, q) or "")
        importers = module_importers(idx, mid) if mid else []
        return {"kind": "importers", "target": mid, "entities": importers,
                "text": f"modules importing {mid}: {', '.join(importers) or '(none)'}"}
    if "entry" in q:
        eps = sorted(n["id"] for n in idx.entry_points())
        return {"kind": "entry_points", "entities": [_norm(e) for e in eps],
                "text": f"entry points ({len(eps)}): {', '.join(eps)}"}
    if "flow" in q:
        flows = sorted((n for n in art["nodes"] if n["type"] == "Flow"),
                       key=lambda n: n["id"])
        key = word_for(idx, q) or ""
        picked = next((f for f in flows if key and key.split("::")[-1] in f["id"]), flows[0])
        steps = sorted(picked.get("metadata", {}).get("steps", []))
        return {"kind": "flow", "target": picked["id"], "entities": [_norm(s) for s in steps],
                "text": f"flow {picked['id']} steps ({len(steps)}): {', '.join(steps)}"}
    if "depend" in q:
        mid = module_id_for(idx, q)
        deps = sorted({_norm(m) for m in idx.deps_closure([mid])
                       if m.startswith("module::")}) if mid else []
        return {"kind": "deps", "target": mid, "entities": deps,
                "text": f"deps of {mid}: {', '.join(deps) or '(none)'}"}
    return {"kind": "generic", "entities": [], "text": ""}


def tokens_of(text):
    out = set()
    for t in re.findall(r"[a-z_][a-z0-9_.]*", (text or "").lower()):
        out.add(_norm(t) if t.endswith(".py") else t)
    return out


def score(answer, gold, names):
    ans_tok = tokens_of(answer)
    golds = list(dict.fromkeys(_norm(e) for e in gold["entities"] if e))
    hit_set = ans_tok & set(golds)
    resp = ans_tok & (names | set(golds))
    recall = (len(hit_set) / len(golds)) if golds else 0.0
    precision = (len(hit_set) / len(resp)) if resp else 0.0
    f1 = (2 * recall * precision / (recall + precision)) if (recall + precision) else 0.0
    return {"hits": sorted(hit_set), "gold": golds, "recall": round(recall, 3),
            "precision": round(precision, 3), "f1": round(f1, 3),
            "extra": sorted(resp - set(golds))[:10]}


def raw_chat(model, endpoint, system, user, timeout=120.0, num_predict=500):
    """Minimal /api/chat free-form call (think off, temp 0). Returns (text, usage, elapsed)."""
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "think": False,
        "options": {"temperature": 0.0, "num_predict": num_predict},
    }
    req = urllib.request.Request(f"{endpoint}/api/chat", data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"}, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    elapsed = time.time() - t0
    text = ((data.get("message") or {}).get("content", "") or "").strip()
    return text, {"prompt": data.get("prompt_eval_count", 0), "eval": data.get("eval_count", 0)}, elapsed


def main():
    argv = [a for a in sys.argv[1:] if a]
    corpus = next((a for a in argv if not a.startswith("--")), None) or DEFAULT_CORPUS
    flags = set(argv)
    model = next((a.split("=", 1)[1] for a in argv if a.startswith("--model=")), "qwen3:0.6b")
    endpoint = next((a.split("=", 1)[1] for a in argv if a.startswith("--endpoint=")), "http://localhost:11434")
    out_pre = next((a.split("=", 1)[1] for a in argv if a.startswith("--out=")), "p9_study")
    real = "--real" in flags
    name_tok = model.replace(":", "_").replace(".", "_")

    print(f"=== Phase 9 study (draft pass) — corpus `{corpus}`, agent `{model}` ===")
    art = extract.build(corpus, cache_dir=cli._cache_dir_for(corpus))
    art = semantics.enrich(art, verbose=False)
    idx = indexmod.Index(art)
    names = {n["name"].lower() for n in art["nodes"]}
    names |= {_norm(n["name"]) for n in art["nodes"]}
    names |= {"insufficient", "unknown", "none", "context"}

    provider = llm.OllamaProvider(endpoint, model)
    if provider.probe():
        print(f"[agent] {model} @ {endpoint} — live")
        agent = (model, endpoint)
    elif real:
        print(f"error: {model} not reachable at {endpoint}", file=sys.stderr)
        return 2
    else:
        agent = None
        print(f"[agent] {model} NOT reachable — deterministic MockProvider smoke (use --real for live)")

    gold = {q: gold_for(idx, art, q) for q in SEED_QUESTIONS}
    rows, graded = [], []
    for i, q in enumerate(SEED_QUESTIONS, 1):
        gg = gold[q]
        conds = [("baseline", baseline_context(art, q)),
                 ("ssrl", fmt_evidence(extract_evidence(idx, art, q))),
                 ("layer", None)]
        for cond, ctx in conds:
            if cond == "layer":
                ans = qa.answer(idx, q)
                answer = ans.get("answer_text", "")
                usage, elapsed = {"prompt": 0, "eval": 0}, 0.001
            elif agent is None:
                answer = (f"Mock: gold hint = {gg['text']}") if cond == "ssrl" else f"Mock answer for {q}"
                usage = {"prompt": len(ctx) // 4, "eval": len(answer) // 4}
                elapsed = 0.001
            else:
                answer, usage, elapsed = raw_chat(agent[0], agent[1], AGENT_SYSTEM,
                                                  f"Question: {q}\n\nContext:\n{ctx}")
            sc = score(answer, gg, names)
            rows.append({"id": f"q{i}", "question": q, "condition": cond,
                         "answer": answer, "gold": gg["text"],
                         "elapsed_s": round(elapsed, 3),
                         "tokens_prompt": usage["prompt"], "tokens_eval": usage["eval"],
                         **sc})
            graded.append({"id": f"q{i}", "question": q, "condition": cond,
                           "answer": answer, "graded": True, "draft": True,
                           "score": {k: sc[k] for k in ("recall", "precision", "f1", "hits")}})
            print(f"  q{i} [{cond:8}] r={sc['recall']:.2f} p={sc['precision']:.2f} "
                  f"f1={sc['f1']:.2f} tok={usage['prompt']}/{usage['eval']} t={elapsed:.1f}s")

    write_outcomes(rows, graded, gold, out_pre, name_tok)
    return 0


def fmt_evidence(rows):
    if not rows:
        return "(no structural evidence found)"
    lines = []
    for r in rows:
        r = dict(r)
        r.pop("question", None)
        r.pop("note", None)
        lines.append("  " + json.dumps(r, ensure_ascii=False))
    return "Evidence (SSRL layer, deterministic facts):\n" + "\n".join(lines)


def write_outcomes(rows, graded, gold, out_pre, name_tok):
    def agg(cond):
        sub = [r for r in rows if r["condition"] == cond]
        return {"f1_mean": round(statistics.mean(r["f1"] for r in sub), 3),
                "recall_mean": round(statistics.mean(r["recall"] for r in sub), 3),
                "tokens_prompt": sum(r["tokens_prompt"] for r in sub),
                "tokens_eval": sum(r["tokens_eval"] for r in sub),
                "elapsed_s": round(sum(r["elapsed_s"] for r in sub), 2)}

    rel = {
        "corpus": "doc_rag",
        "agent": name_tok,
        "method": "draft automated pass, entity-level F1 vs deterministic gold (facts)",
        "rows": rows,
        "aggregates": {"baseline": agg("baseline"), "ssrl": agg("ssrl"), "layer": agg("layer")},
        "gold": {q: v["text"] for q, v in gold.items()},
    }
    with open(os.path.join(ROOT, f"{out_pre}_results.json"), "w", encoding="utf-8") as f:
        json.dump(rel, f, ensure_ascii=False, indent=1)
    with open(os.path.join(ROOT, f"{out_pre}_graded.jsonl"), "w", encoding="utf-8") as f:
        for g in graded:
            f.write(json.dumps(g, ensure_ascii=False) + "\n")

    b, s, l = (rel["aggregates"]["baseline"], rel["aggregates"]["ssrl"],
               rel["aggregates"]["layer"])
    md = [
        f"# Phase 9 study — draft automated pass (`{name_tok}`)",
        "",
        f"Corpus: `doc_rag` (31 files) · agent: `{name_tok}` · 6 questions x 3 conditions.",
        f"Scoring: entity-level recall/precision/F1 against a deterministic gold standard computed",
        "from SSRL facts. This is the ROUTINE draft (single model, single corpus,",
        "automated proxy). The definitive study (multi-participant, human grading)",
        "is planned in REPORT-P9. The 'layer' condition is the deterministic `ask`",
        "projection — no LLM — included as the oracle reference.",
        "",
        "## Aggregates (n=6)",
        "",
        "| condition | F1 mean | recall mean | tokens prompt | tokens eval | elapsed_s |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| baseline (raw names + LLM) | {b['f1_mean']} | {b['recall_mean']} | {b['tokens_prompt']} | {b['tokens_eval']} | {b['elapsed_s']} |",
        f"| ssrl (grounded facts + LLM) | {s['f1_mean']} | {s['recall_mean']} | {s['tokens_prompt']} | {s['tokens_eval']} | {s['elapsed_s']} |",
        f"| layer (deterministic `ask`, no LLM) | {l['f1_mean']} | {l['recall_mean']} | — | — | {l['elapsed_s']} |",
        "",
        "## Ground truth (gold, from the layer)",
        "",
    ]
    for q, t in rel["gold"].items():
        md.append(f"- `{q}` → {t}")
    md += ["", "## Per-question results", ""]
    for r in rows:
        md += [f"### q{r['id'][1:]}.{r['condition']} — {r['question']}",
               f"- score: recall {r['recall']} precision {r['precision']} f1 {r['f1']}",
               f"- tokens {r['tokens_prompt']}/{r['tokens_eval']} · {r['elapsed_s']}s · gold: {r['gold']}",
               f"- answer: {r['answer'][:280]}"]
    with open(os.path.join(ROOT, f"{out_pre}_results.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    print(f"\ngold & graded: {out_pre}_results.json / {out_pre}_results.md / {out_pre}_graded.jsonl")


if __name__ == "__main__":
    sys.exit(main())