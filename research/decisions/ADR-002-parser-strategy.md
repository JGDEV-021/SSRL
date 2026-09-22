# ADR-002 — Parser Strategy: stdlib `ast` First, Tree-sitter Deferred

- Status: **Accepted** (ratified with ADR-005, 2026)
- Decides: `docs/architecture.md` D-4
- Evidence: W4 probe; W2 (Aider repo map, Cursor chunking, Glean cost)

## Context

W2 assumed tree-sitter as "the de-facto parsing substrate." The question was whether SSRL needs it for the facts layer.

## Decision

**Use Python's stdlib `ast` module as the sole parser for the fact layer in v1.** Tree-sitter is deferred — it becomes relevant only if/when (a) another target language is added (ADR-001 scope), or (b) incremental parsing performance proves insufficient at scale (W4 shows 3.3 s for 122 files — non-issue at prototype scale).

## Evidence

- W4: `ast` parsed **100% of both corpora** with zero syntax errors and zero dependencies; produced clean Module/Function/Method/CONTAINS/IMPORTS/CALLS edges matching `docs/projections/graph.md` unchanged.
- W4 cross-module call resolution (import-alias + relative imports) worked without a full symbol table — the expensive part of parsing turns out not to be needed for feasibility.
- W2's caution (Glean's per-language compiler-accurate parsers = brutal onboarding cost) is avoided: `ast` is the interpreter's own parser, accuracy is free.

## Consequences

- **Positive:** zero third-party deps for extraction (NFR-1 dev-friendly: `pip install` nothing), 100% accuracy on well-formed Python, no grammar drift.
- **Negative / risk:** `ast` is not incremental — every parse is a full file parse. At W4 scale this is negligible; for very large repos a cache keyed by file hash + mtime (cheap, stdlib) is the mitigation. Tree-sitter remains the documented fallback in `docs/architecture.md`.

## Alternatives considered

- **tree-sitter from day one:** deferred per above; would add a native wheel dependency without a demonstrated need.
- **Compiler front-ends (mypy, pyright ASTs):** considered — richer type info but heavier integration; revisit in Phase 5 (semantic enrichment) if type-based evidence proves valuable.