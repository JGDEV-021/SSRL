# REPORT-P9 — Phase 9: Micro-LLM Proposer & Experimental-Validation Groundwork

**Version:** v0.7.0 · **Date:** 2026 · **Status:** complete — including the
draft automated study pass (§6.1), the refusal probe battery (§6.2), and the
resulting context-system improvement; human grading is the remaining Phase 10/study step
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
| Study (draft automated pass) | `lab/p9_study.py` → `lab/p9_study_results.{json,md}`, `lab/p9_study_graded.jsonl` |
| Refusal probe battery (§6.2) | `lab/p9_probe.py` → `lab/p9_probe_results.{json,md}` |
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
| q2 | where is embed | raw unit names | node + file:line evidence |
| q3 | which modules import db | raw unit names | per-module IMPORTS profiles |
| q4 | list the entry points | raw unit names | `index.entry_points()` |
| q5 | what does the flow from search do | raw unit names | flow step chains |
| q6 | which files does indexer depend on | raw unit names | transitive IMPORTS closure |

Each row keeps `answer_baseline`, `answer_ssrl`, `graded` for the study run —
the answers the naive agent vs the grounded context produce, then human grading
on time-to-understand and accuracy. The seed is deterministic and regenerated
from `SEED_QUESTIONS` in `lab/p9_lab.py` (q2 uses `embed`, a symbol that exists
in the corpus — the seed's first `save` was dropped because no such symbol
exists in doc_rag).

## 6.1 Study — draft automated pass (executed, `lab/p9_study.py`)

An automated proxy of the flag experiment above (Source-only vs Source+SSRL vs
raw agent Q&A) ran live against `qwen3:0.6b` (Ollama, temp 0): 6 questions x 3
conditions, entity-level recall/precision/F1 vs a **deterministic gold standard
computed from the layer itself** (callers-of, locations, importers, entry
points, flow steps, deps closure). Gold is derived from facts only — sharpening
the measure against "the source file-positions may not match". The third
condition — `layer` — is the deterministic `ask` projection (no LLM), included
as the oracle/celling reference.

Aggregates (n=6, full detail in `lab/p9_study_results.md`). Numbers below are
the run **after** the context-system improvement found by the probe battery
(§6.2): the agent system prompt became a deterministic-CLI contract ("extract
and reproduce verbatim, one per line, do not refuse") and the importer evidence
was noise-filtered (only rows that import the asked module). The pre-improvement
run scored ssrl 0.338 / baseline 0.022.

| condition | F1 mean | recall mean | tokens prompt | tokens eval | elapsed_s |
| --- | --- | --- | --- | --- | --- |
| baseline (raw names + LLM) | 0.153 | 0.330 | 5344 | 3000 | 253.3 |
| ssrl (grounded facts + LLM) | 0.613 | 1.000 | 2631 | 949 | 65.8 |
| layer (deterministic `ask`) | 0.315 | 0.303 | — | — | 0.0 |

Per-question highlights (answers in `lab/p9_study_results.md`):

- **ssrl recall is 1.0 on all six questions** — with the CLI contract the 0.6 B
  extracts *every* gold entity instead of refusing. The gap to F1 is precision:
  it reproduces extra identifiers verbatim from the evidence (q2 lists both
  `embed` sites, q3/q6 list modules that import/neighbor `db`/`indexer`), so
  F1 lands at 0.40–0.84 rather than ceiling.
- **q1 callers → 0.82, q4 entry points → 0.84** (both were ~0 at the first
  prompt wording; q1 fluctuated with wording — see §6.2 on fragility).
- **q3 importers → 0.50** (recall 1.0; importer evidence now 4 rows, not 30).
  The answer-framed renderer gets q3 to **1.00** — but that collapses the task
  to transcription (§6.2 caveat), so the JSON rendering is the honest measure.
- **baseline still fails** the structured questions (q3/q6 = 0.0); the name-soup
  context floods the model even at the CLI contract. Its 0.153 mean is mostly
  q2 landing on `embedder` by chance in this run (temp-0 is not deterministic).
- **Layer oracle:** 0.93 (q1) / 0.65 (q4) but ~0 on q2/q3/q5 — the deterministic
  `ask` projection narrates module intros it was not designed to answer, so its
  mean (0.315) is bounded by *which questions are asked*, not by ground truth.

Read as pilot findings, not a verdict: (1) **context grounding + a strictly
extractive prompt contract are what make a micro LLM answerable** on enumeration
questions — refusals were a prompt artifact, not a capability wall (§6.2);
(2) the 0.6 B is format-fragile and temp-0 is not byte-reproducible — prompt
wording and run-to-run output shift F1 by ±0.3; (3) the deterministic layer
remains the reliable oracle for the questions it projects, which is exactly why
the architecture keeps the LLM on closed tasks (ADR-008). The draft itself is
the *routine* single-model pass; it is **not** the graded study.

### Definitive study plan (roadmap Phase 9, success criterion)

1. **Participants/human grading:** the seed experiment (6 questions x Source-only
   vs Source+SSRL, plus raw-agent and layer-`ask` arms) graded by ≥ 3 people on
   time-to-understand and accuracy — the numbers above are an automated proxy
   for accuracy only.
2. **Models:** keep `qwen3:0.6b` (micro) and add a mid-size class (e.g. 7B) to
   separate *model-capability* from *context* effects on the same seed.
3. **Constrained outputs:** repeat the flag with closed-form answer tasks (≤ 6
   words / taxonomy role, ADR-008 tasks) — where the micro model is designed to
   work — instead of open extraction only, matching the production use of the
   proposer.
4. **Artifacts:** per-run `lab/p9_study_results.md` + `p9_study_graded.jsonl`;
   aggregated anonymized table in this report; reproducibility notes (temp 0,
   `think: false`, budgets).

Run (live, needs `ollama serve` + the model pulled):

```console
python lab/p9_study.py --out=p9_study      # baseline + ssrl (LLM) + layer (deterministic)
```

## 6.2 Refusal probe battery — why does the 0.6 B refuse, and what stops it?

Because the first study run was dominated by refusals ("insufficient context"),
a targeted A/B battery (`lab/p9_probe.py`) isolated the causal factors on the
same golds. Design: 6 questions x 5–10 variants, temp 0, `think` off unless the
variant turns it on, each answer classified as `reject` / `empty` / `answer` and
scored (entity F1 vs the facts gold). Outputs `lab/p9_probe_results.{json,md}`.

Variant axes:

| Axis | Levels |
| --- | --- |
| evidence rendering | `json` (raw evidence rows) · `answer` (answer-framed assertions) |
| prompt contract | `lookup` (refusal-bust "extract the answer") · `cli` (deterministic tool: "reproduce verbatim, one per line, do not refuse") · `fewshot` (CLI tone + 3 in-context Q→A examples) |
| thinking | `think=False` vs `think=True` |

Findings:

1. **Refusals are a prompt-contract artifact, not a capability limit.** All six
   `lookup`/`think` slots rejected q5; battery 2 (30/30 calls, the
   `cli`/`fewshot` family) answered **every** question. Switching the agent from
   "extract the answer to the question" to "authoritative deterministic tool,
   reproduce the identifiers verbatim, one per line, do not refuse" removed
   100% of refusals. `think=True` added nothing.
2. **Best overall: `json_cli`** (F1 mean **0.61**, top on 4/6 questions, never
   collapses). Answer-framed renders beat it only when the task becomes pure
   transcription. Few-shot adds variance: it excels on q6 (0.92) and q5 (0.71)
   yet collapses to echoing the example/entity on q1/q2/q3 (0.00).
3. **Answer-framed assertions collapse the task to transcription.** When the
   context states the answer as prose ("The modules that import module::db are:
   indexer, quality, retriever, scripts") the model transcribes it perfectly
   (q3 = **1.00**, q5 = 0.71–0.62) — but that measures copying fidelity, not
   question-answering, so the study keeps JSON evidence as the honest task and
   records answer-framed numbers as the read-off ceiling. (A renderer mutation
   bug initially made the answer variants render the raw rows; fixed — see
   4.)
4. **Evidence size is the residual killer.** q3's importer evidence (30 rows,
   mostly empty `imports`) floods the model → verbatim dumps/loops → F1 ~0.
   Filtering to rows that import the asked entity (4 rows) fixed the flood and
   is what the study now uses. Large-but-flat evidence (q4 entry points, 29
   items) survives because it is a homogeneous list.
5. **temp 0 is not deterministic for this model.** Same variant+question across
   batteries scored 0.71 then 0.35 (q5 json_fewshot) and cli_fewshot collapsed
   to echo on q3/q6 in one battery. Judgments use variant *means*, and the
   definitive study (§6.1) repeats with human grading.

Variant F1 means (battery 2, 6 questions, fixed renderer):
`answer_fewshot` 0.68 · `answer_cli` 0.65 · `json_cli` 0.61 · `cli_fewshot`
0.50 · `json_fewshot` 0.43.

**Result of the battery → the decision to improve the context system first:**
the refusals were removable with a one-line prompt contract and a noise filter,
and the study re-run (§6.1) moved ssrl 0.338 → 0.613 at free lower token cost
(2631 vs 3173 prompt tokens) and faster wall time (65.8 s vs 56–66 s baseline).

## 7. Verification

- **67 unit tests green** (~0.7 s) — new `TestLLMProposer` (8): mock determinism,
  bundle caps + facts-only, taxonomy rejection, drift/bad-JSON rejection, conf
  clamping, LLM ceiling 0.5 + `SUPPORTS_INTENT` + `origin:"llm"`, offline
  provider ⇒ artifact unchanged, `--scope units` labels modules.
- Determinism re-verified end-to-end on doc_rag (twice, identical).
- `compileall` clean; suite rerun after every edit during the phase.

## 8. Honest limits

- **Draft study is a pilot, not the graded verdict.** §6.1 shows a single
  model, single corpus, automated accuracy proxy. The human-graded multi-arm
  study (definitive plan in §6.1) is the roadmap success criterion and is
  still to be executed.
- **Refusals were a prompt artifact, now removed (§6.2).** The old "extract and
  answer" phrasing made the 0.6 B bail or echo even on grounded evidence; the
  CLI contract + noise-filtered importer evidence lifted ssrl F1 0.338 → 0.613.
  This does not make the model *reason* — with answer-framed contexts it merely
  transcribes, so §6.1 uses JSON evidence as the honest measure.
- **Temp 0 is not byte-reproducible on this model.** Run-to-run F1 moved ±0.3
  for identical variant+question (§6.2 #5); single-run numbers are indicative.
- **Micro-model frugality** is confirmed: the 0.6 B extracts well when the
  context is small, grounded and the contract forces verbatim lists; open-form
  reasoning and large evidence still degrade it (q4 shows a 29-item flat list
  is fine, q3's 30-row flood was not). This motivates the architecture and the
  definitive study's constrained-output arm.
- **`ask` gaps:** the deterministic layer narrates module intros for questions
  it does not project (q2/q3/q5), so the oracle mean (~0.3) is itself bounded by
  *which* questions are asked, not by ground truth.
- Proposals are deliberately minimal: label + role + rationale, ≤ 6 words. The
  micro architecture trades expressive reasoning for speed and tiny contexts.
- Qwen3-0.6B-Instruct is the reference model; any GGUF/OpenAI-compatible
  endpoint works through the same interface (llm.py providers).

## 9. To run

```console
# offline / tests: deterministic mock
python ssrl/cli.py propose ..\..\JG-CODE\doc_rag --mock --scope all
# live: start Ollama, pull the micro model, then
python lab/p9_lab.py --real     # probes, proposes, writes the experiment seed
python ssrl/cli.py propose C:\Users\joaog\Downloads\JG-CODE\doc_rag
# study (draft automated pass): live, 6 questions x 3 conditions
python lab/p9_study.py --out=p9_study
```