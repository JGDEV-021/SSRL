# ADR-003 — Storage: Derived Artifact, No Database Service in v1

- Status: **Accepted** (ratified with ADR-005, 2026)
- Decides: `docs/architecture.md` D-3 (direction)
- Evidence: W4 output shape; NFR-1 (dev-friendly); W2 (Glean, Cursor index cost)

## Context

Architecture doc listed embedded store vs SQLite vs DB service vs graph DB. Prior art (W2) says storage is not the hard part — the schema is; every storage-owning tool either failed (Sourcetrail) or is heavy (Glean at Meta scale, Neo4j).

## Decision

**SSRL v1 stores the fact layer as derived, versioned JSON artifacts (the `{nodes, edges}` structure validated in W4), checked alongside or regenerated from the repository — with SQLite as the optional acceleration if query performance demands it.** No graph database, no vector database, no running service.

The artifact is always **derived from code** (P1): the source of truth is the repository; the artifact is regenerable.

## Evidence

- W4 emitted exactly this shape for two real corpora with no schema adjustments — the artifact format is already validated.
- NFR-1 (dev-friendly): a developer must get value in minutes with zero ceremony. `git clone` + run = a queryable fact artifact beats "install Neo4j, model schema, sync."
- W2: Cursor's index is client-side and light; Glean's heavy fact-store is a scale solution SSRL does not need at prototype/research scale.
- `docs/concepts.md` P6: projections are views over the layer — storage is an implementation detail behind the layer, freely swappable later.

## Consequences

- **Positive:** zero infra (NFR-1), trivially portable, diffable (supports future drift analysis), matches "derived, never authoritative" (P1, NFR-4 determinism).
- **Negative / risk:** no query engine at scale yet; graph traversal queries on large repos may need an index. Mitigation: SQLite (embedded, stdlib) is the pre-declared escalation path — not a rewrite.
- Multi-developer / concurrent access is out of scope for v1 (single-artifact, regenerate-or-pull model).

## Alternatives considered

- **Graph DB (Neo4j/Memgraph):** rejected for v1 — infra cost defeats NFR-1; revisit only if H4 (graph projection) wins ADR-005 *and* queries exceed SQLite/graph-lite capability.
- **Vector DB as primary store:** rejected outright (see ADR-004).