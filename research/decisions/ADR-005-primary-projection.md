# ADR-005 — Primary Projection (RN-1): Grounded Q&A First, Living Narrative Co-Surface

- Status: **Accepted** (maintainer sign-off, 2026)
- Additional status note: ADR-001/002/003/004/006/007 also **Accepted** alongside (all ratified, no objections raised at sign-off).
- Decides: `docs/requirements.md` RN-1 = RQ-2 / architecture D-1
- Evidence: W1 (literature), W2 (prior art), W3 (discourse), W4 (probe)

## Context

RQ-2 asks which surface gives developers the best comprehension with the least friction. SSRL holds this open as RN-1 because the whole product shape (integration surface ADR-006, enrichment quality, evaluation design) depends on it.

## Decision

**Primary projection: H1 — grounded on-demand Q&A** ("ask anything about the system; answer with grounded facts + evidence + confidence").

**Co-primary lived surface: H3 — living narrative**, offered as an on-demand, structure-aware report (system story updated from the fact layer), *not* as a default route.

**H4 (graph) and H2 (zoom) are demoted to supporting projections** — available, never the default path.

The Q&A answers are **hypotheses-first**: every answer identifies its confidence, splits *facts* (off the structural layer, confidence 1.0) from *inferred semantics* (hypotheses, calibrated confidence), and always carries evidence links to `file:line`. This is the RQ-3 mechanism — it is a core part of the projection, not a decoration.

## Evidence

### W1 supports Q&A + falsifiable grounding
- Empirical comprehension behavior is **inquiry-driven** (Q&A-by-nature); a "Q&A projection" therefore matches how developers actually think, better than a static graph or zoom (W1).
- Deterministic structural validation is the single strongest hallucination corrector (Arafat 2025: zero hallucination under mechanical citation; FASE 2026: 100% precision AST-based checks). An answer channel that always validates against the structural layer is the most reliable place to demonstrate value.
- Holtzblatt's task/comprehension distinction (W1) maps cleanly: Q&A covers both execution-style ("what calls X?") and understanding-style ("why does this exist?") questions, both served — at different confidence — off the same layer.

### W2 supports Q&A trajectory; refutes graph-first
- The market has converged on **Q&A-as-interface**: Copilot, Cursor, Claude Code, and Cline all expose natural-language questions as their primary UX (W2). Sourcetrail's graph-first death (2021) is a direct refutation of H4-as-primary (W2).
- BUT: current tools answer **without an explicit fact/hypothesis split**, without a persistent, structured claim abstraction, and without confidence calibration — each prompt re-reasons from scratch. That is exactly the gap SSRL's Adapter (FR-3–4) fills.
- Aider's **deterministic repo map** proves cheap structural grounding measurably reduces invented symbols (W2) — the mechanism H1/Q&A needs already exists in the open.

### W3 supports the demand, calibrated against slop
- The dominant real-world complaint is **ungrounded, context-less AI answers** ("AI slop", "confidently wrong", "doesn't know the repo") — the exact failure mode a fact/hypothesis Q&A projection with evidence addresses (W3).
- The gap is real and felt; the claimed differentiators of current products are **speed/UX, not grounding** — so grounding is an open competitive space (W3).

### W4 constrains the implementation, not the choice
- Facts are **free** (0.6 s on 31 files; 3.3 s on 122 files; 100% parse) — so a Q&A answer can always be backed by real structure. The projection's cost is in *which hypotheses need LLM* (RN-4 already limits that), not in extraction.

## Reconciliation of H3/H4/H2
- **H4 (graph)** — refuted as primary (Sourcetrail failure, W2; graph is `supporting` — "who calls X?" is a query, not a surface). Graph remains available *inside* answers when it's the clearest evidence widget.
- **H2 (zoom)** — a navigation mode, not a comprehension engine; folded into Q&A (answers can drill from system→module→function in one thread) and the supporting projection list.
- **H3 (living narrative)** — **kept as co-primary**, because: (a) W2 finds no credible incumbent (maintainable, code-derived system story is uncontested space), and (b) it doubles as the layer's **self-demonstration artifact** (Phase 9). Its risk (staleness, bloat) is controlled by making it on-demand and diff-based, never an always-on artifact.

## Consequences

- **Positive:** empirically grounded primary surface (RQ-2's likely answer), cheapest-to-validate hypothesis (the probe already provides the fact basis), strongest alignment with dominant UX and distortion-free evaluation (W1's comprehension tasks can be phrased as questions).
- **Negative / risk:** Q&A expectations are set high by existing chat-AIs (users will compare to Copilot/Cursor anyway); the projection must *win on evidence and structure*, not on fluency — a choice that favors the fact layer (SSRL's differentiator). Risk is mitigated by grounding-guaranteed answers (NFR-2) and by explicitly not competing on chat quality.
- H1-first shapes ADR-006 (CLI + MCP) and the evaluation design (RQ-1 measured as Q&A accuracy-with-evidence vs. garden-variety agent answers).

## Alternatives considered
- **H2/H4 primary:** rejected (zoom = navigation, graph = refuted by Sourcetrail). 
- **H3 primary:** rejected for default — narrative-as-default requires the richest hypotheses (RN-4 names naming+structure heuristics, which are limited); H3 should **report on** the layer, not be the layer's first test bed. Kept co-primary to keep the differentiation room open.