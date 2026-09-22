# Sourcetrail — Prior Art Note

> Research date: 2026-09-22 · Source: sourcetrail.com archive, GitHub `CoatiSoftware/Sourcetrail` (archived), Wikipedia.

## What it was
An open-source, cross-platform **interactive source explorer** (C++, Java, Python). Indexed source and built an **interactive dependency graph**; the primary UI was the graph with symbol navigation — the closest thing the market has produced to SSRL's H4 ("graph-first" comprehension surface).

## History (why it matters)
- Started 2016 as commercial product "Coati"; went **open source (GPL-3.0) in Nov 2019**; **archived/end-of-life Dec 2021**. ~16.5k GitHub stars; 16k stars at archive.
- Discontinuation reasons (from maintainer blog + repo discussion):
  - Multi-platform + multi-language + multi-build-system indexer maintenance is huge (Qt, LLVM-based indexers, Java SDK, per-environment config).
  - "Did not succeed as a commercial product."
  - No successor maintainer team found even with transfer to KDE/hosted umbrella considered.
- Origin anecdote: author spent 1 month to implement a feature he expected to take 1–2 hours in Chrome — motivation was exactly SSRL's *comprehension/change-impact* problem.

## What it delivered / where it stopped
- Inverse-dependency and call-tree navigation; a real graph surface for unfamiliar code.
- **Did not deliver meaning**: it was structure (defs, refs, calls), not semantics (behavior, intent, why). No hypotheses, no confidence, no evidence links.
- Single-tool, desktop UX; no agent/CI/LSP integration; index freshness was manual.

## Relevance to SSRL
1. **H4 graph-first as a primary product surface is high-risk.** The only pure-graph comprehension tool failed commercially and maintainably. Its failure was not the graph idea but the cost of a bespoke, compiler-grade, multi-language index with a standalone-product business model.
2. Validates SSRL's constraints: cheap parsers (tree-sitter, not LLVM), incremental derivation, a layer (not a standalone product), MCP/LSP integration, and hypotheses (not just structure).

## Licensing
GPL-3.0, archived, read-only. Not a reuse/embedding candidate; a design reference only.