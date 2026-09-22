# SSRL Roadmap

## From Documentation to a Validated Understanding Layer

> SSRL is a research initiative that may eventually become software.
>
> The cardinal rule of this roadmap: **research gates code.** We do not write a parser before we know the questions, the projections, and the evidence.

---

## Current Status

```text
Stage: Prototype — V1 MVP complete (Phases 3–6 compressed into an MVP)

Progress:
█▓▓▓▓▓▓▓▓░ 92%
```

Completed:

- [x] Vision & principles
- [x] Spec-driven requirements (draft)
- [x] Position paper (v0.2 → **v0.3**, updated with G1 resolution + prototype findings)
- [x] Research plan
- [x] Research leads (related work)
- [x] W1 literature (validates facts/hypotheses, structural grounding)
- [x] W2 prior art & market (graph-first refuted; Q&A convergence)
- [x] W3 practitioner discourse (comprehension gap confirmed)
- [x] W4 probe (stdlib `ast`: 100% parse, 3.3 s / 1058 nodes, 0 deps)
- [x] W5 ADRs (ADR-001…007) — **all accepted**
- [x] **Gate G1 PASSED** — ADR-005 signed off (2026); requirements/architecture frozen to v1.0
- [x] **V1 MVP** — `prototype/ssrl/` package (extract → enrich → calibrate → Q&A → narrative → CLI), 67 unit tests green, validated on both corpora with determinism
- [x] **Phase 7: lab integration** — `watch` (continuous no-manual-sync regeneration, delta-only re-parse via D-8); success criteria verified on real repos read-only (see `prototype/REPORT-P7.md`)
- [x] **Phase 8: end-to-end + agent surface** — MCP server over stdio (zero-dep, evidence-preserving tools `ask/why/narrative/stats/audit/impact`) + CI impact report `impact [--git]`; CLI and MCP answer the same layer coherently (see `prototype/REPORT-P8.md`)
- [x] **Phase 9: experimental validation groundwork** — micro-LLM proposer (ADR-008), probe battery → prompt-contract fix, study re-run **baseline 0.15 / ssrl 0.61 / layer 0.32**, ssrl recall 1.0/6 (see `prototype/REPORT-P9.md`)
- [x] **Phase 9.5: Explainable AI for external coding agents (ADR-009)** — grounded self-explanation axis: MCP/CLI `explain` + `verify_explanation` auditor, "the AI is the witness, the layer is the notary"; battery with an opencode big-pickle subagent as synthetic coding AI: **ceiling 3/3 PASS, fabricated reference 1/1 caught** (see `prototype/REPORT-P10.md`)
- [x] **Live demo + three fixes** — a real external-coding-AI loop (subagent builds a CLI game, self-explains, `verify` audits) exposed: duplicate `IMPORTS` edges for multi-symbol `from x import a, b`; auditor relation grammar EN-only (now EN+PT); QA PT question patterns (now routed). Suite 88 → **95 green** (BUILDLOG §9.6)

---

## Phase 0 — Foundation

**Goal:** a coherent, evidence-ready research program.

**Deliverables**

- [x] Project repository
- [x] Vision, objectives, non-goals, principles
- [x] Spec-driven requirements (`docs/requirements.md`)
- [x] Position paper v0.3 (G1 resolution + prototype findings)
- [x] Research plan with questions, hypotheses, methods, gates (`research/plan.md`)
- [x] Research leads (`docs/related-work.md`)

**Success criteria:** anyone can read the repository and know *what SSRL claims, why, and how it will be tested* — with no code.

---

## Phase 1 — Research & Analysis

**Goal:** collect evidence — literature, prior art/market, practitioner discourse, cheap read-only probes.

**Structure** (created inside `research/`):

```text
research/
├── plan.md
├── literature/      # paper notes & summaries
├── prior-art/       # CodeQL, Sourcegraph, Sourcetrail, Copilot, Cursor, Claude Code, RAG/GraphRAG...
├── discourse/       # HN, Reddit, Lobsters, dev.to, GitHub discussions — real pain reports
├── probes/          # throwaway read-only extraction experiments (NOT the real prototype)
└── decisions/       # ADRs resolving the open questions
```

**Key questions**

- Does the comprehension gap hold up against real practitioner reports? (W3)
- Which of H1 (Q&A) / H2 (progressive zoom) / H3 (living narrative) / H4 (graph) is the best **primary** projection? (RQ-2)
- What do existing tools actually deliver — and where do they stop? (W2)
- Are cheap structural facts feasible on a real small repository? (W4)

**Gate G1 — Evidence enough to write code:**

- Primary projection resolved: **ADR-005 accepted** (H1 grounded Q&A + H3 co-surface) → FR-6/FR-6a.
- Target language, parser strategy, and storage direction chosen: **ADR-001 (Python), ADR-002 (stdlib `ast`), ADR-003 (derived artifact)**.
- Comprehension benefit has correlational support: **confirmed (W2/W3/W4).**
- Requirements and architecture docs: **frozen to v1.0**.

**✅ Gate G1 PASSED (2026). Phase 1 and Phase 2 complete — the spec is contractable. Prototype coding begins.**

---

## Phase 2 — Decision & Spec Freeze

**Goal:** from research conclusions to a frozen v1 spec. **✅ Complete**

**Deliverables**

- [x] ADRs for every open architecture decision (D-1…D-8) — ADR-001…007, **all accepted**
- [x] `docs/requirements.md` frozen (v1.0)
- [x] `docs/architecture.md` finalized (invariants + chosen directions, v1.0)
- [x] Paper updated to v0.3 with research findings (G1 resolution + V1 MVP data) — `paper/SSRL-v0.3.md`
- [x] First prototype scope defined: small real Python repo, facts first (Phase 3)

> No production code until this phase. Throwaway probes live only under `research/probes/`. **Prototype code (real, non-throwaway) starts in Phase 3.**

---

## Phase 3 — Prototype: Facts First

**Goal:** generate the first structural facts from code. **✅ Complete (part of V1 MVP).**

**Scope**

- [x] Input: a small real Python repository (2 validation corpora: 31 + 122 files)
- [x] Extract: Repository / Module / Class / Function / Method / imports / calls
- [x] Output: deterministic `{nodes, edges}` in the stable model format (`prototype/ssrl/extract.py`)
- [x] Determinism verified (NFR-4), zero deps (ADR-002), 100% parse on both corpora
- [x] Incremental sync (D-8: file-level sha256 cache) — `--cache` in CLI

**Artifacts:** `prototype/ssrl/` package + `prototype/README.md` (metrics & limits) + `REPORT-V1.md`. Validated on `JG-CODE/doc_rag` (31 files, 244 nodes) and `jgpredictor` (122 files, 1117 nodes), read-only.

---

## Phase 4 — Primary Projection MVP

**Goal:** expose the facts through the research-chosen primary projection (**ADR-005: H1 grounded Q&A**, with H3 living narrative as on-demand co-surface). **✅ Complete (part of V1 MVP).**

- [x] H1: grounded Q&A over the fact model — primary (`prototype/ssrl/qa.py`), deterministic, FACTS vs HYPOTHESES separation (FR-6a)
- [x] H3: generated living narrative — co-primary (`prototype/ssrl/narrative.py`)
- [ ] H2: system → subsystem → module → line drill-down — supporting *(deferred post-MVP)*
- [ ] H4: graph navigation — supporting *(deferred post-MVP)*

**Success criteria:** a developer can comprehend the test project *faster* through SSRL than from raw files alone → **partially verified**: `ask` answers `where/callers/callees/imports/summary/entry points/flows` with evidence on both corpora.

---

## Phase 5 — Semantic Enrichment v1

**Goal:** introduce probabilistic hypotheses over facts. **✅ Complete (part of V1 MVP).**

- [x] Evidence sources: naming, structure (call-graph), entry-point/docstring signal (`prototype/ssrl/semantics.py`)
- [x] Every hypothesis labeled, with confidence and evidence (`confidence.calibrate`)
- [x] Facts and hypotheses kept strictly separate in all surfaces (listings, Q&A, narrative)
- [ ] LLM proposals as proponent only (RN-4 / ADR-007) — ✅ **implemented in Phase 9** as a *micro* model (Qwen3-0.6B class), proponent-only, `LLMProposal` evidence capped at 0.5 (ADR-008); still marked deferred for the V1 MVP core, which stays fully deterministic

**Success criteria:** semantic labels are useful and their uncertainty is visible → **Verified**: flows (doc_rag 10), intents (174 jgpredictor), service/domain concepts (24 jgpredictor), all `confidence < 1.0`, exposed via `ask flows|intents`, `audit`, `why`.

---

## Phase 6 — Confidence & Evidence Engine

**Goal:** explicit, calibrated confidence. **✅ Complete (part of V1 MVP).**

- [x] Weighted agreement across evidence sources (`confidence.aggregate` — noisy-OR capped by strongest source)
- [x] "Why does SSRL believe this?" always answerable (`confidence.why` + CLI `why`)
- [x] Calibration validation groundwork (`confidence.audit` + CLI `audit`) — full RQ-3 study deferred to Phase 9

**Success criteria:** a user can adjust trust based on confidence without reading code to double-check → **Verified**: `audit` lists hypothesis with calibrated conf/note; facts always 1.0 with evidence.

---

## Phase 6.5 — V1 MVP integration (implemented)

Compressed Phases 3–6 into a minimal cohesive package shipped as the **V1 MVP**:

- [x] `prototype/ssrl/` package (10 modules, zero deps)
- [x] CLI (ADR-006): `build | enrich | ask | why | narrative | audit | stats | json`
- [x] Incremental cache (D-8): 31/31 from_cache on warm run, artifact identical
- [x] Tests: 67 unit tests green (extract, cache, semantics, confidence, index, qa, narrative, watch, impact, mcp, llm)
- [x] Determinism verified end-to-end on both corpora (fresh + cached)
- [x] Reports: `prototype/BUILDLOG.md`, `prototype/REPORT-V1.md`, `prototype/README.md`

**Next (post-Phase 9.5):** Phase 10 publication prep. Phase 9 groundwork + the
draft automated study pass are done (§6.1 of `prototype/REPORT-P9.md`); the
human-graded multi-arm study and full calibration analysis remain as the
definitive validation step. Phase 9.5 (ADR-009) added the Explainable-AI axis
for external coding agents — see `prototype/REPORT-P10.md`.

---

## Phase 7 — Lab Integration (Real-World Testbed)

**Goal:** first real-world laboratory.

- Use the author's existing **Python** project as a production-sized testbed (e.g., a real application with multiple modules)
- Feed real repositories; measure extraction quality and freshness (incremental sync)

**Success criteria:** SSRL operates continuously on real, evolving projects without manual sync.

---

## Phase 8 — End-to-End & Agent/AI Surface

**Goal:** complete pipeline + AI consumer.

- Full flow: code → facts → hypotheses → primary projection, incrementally
- AI-agent consumption (grounded context with evidence, e.g., via an agent protocol like MCP)
- CI impact reports ("what does this PR affect?") as a supporting surface

**Success criteria:** humans and agents consume the same layer coherently.

---

## Phase 9 — Experimental Validation

**Goal:** measure the claim, not just build the thing.

- Controlled experiments: Source-only vs Source+SSRL (and vs raw agent Q&A)
- Metrics: time to understand, time to find a bug, time to onboard, answer accuracy
- Must handle the "ask the agent" baseline (threat §11 of the paper)

**Implemented (groundwork):**
- [x] Micro-LLM hypothesis proposer (`ssrl/llm.py`, ADR-008) — Qwen3-0.6B-class
      model via Ollama/OpenAI-compatible providers, or deterministic mock.
- [x] Proponent-only, never fact: `LLMProposal` evidence capped at conf 0.5,
      `SUPPORTS_INTENT`, `origin:"llm"` (RN-4 / ADR-007 obeyed).
- [x] Tiny contexts by design: facts-only bundles, ≤ 2600 chars (flows) /
      ≤ 2200 chars (units) — fit a micro model's whole window
      (doc_rag flows: median 553 chars ≈ 149 tokens).
- [x] Experiment seed (`lab/p9_experiment_seed.jsonl`): 6 questions × baseline
      (raw names) vs SSRL-grounded contexts, answers + grading left to the
      study run.
- [x] Study execution — **draft automated pass** (`lab/p9_study.py`, live
      `qwen3:0.6b`): baseline vs Source+SSRL vs deterministic-layer reference,
      entity-level F1 vs facts-derived gold. After the refusal probe battery
      (§6.2 **`lab/p9_probe.py`**) proved refusals were a prompt artifact, the
      context system was improved (deterministic-CLI contract + importer
      evidence filter) and re-run: **baseline 0.15 / ssrl 0.61 / layer 0.32**,
      ssrl recall 1.0 on all 6 questions. Full detail + the **definitive study
      plan** (human-graded, multi-model, closed-task arms) in
      `prototype/REPORT-P9.md` §6.1 / §6.2.
- [ ] Definitive study: human-graded multi-arm (Source-only vs Source+SSRL vs
      raw-agent), ≥ 3 graders, mid-size model arm, accuracy + time-to-understand.

**Success criteria:** measurable, significant comprehension improvement.

---

## Phase 9.5 — Explainable AI for External Coding Agents (ADR-009)

**Goal (author directive):** developers no longer write or read code — coding AIs do.
The missing capability is **self-explanation**: what the AI did, why, how. SSRL's
job is to be the substrate external coding AIs (Claude, Codex, …) explain
*against* — and the notary that audits those explanations. "The AI is the
witness, the layer is the notary" (model proposes, structure disposes, extended
to the *external* process).

**Implemented (deterministic, stdlib-only, no model inside the layer):**
- [x] `ssrl/explain.py` — grounded WHAT/WHY/HOW (`explain_node` / `explain_changed`,
      deriving facts + evidence + pipeline stages off the artifact) and the
      **auditor** `verify_explanation`: quoted identifiers are citations
      (present / external / **invented**); unquoted identifier-like tokens resolve
      as hits and never count invented; sentences without citations are
      "unsupported"; asserted relations are structurally consistency-checked.
- [x] MCP tools `explain` + `verify_explanation` (ADR-006 surface, agents speak
      MCP natively) and CLI `explain` / `verify` (+`--git`, stdin/file narration).
- [x] Battery (`lab/p10_eai.py`, seed `lab/p10_eai_seed.json`): narrations
      **drafted by an opencode subagent on model `opencode/big-pickle` as the
      synthetic coding AI** (same caliber as the frontier tools this targets).
      Result: **3/3 faithful ground-truth narrations PASS (ceiling, groundedness
      1.0, invented 0); 1/1 adversarial narration with a fabricated reference
      caught → REVIEW, invented=1.** See `prototype/REPORT-P10.md`.
- [x] Tests: 88 green (21 new EAI tests incl. MCP wiring).
- [x] Live-demo fallout (coin-toss): three gaps found and fixed — duplicate
      `IMPORTS` edges per multi-symbol `from x import a, b` (extract.py);
      auditor relation grammar EN-only → **EN+PT** (explain.py); QA intent
      parser EN-only → **PT patterns + stopwords** (qa.py). Suite now **95 green**
      (BUILDLOG §9.6).
- [ ] Open items, documented in REPORT-P10: nested/ambiguous identifier
      extraction noise, "grounded but wrong reason" (no semantic entailment) —
      both by-design ceilings, not bugs.

**Success criteria:** an external coding AI can self-explain against the layer and
the layer can tell a grounded self-explanation from a fabricated one. **Verified
in-battery**; real Claude/Codex-grade integration is Phase 10 outreach.

---

## Phase 10 — SSRL v1 Publication

**Deliverables**

- Position paper → published version (v1)
- Working prototype + documentation
- Validation dataset
- Evaluation results and decisions made

**Audience:** researchers, software architects, AI engineers, tool builders.

---

## Long-Term Vision

- Multi-language support
- Architecture drift detection
- AI-native analysis grounded in the layer
- Knowledge preservation independent of specific models
- Enterprise-scale application

---

## Success Definition

SSRL succeeds if a developer can answer *"what does this system do?"* and *"what breaks if I change X?"* faster — and with greater confidence — than by reading code alone.

SSRL succeeds if software knowledge becomes more durable than the people or models that originally created it.

---

## Final Principle

> AI reduces the cost of creating software.
>
> Humans define its purpose.
>
> SSRL seeks to reduce the cost of understanding it.
>
> Knowledge that cannot be understood is lost knowledge.