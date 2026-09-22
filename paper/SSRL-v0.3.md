# SSRL v0.3

## Semantic Software Representation Layer

### A Position Paper on Software Understanding in the Age of AI

---

## Abstract

Artificial intelligence has made software *production* nearly free. The bottleneck of software engineering has moved. Producing code is cheap; **understanding it is not**. Teams now ship codebases that even their authors and the models that generated them cannot fully explain.

This paper introduces the Semantic Software Representation Layer (SSRL): a proposal for a derived, continuously synchronized representation of software — separate from source code — that makes what a system *is*, *does*, and *means* explicit, navigable, and answerable. SSRL is not a documentation generator, nor a graph product, nor a static analyzer. It is a layer over code that serves comprehension to both humans and AI agents, with an explicit separation between **deterministic facts** and **probabilistic hypotheses**, where every hypothesis carries confidence and evidence.

v0.3 updates: the research program has passed its first gate (G1). The primary projection question (RQ-2) is resolved by evidence in favor of **grounded Q&A (H1) with a living narrative (H3) as co-surface**, and this resolution is now validated by a working, dependency-free V1 prototype on real repositories (Sections 8, 13, 15).

---

## 1. Introduction

For decades, software engineering optimized *production*. Languages, frameworks, IDEs, and automated tooling reduced the effort to create software. Artificial intelligence completed that trajectory: code generation has become so cheap that "how do we write it" is rarely the hard question anymore.

A new asymmetry has emerged:

```text
Cost of producing code   ↓↓
Cost of understanding code  →
```

Modern AI systems can generate software faster than people — or other AI systems — can comprehend it. The consequences are visible across the industry: codebases nobody fully understands, "ask the agent" as a substitute for knowledge, refactors that break undocumented invariants, and teams that cannot tell good AI-generated output from bad.

The question SSRL poses:

> If software can be generated faster than it can be comprehended, what abstraction is required to preserve and communicate the understanding contained in that software?

## 2. The comprehension gap

Code producers today fall into three modes:

| Mode | Relationship to AI | Understanding of the system |
| --- | --- | --- |
| **AI SLOP** | Generates code without understanding it | None — cannot judge, fix, explain, or trust it |
| **AI DEV** | Generates code deliberately | Local — understands what they produced |
| **DEV** | Builds structure and logic themselves | Systemic — holds the full mental model |

The gap between these modes is a **comprehension gap**, and it is widening: AI lowers the cost of producing code (making SLOP common) without reducing the cost of understanding it. Practitioner evidence (Section 14, W3) confirms that this gap is experienced in production: engineers report onboarding measured in weeks, unreadable inherited systems, and "ask the agent" becoming a substitute for owned knowledge.

**SSRL's thesis is that this gap can be compressed by an external representation layer** — so that a developer or an agent can reach the "DEV" level of understanding of any codebase, in the time it currently takes to generate code, with evidence for every claim.

## 3. Problem statement

Source code contains implementation *and* knowledge, but the knowledge is implicit. Developers routinely need to answer:

- Why does this component exist?
- Which business process depends on it?
- What breaks if this module changes?
- Which flow does this function belong to?
- What was the intent behind this implementation?

Existing artifacts answer these poorly:

| Artifact | Strength | Limitation |
| --- | --- | --- |
| Source code | Exact | Hard to navigate at scale |
| Documentation | Readable | Goes stale |
| AST/CFG/PDG | Accurate | No meaning |
| Dependencies | Precise | No intent |
| AI explanation | Flexible | Unverifiable, non-persistent |

SSRL proposes investigating a layer whose job is exactly the column these artifacts miss: preserving *software knowledge* — with provenance.

## 4. Proposal: a semantic representation layer

SSRL is a derived layer over source code. Derivation is non-negotiable: the code is the truth; the layer is always regenerated from it and never overrides it.

The layer holds two epistemic classes, never conflated:

- **Facts** — deterministic, verifiable structure: modules, functions, calls, imports, events, dependencies. (Confidence `1.0`.)
- **Hypotheses** — probabilistic interpretations of meaning: intent, flows, domain concepts. (Confidence `0–1`, with evidence.)

Every hypothesis carries confidence, the evidence behind it, and its production method. "Why does SSRL believe this?" must always have an answer.

The layer synchronizes **incrementally** as code changes. A representation that goes stale is misinformation.

## 5. Design principles

1. **Code is the source of truth.** The layer is derived, never authoritative.
2. **Facts and hypotheses never mix.** Two labeled epistemic categories.
3. **No claim without evidence.** Confidence + provenance on every hypothesis.
4. **Continuity by design.** Incremental, automatic regeneration; manually-synced artifacts are forbidden.
5. **Dev-friendly or it fails.** Adoption friction above value means death. The bar is minutes-to-first-value, zero ceremony.
6. **Projections are views, not the product.** Graphs, narratives, dashboards and reports are interfaces to the layer.
7. **AI is a worker, not an oracle.** LLM output is a hypothesis source, never truth.
8. **Comprehension is the metric.** Success is measured by comprehension outcomes, not by artifact beauty.

## 6. Semantic model

v0.1 entities are now constrained by the prototype (ADR-003 artifact schema):

- **Structural (facts, confidence 1.0, always derived):** `Repository`, `Module`, `Class`, `Function`, `Method`.
- **Semantic (hypotheses, confidence [0,1), always inferred):** `Service`, `Flow`, `Intent`, `DomainConcept`.

Relations: structural `CONTAINS`, `IMPORTS`, `CALLS`; semantic `PARTICIPATES_IN`, `SUPPORTS_INTENT`, `RELATED_TO`. IDs are stable and deterministic (`module::<id>`, `class::<mid>::<name>`, `func::<mid>::<name>`).

The model remains provisional. Which concepts carry real comprehension value on real code is a live research question (RQ-5); the MVP validates that the *mechanism* — derived facts + labeled hypotheses — is implementable and fast enough (Section 15).

## 7. Confidence and evidence

Semantic understanding is treated as probabilistic — an agreement among independent evidence sources (naming, structure, documentation, usage, similarity, LLM proposal, history):

```yaml
Flow: func::benchmark::main
Evidence:
  CallGraph (entry): 0.88
  CallGraph (chain): 1.0
Confidence: 0.88   # noisy-OR capped by strongest single source
```

v0.3 policy (implemented, conservative — ADR-007 / RN-3):
- Hypotheses are capped so the combined confidence **never exceeds the strongest single source**; naming-only hypotheses cannot exceed their naming weight; evidence-free hypotheses demote to `0.5`.
- "Why does SSRL believe this?" is answered by `why()`/`audit()` for any node — already wired into the CLI.

Confidence is not certainty; it is stated confidence in a hypothesis, revisable as evidence accumulates. Calibration — what `0.83` actually communicates to a user or agent — remains an open research problem (RQ-3), now with a primitive auditable in the prototype.

## 8. Projections — the resolved open question

A projection is how a consumer experiences the layer. Candidates:

- **H1 — On-demand Q&A.** Ask anything; get grounded answers with evidence.
- **H2 — Progressive semantic zoom.** Collapse the system into a comprehensible high-level model, then drill into detail.
- **H3 — Living narrative.** The system explains itself, in order, updated as code changes.
- **H4 — Graph exploration.** Navigate entities and relationships directly.
- Supporting: AI-agent context supply; CI impact reports.

**Resolution (Gate G1, 2026, evidence-backed):** Grounded Q&A (H1) is the **primary** projection; the living narrative (H3) is the **co-primary** on-demand surface. H2 and H4 are supporting. This is recorded as **ADR-005** with W1–W3 evidence sections (literature, prior art, practitioner discourse).

Why this resolution: prior-art and market analysis (W2) showed graph-first products (e.g., Sourcetrail) failing in adoption despite technical merit, while practitioner demand cluster around *questions* and answers; literature (W1) supports structural grounding of Q&A; a real codebase probe (W4) confirmed the fact layer is cheap at scale with stdlib tooling.

## 9. Positioning against existing work

SSRL does not replace: static analyzers (CodeQL, Semgrep), search/navigation (Sourcegraph, OpenGrok), knowledge graphs, RAG/GraphRAG, or human comprehension. It complements them and tests a specific, under-served claim:

> Existing systems answer *how the software works* (analysis) and *where the code is* (search). SSRL investigates *why it exists, what it means, and with what confidence* — through a *layer*, not an artifact.

Its differentiation rests on three structural properties (in v0.3 implemented, not just argued):

1. **Epistemic honesty** — facts and hypotheses are never conflated (the prototype enforces this boundary end-to-end).
2. **First-class confidence** — no semantic claim without evidence (calibrate/why/audit are working code).
3. **Continuity** — derived incrementally from code, never stale by design (file-level hash cache, D-8).

## 10. Research agenda

- **RQ-1 (Value):** Does a semantic representation layer measurably improve comprehension over source-only reading and agent Q&A?
- **RQ-2 (Interaction):** Which primary projection best serves comprehension with least friction? → **Resolved (G1): H1 primary + H3 co-surface.** Secondary resolution (by domain, by task) remains open.
- **RQ-3 (Trust):** Does confidence + evidence reduce unwarranted trust and hallucination in AI code reasoning?
- **RQ-4 (Sources):** Which hypothesis sources give the best confidence/cost trade-off?
- **RQ-5 (Model):** Which semantic concepts survive contact with real code?

Methodology and gates are specified in [`research/plan.md`](../research/plan.md).

## 11. Threats to validity

- **Semantic ambiguity.** Software admits multiple valid interpretations; the layer must represent uncertainty, not hide it.
- **Misleading names.** Naming signals can be wrong; evidence must be multi-source.
- **Obfuscated/generated code.** Extraction quality degrades; value must be shown on ordinary code first.
- **Domain dependence.** Semantic signal quality varies by domain; validation requires representative corpora.
- **LLM bias.** If LLMs propose hypotheses, their biases propagate; confidence must be calibratable.
- **Scale.** Dense systems may overwhelm the consumption surface; projections must manage cognitive load.
- **The "ask the agent" baseline.** If agent Q&A becomes good enough on raw code, SSRL's value claim weakens — exactly why RQ-1/RQ-2 must be tested empirically, not assumed.

v0.3 addition: **hypothesis quality.** The MVP's naming/structure heuristics produce hypotheses that are *labeled and bounded* but not yet quality-validated; the `audit` output is the instrument, ground truth remains future work (Phase 9).

## 12. Limitations

SSRL will not: guarantee perfect intent extraction; guarantee correctness; scale infinitely; replace developer expertise. It is an assistive layer that manages uncertainty honestly — an amplifier of comprehension, not a substitute for judgment.

## 13. Roadmap — status update

1. **Foundation.** Vision, requirements, architecture concerns, research plan. ✅
2. **Research Phase 1.** Literature, prior art, practitioner discourse, probes. ✅ W1–W4 complete.
3. **Decision & spec freeze.** ADRs 001–007 **all accepted**; requirements/architecture **frozen to v1.0**. ✅ **Gate G1 PASSED.**
4. **V1 prototype.** Facts-only extraction **plus** the primary projection (H1 QA), hypotheses (enrichment), confidence engine, living narrative (H3), and a CLI — delivered as a single dependency-free package. ✅ (Phases 3–6 of the roadmap, compressed; see Section 15.)
5. **Validation.** Controlled comprehension experiments (Phase 9). ⏳ Next.

## 14. Evidence base (summary)

| Workstream | Question | Finding |
| --- | --- | --- |
| W1 · Literature | Does structured grounding help? | Yes — evidence for facts + hypotheses as separate epistemic classes; structural grounding of Q&A supported. |
| W2 · Prior art & market | Why do comprehension tools fail? | Graph-first products under-adopted (Sourcetrail); demand converges on *answers, not graphs*. |
| W3 · Practitioner discourse | Is the comprehension gap real? | Confirmed: onboarding cost, unreadable systems, agent-as-substitute pain, reported continuously. |
| W4 · Probe | Is the fact layer cheap? | stdlib `ast` parses 100% of two real corpora (31 + 122 files) in ~0.5–3.3 s, deterministic, zero deps. |
| W5 · Decisions | Which directions survive? | ADR-001…007 accepted; Q&A primary; graph hypothesis support dropped as primary. |

## 15. Prototype findings (V1 MVP)

Implementation: `prototype/ssrl/` — 10 modules, stdlib only, deterministic. Corroborate the paper's structural claims:

- **Facts are cheap and exact.** 100% parse on both corpora (31 + 122 files), 0 syntax errors; deterministic across runs (identical node/edge id sets).
- **Hypotheses can be produced without AI and labeled honestly.** Call-chain flows, naming/docstring intents, and module/class domain concepts are generated with `confidence < 1.0` and explicit evidence; `why`/`audit` explain each.
- **Primary projection works on real code.** The grounded Q&A answers `where is X`, `who calls X`, `what does X do`, `imports of X`, `entry points`, `flows` with facts split from hypotheses.
- **Continuity is implementable.** File-level hash caching (D-8) makes warm builds incremental without perturbing determinism.
- **39 unit tests green** on a synthetic fixture; determinism verified on both real corpora; continuous `watch` regeneration (Phase 7) keeps the layer fresh without manual sync.

Full metrics and honest limits: [`prototype/REPORT-V1.md`](../prototype/REPORT-V1.md), [`prototype/README.md`](../prototype/README.md), [`prototype/BUILDLOG.md`](../prototype/BUILDLOG.md).

These findings are *positive but preliminary*: they validate mechanics at MVP scale, not the comprehension-value claim (RQ-1) — that remains Phase 9's job.

## 16. Conclusion

AI reduced the cost of *creating* software. The price is that software is now produced faster than it can be understood. SSRL proposes a semantic representation layer to close the gap: honest, derived, continuously synchronized, and dev-friendly — serving both the developer and the agent. A dependency-free prototype now demonstrates the mechanics end-to-end on real code, from facts through hypotheses to the grounded Q&A projection chosen by research.

SSRL's contribution is not a graph or a document. It is a proposal for a new category: **a layer of understanding above the code** — and a research program to prove whether, and how, it works.

---

## Manifesto

> AI reduces the cost of creating software.
>
> Humans define its purpose.
>
> SSRL seeks to reduce the cost of understanding it.
>
> Knowledge that cannot be understood is lost knowledge.