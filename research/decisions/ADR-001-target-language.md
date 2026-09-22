# ADR-001 — First Target Language: Python

- Status: **Accepted** (ratified with ADR-005, 2026)
- Decides: `docs/architecture.md` D-2
- Evidence: W4 probe (`research/probes/`), W1/W2

## Context

SSRL needs a first validation corpus. Language choice affects parser feasibility (D-4), domain-signal quality for semantic hypotheses, and how quickly a demo can be built. The original docs floated several languages.

## Decision

**Python is the sole first target language of SSRL v1.** Other languages are explicitly out of scope for the prototype and research validation phases; the parser interface must not preclude them later (FR-9), but no work is committed to them.

## Evidence

- W4 probe: stdlib `ast` alone parsed **100% of two real Python corpora** (31-file clean package + 122-file messy codebase), 1058 nodes in 3.3 s, zero dependencies.
- W2: tree-sitter (the usual multi-language answer) is **not required** for Python facts (ADR-002) — choosing Python removes the multi-language parser problem from the critical path entirely.
- Python's syntax (significant whitespace, decorators, async) is representative enough that mechanisms proven here (fact extraction, call graph, incremental updates) transfer.

## Consequences

- **Positive:** one grammar, stdlib parser, instant test corpora (any GitHub Python repo), no grammar-maintenance burden for the prototype.
- **Negative / risk:** domain-signal richness of the semantic layer is first measured only in Python ecosystems; conclusions about other languages must be re-validated. Mitigated by keeping the semantic model (facts/hypotheses) language-agnostic in `docs/concepts.md`.

## Alternatives considered

- **Multi-language from day one (tree-sitter):** rejected — adds a native dependency, grammar management, and delays the actual product question (projection value) by weeks. Revisit only when FR-9 activates.