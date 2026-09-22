# GitHub Copilot — Prior Art Note

> Research date: 2026-09-22 · Sources: docs.github.com (repository-indexing), code.visualstudio.com/docs/agents + microsoft/vscode-docs, learn.microsoft.com (Visual Studio Copilot context), github.blog (context handling & model routing, 2026-06).

## What it is
The default AI coding assistant (autocomplete + chat + agent mode) across VS Code/Visual Studio/JetBrains, backed by GitHub's repo indexing.

## How context works (the important part for SSRL)
- **Repository indexing**: builds a semantic code search index (embeddings capturing "patterns and relationships"). GitHub repos get a **remote index** (built once, kept up to date, seconds after new conversation); local/non-GitHub repos get a local index (VS Code advanced local index up to ~2500 files; beyond that a basic index; local advanced index needs manual enable elsewhere). Remote index covers only *committed* state — uncommitted changes handled by hybrid: remote index + reading current file content from editor. Initial remote index can take ~60s; large repos slower.
- **Agent tool set** (VS Code Copilot agents): semantic search `#codebase`, text search, grep, file search, **usages** (find-refs/implementations/definitions — the *structural* tool), list directory, read file; iterative "gather context the same way a developer would"; can search other GitHub repos (upstream APIs). The agent decides which tools to invoke and re-searches until it "has a good understanding".
- **Intent detection in Ask/Edit modes**: they decide automatically whether workspace context is needed.
- **Context hygiene**: `files.exclude`/`.gitignore`/`search.exclude` prunes noise; docs warn every grep hit becomes context (noise). **Compaction** (`/compact`, summarize) frees context window; references dropdown shows what Copilot actually cited.
- **Efficiency (2026-06 blog)**: prompt caching (prefix reuse), **tool search** (load tool schemas on demand), **cache-aware model routing** (switch models only at cache boundaries).

## Where comprehension stops
- Understanding is **emergent per-session agent exploration**: there is **no persistent knowledge artifact**. The index is text/semantic vectors (meaning similarity, not relationships — same limit as Cursor's; "usages" is the only structural tool and it's linear symbol navigation, not a queryable graph).
- Index freshness has explicit holes (committed-state remote index; uncommitted local hybrid).
- No confidence/evidence labeling of answers. No durable "how the system works" model across sessions/teams.

## Relevance to SSRL
- Copilot/VS Code define the **user-visible baseline** for H1 (ask-the-codebase): this is what SSRL's Q&A must beat on were groundedness the metric.
- The **"usages" = symbol-reference navigation** is the extent of structural awareness; there is no call-graph/cross-file impact layer → SSRL's fact graph distinguishes it.
- Index staleness and context-window hygiene are live Shopify-scale problems SSRL's derivation/continuity (P4/P5/P8) are designed to solve.

## Licensing / constraints
Proprietary SaaS subscription; **no embeddable components**. The indexing/agent behavior is documented openly (vscode-docs, github blog) → useful design reference only. Notably: remote indexing uploads code snippets to GitHub (policy-gated; "Semantic indexing for non-GitHub repos" off by default for orgs) — a data-governance constraint SSRL (self-hostable layer) structurally avoids.