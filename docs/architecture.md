# SSRL Architecture — Design Concerns & Decisions

- Version: **1.0 (frozen — Gate G1 passed)**
- Status: D-1…D-7 resolved and **accepted** (ADR-001…007). D-8 has a working assumption (file-level hash+mtime) pending prototype data.

> This document records the invariants the architecture must respect and the decisions the research phase resolved (ADR-001…007). D-1 is resolved by ADR-005; D-8 retains a working assumption (file-level hash+mtime cache) until prototype data indicates otherwise.

---

## 1. Architectural invariants (will not change)

Derived from [`vision.md`](vision.md) and [`requirements.md`](requirements.md):

1. **Derived, never authoritative.** The layer is always regenerated from code and never overrides it.
2. **Facts and hypotheses are distinct.** Two epistemic classes, one storage-aware separation.
3. **Traceability.** Every claim resolves to a code location.
4. **Incremental sync.** Partial re-derivation is the default; full rebuild is the fallback.
5. **Dual consumers.** Humans and AI agents are first-class.
6. **Dev-friendly.** Friction above value does not ship (NFR-1).

---

## 2. Design drivers

- **D1 — Cold start.** A new repository produces first value in minutes, zero config (NFR-1).
- **D2 — Continuous truth.** Freshness bounded, incremental updates (NFR-3, FR-5).
- **D3 — Honest uncertainty.** Hypothesis ≠ fact; confidence + evidence always present (P2, P3).
- **D4 — Projection-agnostic core.** The model is stable no matter which projection is primary (P6).

---

## 3. Processing concerns

Any implementation must address these stages; the ordering and technology are open:

```text
extraction    →  structural facts from source code (parser)
modeling      →  facts + hypotheses in a stable, auditable model
enrichment    →  hypotheses, confidence, evidence
projection    →  interfaces for humans and AI (view layer)
sync          →  incremental re-derivation on change
```

---

## 4. Decisions (resolved by ADR-001…007)

| ID | Decision | Status |
| --- | --- | --- |
| **D-1** | Primary projection: **H1 grounded Q&A** (primary), H3 living narrative (co-primary, on-demand), H2/H4 supporting | **Resolved — ADR-005 (accepted)** |
| **D-2** | First target language: **Python** | **Resolved — ADR-001** |
| **D-3** | Storage: **derived `{nodes, edges}` artifact**, regenerated from code; SQLite as pre-declared escalation; no DB service in v1 | **Resolved — ADR-003** |
| **D-4** | Parser: **stdlib `ast` first**; tree-sitter deferred (multi-language or incremental-scale fallback) | **Resolved — ADR-002** |
| **D-5** | Hypothesis sources: **structure/naming first, LLM last (as proposer only)** | **Resolved — ADR-007** |
| **D-6** | Embeddings/vector DB: **none** in fact layer or first projection | **Resolved — ADR-004** |
| **D-7** | Integration: **CLI first, MCP second**; LSP/CI deferred | **Resolved — ADR-006** |
| **D-8** | Incremental change granularity | **Working assumption (v1.0): file-level** via hash+mtime cache, per W4; revisit node-level only if freshness binds (NFR-3) |

Decision records: [`/research/decisions/`](../research/decisions/ADR-index.md).

---

## 5. Reference flow (binding at v0.3, revisable by evidence)

```text
Source code (Python)              storage: derived {nodes, edges} artifact
    ↓  (extraction, stdlib ast)   (JSON; SQLite escalation; no DB service)
Structural facts ──► stable model (facts + hypotheses)
    ↓  (enrichment, w/ confidence + evidence)
Semantic hypotheses
    ↓                                projections
Sync on change (hash+mtime)      ├── primary: grounded Q&A (H1, ADR-005)
                                 ├── co-primary: living narrative (H3, on-demand)
                                 └── supporting: graph, zoom (H2/H4), CI
```

Graph and vector layer are **not** required components. Facts are derived structurally with zero vectors and zero probabilistic inference (ADR-002, ADR-004); hypotheses may use an LLM **as proposer only** (ADR-007).

---

## 6. Integration surfaces (resolved by ADR-006)

- **CLI** (`ssrl <repo>`) — dev-friendly cold start; the v1 surface
- **MCP** — grounded context for AI agents (FR-7); the v1.5 surface
- ~~IDE extension (via LSP or editor API)~~ — deferred
- ~~CI report~~ — deferred; candidate for a supporting projection