# Glean (Meta) — Prior Art Note

> Research date: 2026-09-22 · Sources: facebookincubator/Glean (GitHub), glean.software docs (Introduction, Incremental), engineering.fb.com "Indexing code at scale with Glean" (2024-12), Sourcegraph SCIP announcement (Don Stewart integration note), engines.dev code-navigation survey.

## What it is
Meta's **open-source (Apache-2.0) system for collecting, deriving, and querying facts about source code**. Powers code browsing, search, code review navigation, documentation gen, dead-code detection, API migration, RAG for coding assistants — at Meta scale (monorepos, deeply incremental).

## Technical shape (why SSRL cares deeply)
- **Facts**: typed, **schema-defined immutable terms** stored in RocksDB (DAG-shaped, auto-dedup'd). Per-language schemas (C++/C, Hack, Flow/Javascript, + SCIP/LSIF import for Go, Java, Python, Rust, TS, Dotnet). "Think of it as being able to store and query the AST of your code, efficiently and type-safely."
- **Angle**: a Datalog-style declarative query language for schemas AND queries; can **derive new facts by rules** (deferred or at query time) and build **language-neutral abstractions ('SQL views') over language-specific schemas**.
- **Incrementality**: stacked immutable DBs over a base DB; units (typically file/module) label the facts they own; a new DB **hides changed units and overlays re-indexed facts** — O(changes), not O(repo) — with ownership-set propagation so derived facts stay consistent, and multi-revision access simultaneously. ~"index the changes in O(changes)" goal.
- **Diff indexing**: facts are emitted per-diff, producing a "diff sketch" (new class, removed method, added field, new call) → lint, notifications, semantic search over commits, stack-trace→changeset root-cause, code-review navigation. Language-neutral queries in review UI (go-to-def, type-on-hover, docs).
- **Glass**: language-agnostic symbol server on top (documentSymbols, refs, call hierarchy) → LSP server browsing.
- **SCIP support**: Meta engineer integrated Sourcegraph's SCIP (Protobuf, human-readable IDs) into Glean ("8x smaller, 3x faster to process" than LSIF; native mapping ~550 LOC vs 1500).

## Where comprehension stops
Glean stores **mechanical facts only**: definitions, references, calls, inheritance, imports, docs. Deliberately "**not meaning**" — no intent, no business semantics, **no hypotheses, no confidence, no evidence/derivation provenance exposed to users**. It answers "what symbols/edges exist", not "what does this system do / why".

## Relevance to SSRL
- **The strongest existing precedent for SSRL's fact model**: typed schema, deterministic extraction, incremental stacked storage (SSRL P4/P5, D-3), and *derived facts* via rules (direct analog of SSRL "hypotheses derived from facts, with evidence links"). If SSRL ever needs to justify its fact-layer architecture, "Glean does exactly this at Meta scale" is the proof.
- **Its boundary proves SSRL's need**: Glean's fact layer is deliberately meaning-free, and Meta layers human/LLM reasoning on top *ad hoc*. SSRL's unique contribution is the *meaning layer with honest confidence*, which Glean does not attempt.
- **Derived-fact ownership sets** are a precise machinery SSRL can borrow for "evidence provenance" (which facts underpin a hypothesis; invalidate when sources change).
- **Warning**: Glean's per-language schema/indexer cost is high (OSS ships only C++/Hack/F‌low + SCIP bridge; "custom parser must be written" per engines.dev) → SSRL should *not* copy the compiler-grade indexer investment; tree-sitter-based cheap extraction (W4) is the right scope for a first slice.

## Licensing
Apache-2.0 — permissively reusable (conceptually, or as query/storage reference). Lightweight adoption barrier: OSS indexers thin; Thrift ecosystem historically Haskell-centric.