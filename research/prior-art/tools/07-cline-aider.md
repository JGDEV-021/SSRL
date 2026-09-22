# Cline / Aider — Prior Art Note

> Research date: 2026-09-22 · Sources: aider.chat/docs (repo map), multiple 2026 head-to-head reviews (topaitracker, fast.io, devtoolsreview, pondero.ai), neural-llm blog.

## What they are
The two dominant **open-source, BYOK (bring-your-own-key) AI coding agents**:
- **Cline** — editor-first (VS Code, JetBrains, CLI via npm, SDK), approval-gated Plan/Act, MCP, subagents (read-only, parallel research, in v3.58+ `use_subagents`), browser automation, Kanban multi-agent.
- **Aider** — terminal-first, git-native, auto-commit-per-edit, architect (planner) + editor (cheap model) two-model routing.

## The one architectural artifact SSRL must absorb: **Aider's repo map**
> "Aider builds a concise map of the repository: important classes and functions with types and signatures... For larger repos, Aider ranks files with a graph of dependencies and fits the most relevant symbols into a token budget (`--map-tokens`)." (aider.chat docs)

Mechanics (from docs + independent analyses):
- Tree-sitter parse of every supported file at ~session start → extract top-level symbols → **graph-rank (PageRank-like) by inbound reference count** → a **token-budgeted ranked map** is placed **in the system prompt**, refreshed as files change.
- The model sees "the shape of the repo" before reading any file. Precise symbol/paths (`/add file.ts`) scope context explicitly; *everything else is off-limits for edits*.
- Effects reported: fewer grep round-trips, lower rate of **invented function names/imports** on legacy codebases (>50k LOC); eta on semantic-map quality lower than full-file contexts but much cheaper.

Why it matters: **a deterministic, precomputed, rankable structural index — the cheapest possible "fact graph" — measurably reduces hallucinated cross-file references.** It is the empirical floor for SSRL's core bet (P1/P2 in the vision: facts first, hypotheses second). Aider shows that even *symbols+references, ranked, in a prompt* beats "grep on the fly"; SSRL generalizes this to a queryable, persistent, semantic-annotated layer.

Cline's contrast (on-demand tool-call context, no persistent map) is a live A/B of the same idea: reviewers consistently attribute Cline's extra round-trips and more context-hungry behavior to the absence of a precomputed map.

## Where they stop
- Repo map is top-level structure via grammar; **no cross-file flow, no impact analysis** beyond symbol-rank; **no meaning** (naming-based); no confidence/evidence model; map lives only inside the prompt, thrown away after session. Both are **action** tools (edit code), not comprehension surfaces.

## Relevance to SSRL
- Empirical support for **structural-first context > embeddings/text only** (see also Copilot "usages", Cursor's lack of edges, Cody's code graph).
- Aider's tech stack is directly reusable: **tree-sitter + a ranker** = W4 probe material; the repo-map format is a candidate for SSRL's "cheap facts" first slice (D-2/D-4).
- Architect/editor split & auto-commit-per-edit = candidate patterns for SSRL's *evidence recording* (change-sourced hypotheses), though these are tooling practices, not layer features.

## Licensing
Both open source (Apache-2.0 & GPL-family per repo metadata — verify exact identifiers at reuse time); API-metered (BYOK). Architecture is documented publicly; the repo-map idea is permissibly replicable.