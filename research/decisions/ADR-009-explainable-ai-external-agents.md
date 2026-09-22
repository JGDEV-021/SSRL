# ADR-009 — Explainable AI for External Coding Agents: Grounded Self-Explanation + Explanation Auditor

- Status: **Accepted** (2026) — ratified by the author ("implemente") and fully implemented as
  roadmap Phase 9.5: `ssrl/explain.py`, MCP `explain`/`verify_explanation`, CLI `explain`/`verify`,
  95 tests green (live-demo fallout fixed EN→EN+PT relation grammar + PT QA routing),
  battery executed (`lab/p10_eai.py`) with an opencode subagent on
  `opencode/big-pickle` as the synthetic coding AI. See `prototype/REPORT-P10.md`.
- Decides: how SSRL serves **external coding AIs** (Claude, Codex, Copilot, Cline, …) with
  a grounded **self-explanation** surface + an **explanation auditor**; extends ADR-006 (D-7:
  MCP agent surface) and the Phase 9 "model proposes, structure disposes" rule to the
  *external* process.
- Scope decision: *where the external AI plugs in*, *what the self-explanation contract is*,
  *who produces the WHAT vs WHY/HOW*, *what the auditor verifies*, *how it is scored* —
  requested by the author (external coding AIs are the target; SSRL's own micro-LLM is out
  of scope).

## Context

Author's strategic directive: developers no longer write code (coding AIs do) and increasingly
no longer read it either. What is missing is **"Explainable AI"** — the capacity of a coding AI
to **self-explain**: *what it did, why it did it, how it did it that way*. And that capacity is
the "pulo do gato" that lets the transition go *from Python/JavaScript to whatever the AI
produces next*. Clarified: this is about **external coding AIs (Claude, Codex, …) and the
external process** — not about the micro model inside SSRL (ADR-008).

The problem is that an external AI's self-explanation is produced from *its own memory of the
codebase*. That memory is exactly where Phase 9 probes found the failure modes: unsupported
assertions, prompt-artifact refusals, and "answers" that are transcription rather than grounded
statements. So an explanation is only as good as the ground it cites.

SSRL's differentiator becomes concrete: the layer is the **notary** to the external AI's
**witness**. The AI explains in natural language; SSRL provides the structural *WHAT* (what
changed, what it touches) and verifies the WHY/HOW narrative against facts — so the AI's
self-explanation is audited, citing **real symbols and relations from the artifact**, not
memory. The contract is language-independent (ADR-009 sees through any generator's output),
even though current derivations are Python-only (ADR-001).

## 1. What this ADR is NOT about (scope carve-outs)

- Not the rationale of SSRL's internal micro-LLM proposals (ADR-008 stays as is).
- Not a code generator, not a diff summarizer by itself (the structural WHAT uses the existing
  `impact` projection as the spine).
- Not NLP semantics: SSRL does **not** judge whether an explanation sentence is true in
  meaning. It verifies **grounding** (cited identifiers/relations exist) and **consistency**
  (cited structural facts match the artifact). Semantic entailment is explicitly out of scope.
- The auditor does **not call any model** and does **not require the coding AI** to be SSRL-aware
  to be useful (it audits free-text explanations + a change list).

## 2. The self-explanation pipeline (the external process)

```
coding AI edits repo            (Claude / Codex / Cline / Copilot …)
   -> ssrl watch / impact       (expected: build artifact on HEAD)
   -> SSRL WHAT                 (deterministic: units/relations changed + impact bundle)
      the AI (or dev) Writes WHY/HOW  (natural-language narration; free text)
   -> SSRL audit                (deterministic: verify_explanation)
   -> grounded report           (what = structure, why/how = claimed + verified, verdict)
```

- The **WHAT** is never the AI's word: it comes from `impact_changed` (structural change-scope)
  and the index — facts only.
- The **WHY/HOW** is the AI's own narration; SSRL accepts it as a *claim* and audits it.
- The loop works whether the narration is hand-written, pasted, or produced by the coding AI
  itself after calling SSRL's `explain` tool for grounding.

## 3. The self-explanation contract

Every audited explanation is a triple, addressable per cited fact:

| Slot | Meaning | Producer |
| --- | --- | --- |
| `what`  | what changed / what a node is, in structural terms | SSRL (facts + impact) |
| `why`   | evidence + confidence + rationale for the claim | SSRL evidence trail (reuses `why`/`audit`) **+ AI narration claims** |
| `how`   | the derivation trail that produced the facts | SSRL pipeline lineage (build → enrich → propose → projections) |

Extensions to the author's framing: "what it did" = structural change-scope; "why it did it"
= the AI's rationale *verified*; "how it did it that way" = either the AI's method narration
or SSRL's derivation trail. SSRL never claims authority over WHY/HOW semantics — it claims
authority over **grounding**.

## 4. New surfaces (design for v0.8, same discipline as ADR-006)

Two MCP tools + two CLI verbs, all **stdlib-only, deterministic, no network**:

1. `explain` — deterministic grounded WHAT/WHY/HOW for one artifact node **or** a change set
   (`files`):
   - node mode: reuse `index` + `confidence.why` + derivation trail → `{what, why, how}` with
     citations (symbol ids, `rel:line`).
   - change mode: `impact_changed(files)` → structered bundle: what changed, entry points
     touched, reverse-dependency blast radius, per-unit evidence.
2. `verify_explanation` — the auditor:
   - input: `files` (change list) + `narration` (free text, the AI's why/how).
   - extraction: tokenize identifiers (CamelCase / snake_case tokens, dotted paths) cited in
     the narration; resolve each against the artifact via `index.node` / exact `find`.
   - per citation: `present` (id exists in the changed-neighborhood) vs `invented`.
   - per atomic claim (sentence with ≤1 cited symbol): whether the cited relation/edge exists
     (`has_call_edge`, parents/children, imports) — consistency.
   - output: `{citations_hit, citations_invented, ungrounded_claims, consistency_failures,
     groundedness}`, verdict `PASS`/`REVIEW`. Deterministic thresholds (design: groundedness
     ≥ 0.8 and invented == 0 for PASS; tuned by the validation battery).
   - CLI: `ssrl verify <repo> --changed file1,file2 --explanation <text|@file>`.

Determinism: `explain`/`verify_explanation` are pure functions of (artifact, args). The coding
AI may call them via MCP (Claude Code/Cline/Cursor speak MCP natively), the developer via CLI.

## 5. Groundedness metrics (validation battery, Phase 10)

Reuses the Phase 9 lab harness (corpora: our docs + prototype itself), with a *synthetic coding
AI* — an **opencode subagent running the big-pickle model** (frontier-class, the same caliber
as the real external coding AIs this targets), which drafts the WHaT/WHY/HOW narration on live
change sets in natural language ("here is what I did, why, and how"), exactly as a developer
would paste a Claude/Codex session summary. The auditor then scores it:

- **citations hit-rate** — prompts drafted explanations on verbatim change sets;
- **invented-citation count** — identifiers in narration with no artifact match;
- **unsupported-claim rate** — atomic claims citing nothing;
- **consistency failures** — cited relation/edge absent from the artifact;
- ceiling check: hand-written **ground-truth narrations** must score groundedness = 1.0,
  invented = 0 — the read-off ceiling, same technique as Phase 9.
- battery result + report section + thresholds fixed from data (not assumed).
- **Executed (Phase 9.5):** `lab/p10_eai.py` — faithful narrations drafted by the
  opencode/big-pickle subagent scored **3/3 PASS with groundedness 1.0 and invented 0**
  (ceiling confirmed); the adversarial narration with a fabricated reference was **1/1
  caught** (REVIEW, groundedness 0.67, invented 1). Full table in `prototype/REPORT-P10.md`
  §5 and `lab/p10_eai_results.md`. Thresholds ship conservative (≥ 0.8, invented==0);
  tuning from a larger battery is Phase 10 data work.

## 6. Honest limits (documented, same candor as ADR-008)

- Identifier-token extraction on free text is heuristic (false splits for hyphenated/underscore
  names); mitigated by exact-match against the artifact symbol set and by reporting unresolved
  tokens as *unresolved*, not *invented*, when they are not quote-shaped identifiers.
- No semantic entailment: a narration can be fully "grounded" yet describe the wrong reason.
  The auditor catches fabricated references and structural inconsistency, not wrong intent.
- Language-agnostic *by contract*, but the fact layer is Python-only today (ADR-001); a TS/JS
  or "whatever the AI produces" extractor would drop into the same contract unchanged.

## 7. Determinism and dependency contract

- `ssrl/explain.py` (new) + `ssrl/verify.py` (new, or one module) — stdlib only, no LLM
  imports, deterministic given the artifact. The MCP `TOOLS` list and CLI verbs grow by the
  two additions; everything else untouched.
- The only model contact in this phase is the *lab harness*: an opencode subagent (model
  `opencode/big-pickle`) drafts the coding-AI narrations for the battery. The layer never
  trusts a model for authority: **the AI is the witness, the layer is the notary** —
  extending ADR-007/ADR-008 "model proposes, structure disposes" to the external process.

## 8. Consequences

- **Positive:** SSRL gains the differentiated, author-flagged capability — making any coding
  AI's self-explanation *auditable*; the MCP surface (ADR-006) becomes the vector coding AIs
  already speak; the auditor works even when the AI never heard of SSRL; the contract is what
  survives the language transition (ADR-001), since it references facts, not syntax.
- **Negative / risk:** identifier-citation heuristics add review noise; narration quality is
  bounded by the writer; "grounded but wrong reason" remains — documented, not solved. Tuning
  thresholds is Phase-10 data work, so v0.8 ships with conservative settings.

## Alternatives considered

- **Trust the coding AI's self-report** (require it to summarize; no audit): rejected — Phase 9
  proved the model's word is transcription/refusal, not ground truth.
- **Structured change manifest from the AI** (the AI emits a JSON SBOM of its edits to verify):
  rejected — a self-reported manifest is the same unreliable witness in prettier shape; the
  structural WHAT must come from the layer, and the auditor must not depend on the AI's honesty.
- **Schema-enhanced narration (agentic "reason traces")**: deferred — training/coercing
  external AIs to emit machine-readable traces precedes SSRL's value and depends on every
  vendor; free-text audit covers all of them, today.
- **Internal-only explainability (SSRL's own micro-LLM):** explicitly out of scope per the
  author — the external process is the point.

## Decision checklist for the author

- [x] Ratify the WHY/HOW-as-claim, WHAT-as-fact split (the AI witnesses, the layer notarizes).
      **Ratified ("implemente") — implemented in `ssrl/explain.py`.**
- [x] Ratify scope: MCP `explain` + `verify_explanation`, CLI `verify` (+`explain`), new
  `ssrl/explain.py`; no changes to the micro-LLM stage; the Phase 10 lab drafts narrations
  with an **opencode subagent on model `opencode/big-pickle`** acting as the synthetic coding AI.
  **Implemented and battery-executed (3/3 ceiling PASS, 1/1 fabricated caught).**
- [x] Accept the obvious ceiling: grounding + structural consistency only; no semantic entailment.
  **Accepted — documented in REPORT-P10 §7.**
- [x] Confirm target: implement after ratification (Phase 10, same commit/publish discipline).
  **Done as phase 9.5 — commit/publish follows the project discipline.**