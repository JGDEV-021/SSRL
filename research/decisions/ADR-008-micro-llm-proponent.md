# ADR-008 — Micro-LLM as Hypothesis Proponent (Qwen3-0.6B Class), Speed-First

- Status: **Accepted** (Phase 9, 2026)
- Decides: `docs/architecture.md` D-5 / RN-4 **implementation**; research plan RQ-3/RQ-4
- Scope decision: *which model*, *where it works*, *what it answers*, *what context is
  passed*, *how it is scored* — requested by the author (micro model, delivery-speed focus).

## Context

RN-4 / ADR-007 order hypothesis sources: structure → naming heuristics → **LLM last, as a
proposer only**. The MVP shipped fully deterministic (zero LLM). Phase 9 now brings the
proposer in — but the author's directive is concrete: use a **micro LLM** (Qwen3-0.6B class),
because "tasks are relatively small and speed of delivery is the focus".

A 0.6B dense model is a *different animal* than the frontier default everyone assumes. This ADR
states exactly what a micro proposer may and may not do, so the rest of SSRL (calibration,
audit, Q&A, narrative, MCP, watch) is untouched.

## 1. Model

- **Target:** `Qwen3-0.6B` (dense, ~0.6B params; instruct variant; 32K sliding context;
  GQA; Qwen3 tokenizer). Served locally via Ollama (`qwen3:0.6b`) or llama.cpp GGUF —
  `<800` MiB, runs on a laptop/CPU or any small GPU.
- **Why:** author directive; tasks are small; local, private, ~zero cost; cold-start and
  per-request latency are one-to-two orders of magnitude below frontier models.
- **Honest limits of a 0.6B model, and our countermeasures:**

  | Limit | Countermeasure |
  | --- | --- |
  | Weak multi-hop/long-horizon reasoning | Tasks are single-unit, closed-taxonomy classification + ≤6-word naming. No chains of thought. |
  | Project-context hallucination (W1 §5.4 class: invented APIs/names) | Context carries **facts only** (symbol ids from the index, not free text); outputs are validated against the real symbol set before acceptance. |
  | JSON/format drift | Temperature 0, provider-side `format=json`, a lenient first-valid-JSON parser, closed taxonomy check; parse failure ⇒ **discard** (deterministic fallback, no hypothesis). |
  | Attention dilution on long prompts | Hard context caps (§4) keep prompts ≈ ≤700 tokens. |
  | Shallow semantics | LLM output is the *last* evidence source, ceiling-capped at 0.5 (existing `SOURCE_CEILING["LLMProposal"]`); structural agreement can raise the final audited conf. |

## 2. Where it works

Exactly one new optional stage, inserted *between fact layer and projections*:

```
facts (AST, deterministic)
  -> semantics.enrich (structure+naming, deterministic, unchanged)
  -> ssrl propose [--llm]   <-- THE ONLY stage that may call the model
  -> confidence calibration -> audit / Q&A / narrative / MCP (unchanged, deterministic)
```

- The default pipeline (`build`, `enrich`, `watch`, `ask`, `narrative`, MCP) is **unchanged**:
  still fully deterministic, no model, no network. `propose` is opt-in per run.
- The model is reachable only through `ssrl/llm.py` (single choke point: timeouts, budgets,
  error handling). No other module imports it.
- It **never**: extracts facts, writes the corpus, writes the cache, or runs inside
  `build`/`enrich`/`watch`. It may be wired into `enrich` later only as an explicit `--llm`
  flag; not in this phase.
- Scope default = **Flows + Modules only** (small N by design; e.g. 1–174 flows, 31–122
  modules on our corpora — not ~900 per-function units). This is the speed decision that
  makes a micro model a viable proponent.

## 3. What it answers

Two closed tasks, nothing else:

- **Task A — flow intent** (`flow_intent`): input = a Flow chain already derived
  structurally (entry function id + ordered step ids). Output = `{label, confidence, rationale}`
  where `label` ≤ 6 words naming the *behavior* (e.g. "session context build"), `confidence`
  ∈ [0,1] is the model's self-report, `rationale` ≤ 1 line.
- **Task B — unit role** (`unit_role`): input = one Module/Class (name, first docstring line,
  external imports ≤ 8, contained functions ≤ 12, caller/callee counts). Output =
  `{role, confidence, rationale}` where `role` ∈ a closed taxonomy passed in the prompt
  (persistence, model, service, config, infra, entrypoint, controller, ui, util, unknown).
- Outputs are **always hypotheses**: materialized as `Intent` nodes (same schema as
  heuristic intents) with `metadata.origin: "llm"`, evidence type `LLMProposal`,
  edge `SUPPORTS_INTENT`. No branch can promote them to facts (RN-4 / FR-3).
- The model **never answers user questions** directly inside the layer. (The Phase 9
  experiment harness may use the same model as a *baseline agent*, but that runs in the lab,
  outside the layer.)

## 4. Context design (what is passed)

"Evidence bundles" — **facts only**, never source bodies, never git history, never the
whole file:

| Bundle | Card (caps) |
| --- | --- |
| `flow_intent` | repo id; flow id; entry symbol id + `rel:line`; up to **24** step ids, each with module + first line of docstring/def. Hard prompt cap ≈ 2600 chars (~≤700 tokens). |
| `unit_role`   | repo id; module/class id + `rel:line`; first 180 chars of docstring; external import names ≤ 8; contained symbol names ≤ 12; caller count, callee names ≤ 8. Hard cap ≈ 2200 chars. |

Why tiny: micro-model quality collapses as prompt length grows; speed scales with token
count; the *point* is that SSRL gives the model **structure, not soup**. Symbols are real
ids from the index — the model cannot invent names because the validator rejects anything
not present in the artifact.

## 5. Serving: zero-dep, local, budgeted

Provider interface in `ssrl/llm.py` (stdlib only, ADR-002):

- `OllamaProvider` — `GET /api/tags` (reachability probe), `POST /api/chat`
  (`stream=false`, `format: json`, `options.temperature: 0.0`, small `num_predict`).
  Uses Ollama's returned `prompt_eval_count`/`eval_count`/`total_duration` for token
  and latency accounting.
- `OpenAICompatProvider` — `POST /v1/chat/completions` (llama.cpp server / vLLM / LM Studio).
- `MockProvider` — deterministic, canned responses; the only provider used by unit tests
  and offline runs (no network).
- Budgets: per-request timeout (default 30 s); zero retries; any error ⇒ `None` ⇒ **no
  hypothesis** (silent, labeled degrade, not a crash). Batch = sequential single units.
- **Implementation note (empirical, qwen3 via Ollama):** with `format: json` +
  `temperature: 0`, the model emits a long *thinking* chain first and, when
  `num_predict` is small, `content` comes back **empty** (budget exhausted by
  thinking, `done_reason: length`). Recorded fix: send top-level `"think": False`
  in the `/api/chat` body — content is returned directly and calls are ~2–3×
  faster (measured on doc_rag: ~5.7 s/call, 49 calls in 281 s wall).

## 6. Re-scoring: the model proposes, structure disposes

Every accepted proposal becomes one Intent node with evidence
`{"type": "LLMProposal", "source": <symbol id>, "weight": min(raw_conf, 0.5)}`.
`confidence.calibrate` then produces the audited confidence — honoring the existing
`LLMProposal` ceiling (0.5), which is deliberate: **an LLM claim alone can never read
"strong"**. If the deterministic heuristic already produced the same label, the proposal is
**skipped** (counted as "covered") — deterministic evidence is never overwritten. The
rationale is stored in `metadata.rationale` and surfaced by `why`/`audit`.

Determinism contract: everything below `propose` is deterministic **given a fixed hypothesis
set**; the only stochastic input is the model itself, isolated to one stage.

## 7. Consequences

- **Positive:** default pipeline stays deterministic and dependency-free; hypotheses remain
  audited second-class claims; micro model keeps latency/cost near zero; same provider
  interface allows a frontier swap later without touching the rest.
- **Negative / risk:** 0.6B label quality is the ceiling on proposal richness — accepted, per
  the author's speed-first directive; validation + caps bound the damage.
- Phase 9's experiment harness can now compare, on identical hardware, *Source-only* vs
  *Source+SSRL* vs *micro-agent baseline* — the "ask the agent" threat (§paper) becomes
  measurable instead of assumed.

## Alternatives considered

- **Frontier model via API:** rejected by the author (speed/local focus) and by ADR-002.
- **No LLM (status quo):** keeps the shallow-semantics ceiling ADR-007 flagged as the known
  risk; `propose` is additive, so this remains the always-available fallback.
- **LLM labeling every function:** rejected for speed — per-function round-trips (hundreds)
  defeat the micro-model point; default scope is flows + modules §2.