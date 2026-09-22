# ADR Index — SSRL Research Decisions (W5)

> Architecture Decision Records produced by the W5 synthesis of W1 (literature), W2 (prior art), W3 (discourse) and W4 (Python probe). Each ADR resolves one open decision from `docs/architecture.md`. Status: **Accepted** — ratified by the maintainer (2026); requirements and architecture docs bumped to v1.0 (Gate G1 passed).

| ID | Decision | Status | Evidence |
| --- | --- | --- | --- |
| [ADR-001](ADR-001-target-language.md) | Target language: **Python** | **Accepted** | W4 probe; W2 tree-sitter/ast findings |
| [ADR-002](ADR-002-parser-strategy.md) | Parser: **stdlib `ast` first**; tree-sitter deferred | **Accepted** | W4 probe (100% parse, 3s, 0 deps) |
| [ADR-003](ADR-003-storage.md) | Storage: **derived artifact** (JSON/graph files), no DB service in v1 | **Accepted** | W4 output shape; dev-friendly NFR-1 |
| [ADR-004](ADR-004-vectors.md) | Embeddings/vector DB: **not needed** for fact layer or first projection | **Accepted** | W4 (facts are free); W2 Cursor/GraphRAG findings |
| [ADR-005](ADR-005-primary-projection.md) | Primary projection (RN-1): **H1 grounded Q&A** as primary; H3 living narrative as the differentiated co-surface; H4 graph demoted to supporting | **Accepted** | W1, W2, W3 triangulation |
| [ADR-006](ADR-006-integration-surface.md) | Integration: **CLI first**, then **MCP** for agents | **Accepted** | W2 (editor/agent protocol won); dev-friendly NFR-1 |
| [ADR-007](ADR-007-hypothesis-sources.md) | Hypothesis sources: **structure/naming first, LLM last** | **Accepted** | W1 (LLM grounding), W2 (Aider repo map) |

**Gate G1 status: PASSED.** All ADRs ratified. Requirements and architecture frozen to v1.0. Prototype coding may begin (roadmap Phase 3).