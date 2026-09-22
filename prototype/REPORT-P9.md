# REPORT-P9 — Phase 9: Micro-LLM Proposer & Experimental-Validation Groundwork

**Version:** v0.7.0 · **Date:** 2026 · **Status:** complete (study execution = next)
**Governance:** roadmap.md Phase 9 (Experimental Validation); ADR-007 (RN-4:
LLM last, proponent only) + **ADR-008** (new: the LLM component is a micro
model — *where it works, what it answers, what context it receives*).

---

## 1. Goal & the author directive

Phase 9 exists to *measure the claim, not just build the thing*. The author
directive sharpened the LLM side of it:

> "O LLM a ser usado nesta fase é um **MICRO LLM** (classe Qwen3-0.6B),
> focado em velocidade — **ajuste toda a arquitetura do sistema de LLM**:
> onde ela vai trabalhar, o que vai responder, o que vai ser passado como
> contexto."

So this phase redesigns the whole LLM architecture around three questions,
answered in ADR-008 and implemented in `ssrl/llm.py`.

## 2. The architecture in three answers

### 2.1 Where it works — exactly one optional stage

```
build ──▶ enrich ──────────▶ ask / narrative / impact / mcp     (deterministic,
    │            │                                              never calls LLM)
    │            ▼
    │      [propose]  ◀── micro model, the ONLY LLM stage       (optional, cheap)
    │            │
    ▼            ▼
        artifact (+LLMProposal hypotheses only if --out)
```

The deterministic pipeline never touches the model (ADR-007 baseline
preserved). `propose` is **pure**: it materializes hypotheses at 0 net change to
source; a provider failure returns `None` outputs (no errors, artifact
untouched) and the CLI exits 3 with "start the server or pass `--mock`".
Nothing in `__init__.py` imports `llm` — like MCP, it is an oncology-layer
addition.

### 2.2 What it answers — closed tasks only

| Task | Input unit | Output | Guardrails |
| --- | --- | --- | --- |
| A — `flow_intent` | a Flow (chain of CALLS from a root) | label, ≤ **6 words** | `parse_flow_decision` lenient JSON; word-count + conf clamp; drift → rejected |
| B — `unit_role` | a Module/Class | role from closed taxonomy `persistence\|model\|service\|config\|infra\|entrypoint\|controller\|ui\|util\|unknown` | `parse_unit_decision`; off-taxonomy → rejected |

Both: temperature 0, JSON requested, `confidence` clamped to [0.3, 0.5] *before*
calibration applies the LLM ceiling (0.5). No open-ended reasoning, no code
generation, no long-form text.

### 2.3 What context is passed — tiny evidence bundles (facts only)

Both bundles are built from **facts** (signature + callees + contained units +
imports), never source bodies, never git history:

| Bundle | Cap | doc_rag measured (10 flows) |
| --- | --- | --- |
| `flow_bundle` | ≤ 2600 chars | min=223, **median=553**, max=1279 (~345 tokens at 3.7 chars/tok) |
| `unit_bundle` | ≤ 2200 chars | — |

A 0.6 B model's whole context window covers any bundle several times over —
that is the "micro" design: throughput and deliver-on-time come from context
sizes, not model size.

## 3. Model proposes, structure disposes

Accepted decisions become `Intent` nodes (same shape as `semantics.py` intents):

```json
{ "id": "intent::flow::func::db::setup:handle-setup",
  "type": "Intent", "name": "handle setup",
  "confidence": 0.5,
  "evidence": [{ "type": "LLMProposal", "weight": 0.5, "source": "llm" }],
  "metadata": { "origin": "llm", "rationale": "...", "llm_conf": 0.55, "target": "...", "hypothesis": true } }
```

- **Ceiling:** `confidence.SOURCE_CEILING["LLMProposal"] = 0.5` — reserved on
  day one, now used. `calibrate` therefore outputs ≤ 0.5 with the
  "weak hypothesis — treat as suggestive" note.
- **Never overwrites:** `apply_proposals` skips any intent already
  covered/derived deterministically; structural evidence is untouched.
- **Traceable:** `origin:"llm"` makes LLM originated intents trivially
  distinguishable in `audit` and narrative.

## 4. Implementation map

| Piece | Where |
| --- | --- |
| Providers: `OllamaProvider` (`/api/chat`), `OpenAICompatProvider` (`/v1/chat/completions`), `MockProvider` (deterministic) | `ssrl/llm.py` |
| Bundles, tasks, lenient parsers, validation | `ssrl/llm.py` (`flow_bundle`, `unit_bundle`, `parse_flow_decision`, `parse_unit_decision`, `propose_flows`, `propose_units`, `apply_proposals`, `run`) |
| CLI `propose <repo> [--provider|--endpoint|--model|--timeout|--scope|--mock|--out|--cache]` | `ssrl/cli.py` |
| Lab + experiment seed | `lab/p9_lab.py` → `lab/p9_experiment_seed.jsonl` |
| Decision | `research/decisions/ADR-008-micro-llm-proponent.md` |
| Version | `ssrl/__init__.py` 0.6.0 → 0.7.0 |

Budgeting: timeout 30 s, **zero retries**, per-request failures → 1
rejected attempt counted in stats (`errors`), artifact never mutated on the
failure path.

## 5. Lab: offline run on a real corpus (doc_rag, 31 files, enrich)

No local model was reachable in this environment, so the lab probed the
endpoint and fell back to the deterministic mock — exactly the graceful gating
a CI/slow environment needs (`--real` forces the model and errors otherwise).

```
[provider] qwen3:0.6b NOT reachable at http://localhost:11434 — using MockProvider
[flows]    10; bundle chars min=223 median=553 max=1279 (~345 tokens)
[propose]  scope=all
  requests=49 accepted=49 covered=0 rejected=0 errors=0
  tokens prompt=4776 eval=1185 elapsed_s=0.004 (mock)
  sample: intent::class::embedder::DocEmbedder:handle-doc-embedder 'service' conf=0.5
          intent::flow::func::db::get_meta_int:handle-get-meta-int 'handle get_meta_int'
  total llm intents: 49   (10 flows + 39 units)
```

- **Determinism (NFR-4):** two identical `propose --scope all --out` runs
  produce byte-comparable intent sets — ids + names + rationales identical.
- **CLI paths:** offline without `--mock` → `exit 3` + friendly message;
  `--mock` → full stats JSON + proposals + `--out` artifact written.

### 5.1 Live run (qwen3:0.6b via Ollama, doc_rag, enrich)

After fixing the provider (see ADR-008 note on Qwen3 *thinking*), a live run
against the real model:

| scope | requests | accepted | covered | rejected | errors | tokens prompt/eval | elapsed_s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| flows | 10 | 10 | 0 | 0 | 0 | 3470 / 361 | 62.4 |
| units | 39 | 39 | 0 | 0 | 0 | 8421 / 2219 | 218.6 |
| **all** | **49** | **49** | 0 | 0 | 0 | 11891 / 2580 | **281.0** |

- ~**5.7 s per call** on CPU for a 0.6 B model; wall clock ≈ 4.7 min for the
  whole repo's flows + units — the "micro + tiny context" payoff.
- **Hardware (worst case, on purpose):** this run used a deliberately weak
  machine — AMD Ryzen 5 1400 (4 cores, 2017), 8 GB RAM, ATI Radeon HD 5400
  (no usable compute support, so Ollama ran **CPU-only**). Latency will shrink
  dramatically on a normal setup with any modern GPU or a faster CPU. Because
  the model is only ~0.6 B params, running it locally is not hard: Ollama
  performs well even on modest machines; speed varies with the user's PC
  configuration.
- Confidence honored: model answers at 1.0 are **capped to 0.5**; where the
  model is genuinely uncertain it says so (`Section → unknown`, conf 0.0).
- Labels: mostly short and English; some inputs leak the corpus's native
  language ("Busca e devolve resultados…"), which is honest hypothesis output —
  ≥ word-cap enforcement still passes (≤ 6 words).
- **Provider quirk found empirically:** qwen3 in Ollama's `/api/chat` spends a
  long *thinking* chain first (with `format: json` + temperature 0 the content
  field came back **empty** because `num_predict` was exhausted by thinking).
  Fix: top-level `"think": False` in the payload → content returned, ~2–3×
  faster per call. Recorded as an implementation note in ADR-008.
- NFR-4 note: the *deterministic pipeline* (build → enrich → projections) is
  bit-reproducible; the live LLM stage uses temperature 0 (near-deterministic)
  but byte-exact reproducibility across runs is not guaranteed — it is optional
  and its outputs are hypotheses capped at 0.5 by design.

## 6. Experiment seed (roadmap Phase 9 — "ask the agent" baseline)

The controlled flag experiment Source-only vs Source+SSRL vs raw agent Q&A is a
*human-graded* study; the lab seeds it deterministically:

`lab/p9_experiment_seed.jsonl` — 6 questions × two contexts:

| id | question | baseline context | ssrl context |
| --- | --- | --- | --- |
| q1 | who calls init_db | raw unit names, no structure | callers-of evidence rows (facts) |
| q2 | where is save | raw unit names | node + file:line evidence |
| q3 | which modules import db | raw unit names | per-module IMPORTS profiles |
| q4 | list the entry points | raw unit names | `index.entry_points()` |
| q5 | what does the flow from search do | raw unit names | flow step chains |
| q6 | which files does indexer depend on | raw unit names | transitive IMPORTS closure |

Each row keeps `answer_baseline`, `answer_ssrl`, `graded` for the study run —
the answers the naive agent vs the grounded context produce, then human grading
on time-to-understand and accuracy.

## 7. Verification

- **67 unit tests green** (~0.7 s) — new `TestLLMProposer` (8): mock determinism,
  bundle caps + facts-only, taxonomy rejection, drift/bad-JSON rejection, conf
  clamping, LLM ceiling 0.5 + `SUPPORTS_INTENT` + `origin:"llm"`, offline
  provider ⇒ artifact unchanged, `--scope units` labels modules.
- Determinism re-verified end-to-end on doc_rag (twice, identical).
- `compileall` clean; suite rerun after every edit during the phase.

## 8. Honest limits

- **No live model was exercised** in this environment (offline). The provider
  interface, parsing and gating are verified with the deterministic mock; a
  live `qwen3:0.6b` run needs `ollama serve` + `ollama pull qwen3:0.6b`, then
  `python lab/p9_lab.py --real` (or `ssrl propose <repo>`).
- Proposals are deliberately minimal: label + role + rationale, ≤ 6 words. The
  micro architecture trades expressive reasoning for speed and tiny contexts.
- The experiment *seed* exists; the **study has not been run** — grading is a
  human step (success criterion of roadmap Phase 9).
- Qwen3-0.6B-Instruct is a draft-day reference point; any GGUF/OpenAI-compatible
  endpoint works through the same interface.

## 9. To run

```console
# offline / tests: deterministic mock
python ssrl/cli.py propose ..\..\JG-CODE\doc_rag --mock --scope all
# live: start Ollama, pull the micro model, then
python lab/p9_lab.py --real     # probes, proposes, writes the experiment seed
python ssrl/cli.py propose C:\Users\joaog\Downloads\JG-CODE\doc_rag
```