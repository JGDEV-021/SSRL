# ADR-006 — Integration Surface: CLI First, MCP Second

- Status: **Accepted** (ratified with ADR-005, 2026)
- Decides: `docs/architecture.md` D-7
- Evidence: W2 (editor/agent protocol won); NFR-1

## Context

D-7 asked where SSRL plugs in: CLI, LSP/IDE, MCP, CI. W2 found the market settled on two surfaces: the **code editor/agent** (Copilot, Cursor, Claude Code, Cline) and the **agent protocol** (MCP).

## Decision

1. **v1 surface: a CLI** (`ssrl <repo>` → fact artifact / query) — this is the NFR-1 cold-start bet: minutes-to-first-value, zero config, works anywhere.
2. **v1.5 surface: MCP** — expose the layer as MCP tools/resources so any MCP-capable agent (Claude Code, Cline, Cursor) consumes grounded facts with evidence. This is the AI-consumer half of FR-7.
3. **LSP/IDE plugin and CI report: deferred** until after the primary projection (ADR-005) is implemented and validated.

## Evidence

- W2: "the integration surface that won was the code editor/agent protocol, not a standalone tool" — MCP is the open, license-free way to reach that surface.
- NFR-1: a CLI is the least-friction possible first contact; Sourcetrail's dedicated-IDE model (W2) was a maintenance liability SSRL should not inherit.
- FR-7 requires humans *and* AI as first-class consumers; CLI covers humans, MCP covers agents.

## Consequences

- **Positive:** no IDE-plugin maintenance for v1; MCP is an open protocol (W2: no licensing barrier); agent access is the most defensible early differentiator vs. human-only tools.
- **Negative / risk:** CLI-only means no in-editor experience at v1 — acceptable for research validation (comprehension experiments in Phase 9 can run entirely via CLI/outputs).
- MCP tool design must respect the evidence/confidence model (each answer carries provenance — RQ-3).

## Alternatives considered

- **LSP first:** rejected — LSP servers serve editors, not the comprehension projection; heavy to build correctly, and the projection (ADR-005) is not chosen yet.
- **CI bot first:** deferred as a *supporting* projection (impact report) — real demand (W1 §7.1 review-friction) but not the primary bet.