# ADR-007 — Hypothesis Sources: Structure & Naming First, LLM Last

- Status: **Accepted** (ratified with ADR-005, 2026)
- Decides: `docs/architecture.md` D-5 / RN-4
- Evidence: W1 (hallucination & grounding), W2 (Aider repo map, Cursor), P7 (AI is worker, not oracle)

## Context

Semantic hypotheses (intents, flows, domain concepts) must come from somewhere. The options: heuristics (naming/structure), LLM proposals, or both.

## Decision

**Layered source priority for hypotheses:**

1. **Structural evidence first** (deterministic, free): call-graph shape, import topology, module boundaries, naming patterns — these are already extracted by the W4 probe at zero cost and carry the highest trust.
2. **Heuristics second:** naming conventions, comment/docstring signals, usage patterns.
3. **LLM last, and only as a *proposer*:** an LLM may *suggest* semantic labels (e.g., "this flow looks like purchase validation"), but its output is **always a hypothesis with explicit, low-default confidence**, never a fact (P2, P7), and never required for the fact layer or the first projection.

This is a standing rule (RN-4), not a one-time choice: any future semantic enrichment must respect the ordering.

## Evidence

- W1: hallucination studies show LLM output is **confidently ungrounded** ~60% on adversarial tasks (Dasu 2026) — while **deterministic structural validation is the reliable corrective** (Arafat 2025: zero hallucination with mechanical citation; FASE 2026 AST-based detection at 100% precision).
- W1: Yamaguchi (CPG inventor) concedes context/business-logic cannot be deduced from code alone — so *some* non-structural source is needed for meaning, but it must be labeled as hypothesis (exactly SSRL's epistemic rule).
- W2: Aider's repo map (**deterministic** tree-sitter + PageRank) measurably reduces invented symbols — the cheapest, most defensible hypothesis-source precedent.
- W2: every 2026 tool defaults to LLM-per-request reasoning with no persistence or confidence — SSRL's differentiation is precisely *not* doing that by default.

## Consequences

- **Positive:** hypotheses inherit the determinism/traceability of structure where possible; LLM dependence (cost, drift, hallucination risk) is minimized; RQ-4 (best source trade-off) has a clear baseline to test against.
- **Negative / risk:** purely structural heuristics may produce shallow semantics ("this module calls database stuff") — richer meaning may genuinely require LLM proposals for H1/H3 quality. The ordering permits LLM, it just never lets it be the sole or primary truth-source.
- Calibration (RQ-3) applies **only to hypotheses**, never facts.

## Alternatives considered

- **LLM-first (industry default):** rejected — contradicts P7, imports the documented grounding failure mode, and forfeits SSRL's epistemic differentiation.
- **Heuristics only:** considered for v1 fact+simple-label demo, but likely insufficient for the semantic quality H1/H3 need — hence "LLM last, permitted" rather than "LLM banned."