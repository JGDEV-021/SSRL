# SSRL v0.2

## Semantic Software Representation Layer

### A Position Paper on Software Understanding in the Age of AI

---

## Abstract

Artificial intelligence has made software *production* nearly free. The bottleneck of software engineering has moved. Producing code is cheap; **understanding it is not**. Teams now ship codebases that even their authors and the models that generated them cannot fully explain.

This paper introduces the Semantic Software Representation Layer (SSRL): a proposal for a derived, continuously synchronized representation of software — separate from source code — that makes what a system *is*, *does*, and *means* explicit, navigable, and answerable. SSRL is not a documentation generator, nor a graph product, nor a static analyzer. It is a layer over code that serves comprehension to both humans and AI agents, with an explicit separation between **deterministic facts** and **probabilistic hypotheses**, where every hypothesis carries confidence and evidence.

A central open question — the subject of the research agenda — is which **projection** becomes the primary interface to that layer: on-demand question answering, progressive semantic zoom, a living narrative, or graph exploration.

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

The gap between these modes is a **comprehension gap**, and it is widening: AI lowers the cost of producing code (making SLOP common) without reducing the cost of understanding it.

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

First-draft entities: structural (Repository, Package, Module, Class, Interface, Function, Event, ExternalDependency) and semantic (Service, Flow, Intent, DomainConcept, Rule). Relations include structural (CONTAINS, IMPORTS, CALLS, TRIGGERS, DEPENDS_ON, IMPLEMENTS) and semantic (PARTICIPATES_IN, SUPPORTS_INTENT, RELATED_TO), with READ/WRITE/MODIFY families where data-flow analysis is affordable.

The model is provisional. Its validation is a research question: which concepts carry real comprehension value on real code (RQ-5).

## 7. Confidence and evidence

Semantic understanding is treated as probabilistic — an agreement among independent evidence sources (naming, structure, documentation, usage, similarity, LLM proposal, history):

```yaml
Intent: PurchaseValidation
Evidence:
  Naming: 0.82
  Structure: 0.91
  Documentation: 0.76
Confidence: 0.83
```

Confidence is not certainty; it is stated confidence in a hypothesis, revisable as evidence accumulates. Calibration — what `0.83` actually communicates to a user or agent — is a research problem (RQ-3).

## 8. Projections and the open interaction question

A projection is how a consumer experiences the layer. Candidates:

- **H1 — On-demand Q&A.** Ask anything; get grounded answers with evidence.
- **H2 — Progressive semantic zoom.** Collapse the system into a comprehensible high-level model, then drill into detail.
- **H3 — Living narrative.** The system explains itself, in order, updated as code changes.
- **H4 — Graph exploration.** Navigate entities and relationships directly.
- Supporting: AI-agent context supply; CI impact reports.

**Which projection is primary — and whether the answer varies by domain — is the central open question of SSRL.** It is deliberately unresolved here. Answering it with evidence, before implementation, is the first research deliverable (RQ-2).

## 9. Positioning against existing work

SSRL does not replace: static analyzers (CodeQL, Semgrep), search/navigation (Sourcegraph, OpenGrok), knowledge graphs, RAG/GraphRAG, or human comprehension. It complements them and tests a specific, under-served claim:

> Existing systems answer *how the software works* (analysis) and *where the code is* (search). SSRL investigates *why it exists, what it means, and with what confidence* — through a *layer*, not an artifact.

Its differentiation rests on three structural properties (to be validated, not assumed):

1. **Epistemic honesty** — facts and hypotheses are never conflated.
2. **First-class confidence** — no semantic claim without evidence.
3. **Continuity** — derived incrementally from code, never stale by design.

## 10. Research agenda

- **RQ-1 (Value):** Does a semantic representation layer measurably improve comprehension over source-only reading and agent Q&A?
- **RQ-2 (Interaction):** Which primary projection best serves comprehension with least friction?
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

## 12. Limitations

SSRL will not: guarantee perfect intent extraction; guarantee correctness; scale infinitely; replace developer expertise. It is an assistive layer that manages uncertainty honestly — an amplifier of comprehension, not a substitute for judgment.

## 13. Roadmap to validation

1. **Foundation (current).** Vision, requirements, architecture concerns, research plan.
2. **Research Phase 1.** Literature, prior art, practitioner discourse, cheap read-only probes. Gate: resolve the primary projection with evidence.
3. **Prototype.** Facts-only extraction on a small real repository; then the primary projection.
4. **Enrichment.** Hypotheses, confidence, evidence; incremental sync.
5. **Validation.** Controlled comprehension experiments (Phase 9 of the roadmap).

No implementation code is written before the research gate — the design space is decided by evidence, not guesswork.

## 14. Conclusion

AI reduced the cost of *creating* software. The price is that software is now produced faster than it can be understood. SSRL proposes a semantic representation layer to close the gap: honest, derived, continuously synchronized, and dev-friendly — serving both the developer and the agent.

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