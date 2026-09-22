# ADR-004 — Embeddings / Vector DB: Not Needed

- Status: **Accepted** (ratified with ADR-005, 2026)
- Decides: `docs/architecture.md` D-6
- Evidence: W4 probe; W2 (Cursor, GraphRAG); W1 §5 (RAG grounding)

## Context

The original architecture proposed a "Vector Layer" between the graph and the semantic engine. D-6 asked whether embeddings are needed at all.

## Decision

**No vector store and no embedding generation in the fact layer or the first projection.** Embeddings are explicitly deferred; if a later projection needs semantic retrieval, they are an optional *accelerator* behind that projection, never part of the fact layer or a prerequisite for value.

## Evidence

- W4: the entire fact layer (modules, functions, calls, imports) was derived **structurally with zero vectors** — embeddings are unnecessary for facts.
- W2: Cursor's embedding index answers "looks like" but has **no resolved edges** ("who calls X?" fails) — vectors do not provide the structural comprehension SSRL targets.
- W1 §5: on code, the biggest grounding wins come from **structure + mechanical verification** (Arafat 2025, zero hallucination), not from similarity retrieval. Vectors are the weak link for cross-file structure.

## Consequences

- **Positive:** removes an entire infra component (NFR-1), keeps the layer deterministic (NFR-4), avoids GraphRAG's indexing-cost failure mode (W1: GraphRAG in maintenance mode).
- **Negative / risk:** a future Q&A projection wanting "find similar code" would need them then — acceptable, since that is retrieval, not comprehension, and is projection-scoped.
- The "Vector Layer" is struck from the reference flow in `docs/architecture.md` §5.

## Alternatives considered

- **Vector store from day one (original design):** rejected — would import cost and staleness problems (the documented killer of prior index products) with no evidence they improve comprehension.