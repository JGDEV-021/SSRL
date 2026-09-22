# SSRL Requirements (Spec-Driven)

- Version: **1.0 (frozen — Gate G1 passed)**
- Status: All research-gated items resolved and **accepted** (ADR-001…007, 2026 sign-off). This spec is the contract for the prototype phase; changes require a new ADR.

---

## Conventions

| Prefix | Meaning |
| --- | --- |
| `FR-x` | Functional requirement |
| `NFR-x` | Non-functional requirement |
| `RN-x` | Research-gated requirement (cannot be specified until research resolves it) |

**Priority:** Must / Should / Could.

---

## 1. Functional requirements

### FR-1 — Derive structural facts (Must)
SSRL must extract deterministic structural facts from source code: modules, functions, classes, interfaces, events, imports, calls, dependencies.

### FR-2 — Produce semantic hypotheses (Should)
SSRL should infer semantic hypotheses over structural facts: intent, flows, domain concepts, business meaning.

### FR-3 — Separate facts from hypotheses (Must)
All outputs and storage must keep facts and hypotheses in distinct, labeled categories. Conflating them is a defect.

### FR-4 — Attach confidence and evidence (Must)
Every hypothesis must carry a confidence score and its supporting evidence. Every fact must be traceable to a code location.

### FR-5 — Update incrementally (Must)
The layer must regenerate on code changes without a full rebuild as the default path.

### FR-6 — Provide at least one projection (Must)
Consumers must be able to experience the layer through at least one projection. **RB-1 (resolved RN-1, ADR-005): the primary projection is grounded on-demand Q&A (H1), with the living narrative (H3) as an on-demand co-surface; H2 zoom and H4 graph are supporting.**

### FR-6a — Grounded answers with separated facts (Must, from RB-1)
Every Q&A answer must (1) mark which statements are facts (confidence 1.0, from the structural layer) vs. semantic hypotheses (calibrated confidence), and (2) attach evidence links resolvable to `file:line` for every claim where structural support exists.

### FR-7 — Serve humans and AI (Must)
Humans (UI/CLI) and AI agents (structured context) are both first-class consumers.

### FR-8 — Zero manual annotation (Should)
The layer must provide value on a repository with no manual configuration or annotation.

### FR-9 — Multi-language (Could)
Support for additional languages beyond the first target is a later concern, but parser interfaces must not preclude it.

---

## 2. Non-functional requirements

### NFR-1 — Dev-friendly (Must)
The bar for adoption: a developer gets first meaningful output on a real repository in minutes, with no configuration ceremony. Any feature that raises friction above its value will not ship.

### NFR-2 — Traceability (Must)
Every claim — fact or hypothesis — must resolve back to a source code location.

### NFR-3 — Freshness (Must)
The layer always reflects the latest committed state. Bounded staleness is defined; unbounded staleness is a defect.

### NFR-4 — Determinism of facts (Must)
Building from the same commit yields the same facts. facts must not. Hypotheses may vary by method; facts must not.

### NFR-5 — Non-invasive (Must)
Analyzing a repository must not modify it.

### NFR-6 — Performance (Should)
Must scale to large repository sizes. Incremental updates must be cheaper than full rebuilds (NFR laid out in FR-5).

### NFR-7 — Auditable & exportable (Should)
The layer must be exportable in a stable, inspectable format.

--- 

## 3. Research-gated requirements (RN)

### RN-1 — Primary projection (resolved by research, RQ-2 → ADR-005)
SSRL's primary interaction is **grounded on-demand Q&A (H1)** with the **living narrative (H3)** as a co-primary, on-demand surface. Progressive zoom (H2) and the graph (H4) are supporting projections only. Answers are hypotheses-first: facts (confidence 1.0) are separated from inferred semantics (calibrated confidence) and always carry evidence links. *Status: **accepted** (ADR-005 ratified). Now specified concretely as FR-6 / FR-6a.*

### RN-2 — Semantic scope (resolved by research, RQ-5)
Which semantic concepts (flows, intents, domain concepts...) are worth extracting for which domains.

### RN-3 — Confidence calibration (resolved by research, RQ-3)
How confidence scores are computed and what `0.83` actually means to a user.

### RN-4 — Hypothesis sources (resolved by research, RQ-4 → ADR-007)
Stacked priority: structural evidence first (deterministic, free), naming/structure heuristics second, LLM proposals last and only as *proposers* (always a hypothesis with explicit low-default confidence, never a fact; never required for the fact layer or first projection).

### RN-5 — Storage and architecture direction (resolved by research + probes → ADR-003/004)
Storage is a **derived artifact** (`{nodes, edges}` JSON regenerated from code) with SQLite as the pre-declared escalation if query performance demands it. **No vector DB and no embedding generation** in the fact layer or first projection (ADR-004). No DB service in v1.

---

## 4. Status table

| ID | Priority | Status |
| --- | --- | --- |
| FR-1 … FR-9 | Mixed | Provisional |
| NFR-1 … NFR-7 | Mixed | Provisional |
| RN-1 | — | **Resolved (ADR-005, accepted)** → FR-6/FR-6a |
| RN-2 | — | Open (research, Phase 5+) |
| RN-3 | — | Open (research, Phase 6) |
| RN-4 | — | **Resolved (ADR-007, accepted)** |
| RN-5 | — | **Resolved (ADR-003, ADR-004, accepted)** |

Research Phase 1 has resolved RN-1, RN-4, RN-5 — all **accepted** at ADR-005 sign-off. **This document is frozen at v1.0 (Gate G1 passed).** RN-2 (semantic scope) and RN-3 (confidence calibration) remain open until the prototype produces data and are tracked as research-phase follow-ups, not input specifications.