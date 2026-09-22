# SSRL Concepts

## The semantic representation model

- Version: 0.2
- Status: Draft
- Audience: future implementers and contributors

---

## 1. What a semantic representation layer is

A layer sits between the source code and anyone trying to understand it. Concretely, it is a derived, persistent model of what the software *is*, *does*, and *means*, living alongside the code — always regenerated, always traceable.

The model separates knowledge into two epistemic classes that are **never conflated**:

### Facts (deterministic)

Things that are true by construction and verifiable against the code:

- "module X imports module Y"
- "function `f` calls function `g`"
- "event `e` triggers handler `h`"
- "class `C` extends `B`"

Facts come from parsing and AST analysis. A fact has confidence `1.0` — it is either true in the code or the parser is wrong.

### Hypotheses (probabilistic)

Interpretations about *meaning* that cannot be proven from syntax alone:

- "module Y participates in the purchase flow"
- "this service belongs to the inventory system"
- "intent: validate purchase before charging"

Hypotheses are inferred from evidence — names, comments, documentation, structure, usage patterns, LLM reasoning. They are **never promoted to facts**.

---

## 2. Confidence and evidence

Every hypothesis carries:

```text
hypothesis
├── label          : "purchase validation"
├── confidence     : 0.0–1.0
├── evidence       : [ { source, weight, detail }, ... ]
└── method         : how it was produced
```

Candidate evidence sources:

- Structural patterns
- Naming conventions
- Documentation and comments
- Usage patterns / call context
- Similarity and embeddings
- LLM proposals
- Git history / human annotation

Confidence is a weighted agreement among independent evidence sources — it expresses *confidence in the hypothesis*, not certainty. Calibration of these scores is an open research problem (see [`../research/plan.md`](../research/plan.md), RQ-3).

```yaml
Intent: PurchaseValidation
Evidence:
  Naming: 0.82
  Structure: 0.91
  Documentation: 0.76
Confidence: 0.83
```

---

## 3. Knowledge model (first draft)

Candidate entities the layer understands. This model is provisional — research (RQ-5) will ground and validate it.

### Structural

Repository, Package, Module, Class, Interface, Function, Event, ExternalDependency.

### Semantic

Flow, Intent, DomainConcept, Rule, Component/Service.

### Relations (first draft)

`CONTAINS`, `IMPORTS`, `CALLS`, `TRIGGERS`, `DEPENDS_ON`, `IMPLEMENTS`, `USES`, `READS`, `WRITES`, `MODIFIES`, `CREATES`, `DESTROYS`, `PARTICIPATES_IN`, `SUPPORTS_INTENT`, `RELATED_TO`.

See the **graph projection** ([`projections/graph.md`](projections/graph.md)) for the formal schema of these candidates.

---

## 4. Projections

A **projection** is an interface that lets a consumer experience the layer. Any projection can render the same underlying model.

Candidate projections:

| Projection | Question it answers | Primary candidate? |
| --- | --- | --- |
| Question & answer | "Ask anything about this system, with evidence" | Hypothesis **H1** |
| Progressive zoom | "It's an inventory system → here is how purchasing actually works" | Hypothesis **H2** |
| Living narrative | "Tell me the story of how this system works, updated as code changes" | Hypothesis **H3** |
| Graph exploration | "Show me everything and how it connects" | Supporting surface |
| Agent context | "Give the agent grounded, up-to-date context" | Supporting surface |
| CI impact report | "What does this PR actually affect?" | Supporting surface |

Only one projection is expected to become the **primary** interaction. Resolving it is the central decision of the research phase.

---

## 5. Lifecycle and synchronization

The layer is constantly derived:

```text
code change → diff → affected facts → affected hypotheses → partial re-derivation
```

Full rebuilds are a fallback, never the default. This is P4 (continuity by design) — a design requirement, not an optimization concern (see [`requirements.md`](requirements.md), NFR-3).

---

## 6. Consumers

- **Developers** — in the IDE, CLI, or via rendered projections.
- **AI agents** — as grounded context with traceable evidence (reduces unwarranted trust in agent reasoning).
- **CI/CD** — architecture impact reports on pull requests.
- **Auditors** — traceability: every claim back to a code location.