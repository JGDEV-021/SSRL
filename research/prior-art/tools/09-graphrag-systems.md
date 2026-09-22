# GraphRAG Systems — Prior Art Note

> Research date: 2026-09-22 · Sources: microsoft/graphrag repo README (status), arXiv 2404.16130, Microsoft Research blog (dynamic community selection), plus cross-link to W1 §5.

## What they are
Retrieval systems that pre-build **knowledge graphs of a corpus** (typically via LLM extraction of entities + relationships), traverse the graph at query time, and (optionally) cluster it into **community summaries** for global ("corpus-level") questions that block-matrix RAG handles poorly.

- **Microsoft GraphRAG "From Local to Global"** (Edge et al., arXiv:2404.16130, 2024): LLM-extracted KG → Leiden communities → hierarchical community summaries → "map-reduce" global answers. Beats vector RAG on comprehensiveness/diversity for global questions; ~"1M-token eval" claims; authors explicitly flag fabrication risk & limited domains.
- **Maintenance mode (as of 2026)**: microsoft/graphrag became **"largely in maintenance mode… won't be accepting new PRs or implementing new features"** — heavy indexing/token cost + niche value. This is a market signal: the commercial-grade version of this idea stagnated.
- **Optimization line**: "dynamic community selection" (LLM-rate community reports, ~77% token-cost cut) — GraphRAG's real economic problem is token spend, not retrieval quality.
- **The critical epistemic point (ties W1 §5.2)**: in so-called "RAG knowledge graphs," **every edge is an LLM hypothesis**, not a verified fact. No provenance cascade, no per-claim confidence, no deterministic backstop. For code, W1 §5.5 (Arafat 2025) showed the winning grounding recipe is *deterministic structure + mechanical citation checking*, not LLM-built graphs.

## Where they stop (vs SSRL)
- Graphs are **LLM-synthesized, one-shot, corpus-static** (no incremental derivation; rebuilding costs tokens).
- No separation of *facts* (deterministic edges like calls/refers/imports) from *hypotheses* (LLM meanings).
- No confidence/evidence journal; no "why did you believe this" replayability.
- Cost scales with corpus size & change rate (same staleness trap).

## Relevance to SSRL
- Reframes **D-5/D-6**: graph-first retrieval is neither necessary (it's one retrieval strategy among several) nor sufficient (LLM-built edges are ungrounded). SSRL's deterministic-facts-first design is the cheaper, honest alternative to GraphRAG's LLM-KG — and W4/W5 should treat "index cost + staleness" as a first-class KPI (GraphRAG's killer).
- Directionally supports **H1/H3**: when you do need global "what is this system?" answers, community-summarization is the same intent as SSRL's living narrative (H3) — but SSRL would source it from *derived hypotheses over facts*, giving the evidence trail GraphRAG lacks.

## Licensing
microsoft/graphrag — MIT. Reusable as reference/retrieval layer if ever needed (not anticipated for SSRL v1: cost+ungroundedness).