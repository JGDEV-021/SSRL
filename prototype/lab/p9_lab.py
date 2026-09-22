"""Phase 9 lab — micro-LLM proposer + experiment-harness seed (ADR-008).

1.  Builds the enriched artifact on a corpus, then runs the hypothesis
    proposer over Flows and Modules using a micro model (Qwen3-0.6B class)
    through a local provider.
2.  Prints context budgets (evidence bundles are tiny by design).
3.  Seeds a controlled-experiment grading sheet: for a set of questions, each
    has a BASELINE context (naive agent: raw names only) vs an SSRL context
    (grounded evidence bundles) — to be answered by participants/agents and
    graded (roadmap Phase 9; the "ask the agent" baseline).

Provider: probes Ollama at the default endpoint; uses the real model if
reachable, otherwise falls back to the deterministic MockProvider (offline).
Use --real to require the actual model (start Ollama + `ollama pull qwen3:0.6b`).

Usage:
    python lab/p9_lab.py [corpus-root] [--real] [--endpoint URL] [--model qwen3:0.6b]
"""

import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(ROOT)
sys.path.insert(0, SRC)
if os.name == "nt":
    os.environ.setdefault("PYTHONUTF8", "1")

from ssrl import cli, extract, index as indexmod, llm, semantics

DEFAULT_CORPUS = r"C:\Users\joaog\Downloads\JG-CODE\doc_rag"

SEED_QUESTIONS = [
    "who calls init_db",
    "where is embed",
    "which modules import db",
    "list the entry points",
    "what does the flow from search do",
    "which files does indexer depend on",
]


def main():
    argv = [a for a in sys.argv[1:] if a]
    corpus = next((a for a in argv if not a.startswith("--")), None) or DEFAULT_CORPUS
    flags = set(argv)
    endpoint = next((a.split("=", 1)[1] for a in argv if a.startswith("--endpoint=")), "http://localhost:11434")
    model = next((a.split("=", 1)[1] for a in argv if a.startswith("--model=")), "qwen3:0.6b")
    scope = next((a.split("=", 1)[1] for a in argv if a.startswith("--scope=")), "all")
    require_real = "--real" in flags

    print(f"=== SSRL Phase 9 lab: micro-LLM proposer (ADR-008) over `{corpus}` ===")

    art = extract.build(corpus, cache_dir=cli._cache_dir_for(corpus))
    art = semantics.enrich(art, verbose=False)
    idx = indexmod.Index(art)

    # ---- provider selection -------------------------------------------------
    provider = llm.OllamaProvider(endpoint, model)
    online = provider.probe()
    if online:
        print(f"[provider] {model} @ {endpoint} (reachable) — real proposals")
    elif require_real:
        print(f"error: {model} not reachable at {endpoint} (start Ollama / pull the model)", file=sys.stderr)
        return 2
    else:
        provider = llm.MockProvider()
        print(f"[provider] {model} NOT reachable at {endpoint} — using deterministic "
              f"MockProvider (offline). Start Ollama and rerun with --real for live runs.")

    # ---- context budgets ----------------------------------------------------
    flows = sorted((n for n in art["nodes"] if n["type"] == "Flow"), key=lambda n: n["id"])
    bundles = [llm.flow_bundle(idx, f) for f in flows]
    chars = [b["chars"] for b in bundles] or [0]
    print(f"\n[flows] {len(flows)}; bundle chars min={min(chars)} median={int(statistics.median(chars))} "
          f"max={max(chars)} (~tokens at ~3.7 chars/tok: {max(chars)//3.7:.0f}..)")

    # ---- propose -------------------------------------------------------------
    t1 = __import__("time").time()
    _, fstats = llm.run(idx, art, provider, scope=scope)
    elapsed = __import__("time").time() - t1
    print(f"\n[propose] scope={scope}")
    print(f"  requests={fstats['requests']} accepted={fstats['accepted']} "
          f"covered={fstats['covered']} rejected={fstats['rejected']} errors={fstats['errors']}")
    print(f"  tokens prompt={fstats['tokens_prompt']} eval={fstats['tokens_eval']} "
          f"elapsed_s={round(elapsed, 3)}  ({provider.name})")
    proposed = sorted((n for n in art["nodes"] if (n.get("metadata") or {}).get("origin") == "llm"),
                      key=lambda n: n["id"])
    print("\n  sample LLM-proposed intents:")
    for n in proposed[:8]:
        print(f"    {n['id']}: '{n['name']}' conf={n['confidence']} "
              f"rationale={n.get('metadata', {}).get('rationale', '')}")
    print(f"  total llm intents: {len(proposed)}")

    # ---- experiment seed ------------------------------------------------------
    seed_path = os.path.join(ROOT, "p9_experiment_seed.jsonl")
    rows = []
    for i, q in enumerate(SEED_QUESTIONS, 1):
        ans = extract_evidence(idx, art, q)
        rows.append({
            "id": f"q{i}", "question": q,
            "baseline_context": baseline_context(art, q),
            "ssrl_context": ans,
            "answer_baseline": "", "answer_ssrl": "", "graded": False,
        })
    with open(seed_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n[experiment seed] wrote {seed_path} ({len(rows)} questions, "
          f"baseline vs SSRL-grounded contexts, answers to be graded)")
    return 0


def baseline_context(art, question):
    """Naive-agent context: raw unit names only — no structure (Phase 9 baseline)."""
    names = sorted(n["name"] for n in art["nodes"]
                   if n["type"] in ("Module", "Function", "Class", "Method"))
    heads = [q.split()[-1] for q in question.split()]
    return f"Repository has {len(names)} Python units:\n" + ", ".join(names[:200])


def extract_evidence(idx, art, question):
    """Map a question to grounded evidence rows (deterministic, facts only)."""
    q = question.lower()
    out = []
    if "who calls" in q:
        name = q.rsplit(" ", 1)[-1]
        hits = idx.find(name) or []
        for h in hits[:3]:
            out.append({"question": q, "target": h["id"], "callers": sorted(
                {c["id"] for c in idx.callers_of(h["id"])})[:15]})
    elif "import" in q:
        target = q.rsplit(" ", 1)[-1].lower()
        for mid in sorted(n["id"] for n in art["nodes"] if n["type"] == "Module"):
            imp = sorted(i for i in (e["target"] for e in idx.children(mid, "IMPORTS"))
                         if i.startswith("module::"))
            if any(t.split("::")[-1].lower() == target for t in imp):
                out.append({"question": q, "module": mid, "imports": imp})
    elif "entry" in q:
        out.append({"question": q, "entry_points": sorted(n["id"] for n in idx.entry_points())})
    elif "flow" in q:
        for fn in sorted((n for n in art["nodes"] if n["type"] == "Flow"), key=lambda n: n["id"]):
            out.append({"question": q, "flow": fn["id"],
                        "steps": sorted(fn.get("metadata", {}).get("steps", []))[:30]})
    elif "depend" in q:
        for mid in sorted(n["id"] for n in art["nodes"] if n["type"] == "Module"):
            deps = sorted(m for m in idx.deps_closure([mid]) if m.startswith("module::"))
            if deps:
                out.append({"question": q, "module": mid, "deps": deps[:30]})
    elif "where" in q:
        name = q.rsplit(" ", 1)[-1]
        for h in (idx.find(name) or [])[:5]:
            out.append({"question": q, "node": h["id"],
                        "loc": h["evidence"][0]["source"] if h.get("evidence") else "-"})
    return out or [{"question": q, "note": "no structural hit"}]


if __name__ == "__main__":
    sys.exit(main())