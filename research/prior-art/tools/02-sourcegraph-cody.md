# Sourcegraph / Cody / Amp — Prior Art Note

> Research date: 2026-09-22 · Sources: sourcegraph.com blog (How Cody understands your codebase; anatomy of a coding assistant; SCIP announcement), Sourcegraph docs (Cody context, Code Graph), sourcegraph.com/changelog/7-0, Wikipedia, devtoolsreview/other 2026 commentary.

## What it is
Sourcegraph = **Code Search** + code intelligence platform (indexes up to 100,000+ repos; precise cross-repo code navigation; historically LSIF, now **SCIP**). Cody = AI assistant on that platform (context-aware RAG answers, autocomplete, test generation). **Amp** = newer frontier agent product, spun off into its own company Dec 2025 (Quinn Slack/Beyang Liu). Sourcegraph is now run as a separate "code search" company with Cody Enterprise retained for existing enterprise customers only.

## How it works (technical, from engineering blogs)
- **Code Intelligence / Code Graph**: indexers produce symbol data (definitions, references, symbols, doc comments) via SCIP (Protobuf, human-readable string symbol IDs; ~5x smaller than LSIF; 10x faster indexing in their migration; incremental and cross-language goals). This is *mechanical structure*, not meaning.
- **Context fetching for Cody chat**: remote Sourcegraph Search (BM25-adapted ranking, query-understanding rewriting, keyword + entity/filename/symbol detection) + local IDE context (open files) + embeddings (either OpenAI text-embedding-ada-002 or Sourcegraph's own `st-multi-qa-mpnet-base-dot-v1`) → global re-rank → top-N snippets → prompt. Autocomplete uses tree-sitter intent detection + Jaccard similarity + cursor position (no embeddings — latency budget). They explicitly say embeddings are complementary (semantic match) to precise search (exact/structural match): "best of both worlds".
- **Cody "validates the output of the LLM"** per the FAQ/handbook (though the precise validation step is less documented).
- Code Graph feature in Cody context: analyzing structure/inheritance/relationships to find context — the "cross-file structural" retrieval W1 §5.5 also found to be the strongest grounding signal.

## Market events (2025-2026) — essential context
- Jun 25 2025: Cody Free/Pro signups stopped; **Cody Free/Pro + Enterprise Starter killed July 23 2025**. Only **Cody Enterprise** remains. Individuals were pointed at Amp (credits, at-cost pricing; Amp Enterprise $1,000 one-time for $1,000 usage, 50% above individual pricing — per Sourcegraph pricing page, verified 2026-03 by third party; sales-led).
- Dec 2025: Amp spun off to separate company; Sourcegraph remains code search + code intelligence under CEO Dan Adler.
- Sourcegraph 7.0 (Feb 2026) removals: **Deep Search replaces Cody in the browser**; Search Notebooks removed; "ownership" features simplified. Their own note: agent tool-calling (Sonnet 3.7-era) "made some problems disappear overnight" — but **they explicitly state enterprises still face code-understanding challenges that small-codebase tools don't see**. That sentence is the SSRL thesis in a vendor changelog.
- No public self-serve Cody tier in 2026; pricing is sales-led and unpublished.

## Where comprehension stops
Everything about "understanding" is per-request LLM reasoning over retrieved snippets. The SCIP code graph is deterministic but *symbolic only* — no meaning, no hypotheses, no confidence; it is infrastructure for RAG, not a comprehension surface. No persistent "what the system does" artifact anywhere in the product.

## Relevance to SSRL
1. **Independently validates the gap**: the incumbent code-intelligence vendor acknowledges enterprises still need code understanding their agents don't provide.
2. **Validates structural retrieval > vectors** for grounding (they combine; W1 §5.5 showed structural/cross-file edges dominate). Consistent with SSRL facts-first.
3. **SCIP is a useful interchange/consultation reference** for SSRL's symbol/definition/reference facts (though SSRL's schema is semantic, not just symbolic).
4. A warning for any "assistant as the product" strategy: the individual assistant market churned hard in a year; a *layer* is a more durable position (consistent with SSRL's architecture decisions).

## Licensing / constraints
- Sourcegraph is a **proprietary SaaS/platform** (Code Search, Cody Enterprise). The Cody harness is partially open source (sourcegraph/handbook + GitHub), but the platform is not releasably licensable for reuse. SCIP spec is open (sourcegraph/scip, Apache-ish). Treat as design references; not buildable-upon components for SSRL.