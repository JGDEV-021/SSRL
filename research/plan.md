# SSRL Research Plan (Phase 1)

- Version: 0.2
- Status: **Executed (W1–W4 complete, W5 ADRs delivered) — Gate G1 pending ADR-005 sign-off**

> Purpose: gather evidence to (1) validate that SSRL addresses a real problem, (2) resolve the **primary projection** (RN-1), and (3) de-risk architecture decisions (architecture D-1…D-8) — *before* any implementation code is written.

---

## 1. Research questions

### RQ-1 — Value
Does a semantic representation layer measurably improve code comprehension compared with source-only reading (and with current agent-based Q&A)?

### RQ-2 — Interaction (the crux)
Which projection, as the **primary** interaction, gives developers the best comprehension with the least friction?

### RQ-3 — Trust
Does explicit confidence + evidence reduce unwarranted trust and hallucination in AI-assisted code reasoning?

### RQ-4 — Sources
Which hypothesis sources (heuristics, structure, naming, LLM) give the best confidence-vs-cost trade-off?

### RQ-5 — Model
Which semantic concepts and schema survive contact with real code — and which are noise?

---

## 2. Hypotheses for RQ-2 (primary projection)

| ID | Hypothesis | Claim to test |
| --- | --- | --- |
| **H1** | On-demand comprehension | "Ask anything about the system, grounded answers with evidence" is the highest-value primary surface |
| **H2** | Progressive semantic zoom | "System → subsystem → module → line" drill-down comprehension is the highest-value surface |
| **H3** | Living narrative | The self-updating story of how the system works is the highest-value surface |
| **H4** | Graph-first | The graph itself is the primary surface (default challenger, has the strongest prior art) |

The graph (H4) and agent-context/CI surfaces are also investigated — but as **supporting**, not primary, unless evidence says otherwise.

---

## 3. Workstreams

### W1 — Literature & papers
Study prior work on: software comprehension measurement, program representation (AST/CFG/PDG/CPG), software knowledge graphs, architecture recovery, code retrieval, GraphRAG, LLM-code grounding.

Output: notes + summaries in `research/literature/`.

### W2 — Prior art & market
Analyze how existing tools actually work: CodeQL, Sourcegraph, Sourcetrail, Copilot, Cursor, Claude Code, Cline/Aider, Glean/Cody-class products, GraphRAG systems, docs-as-code tools. Understand *why* they do or do not deliver comprehension. Include licensing/model constraints relevant to SSRL reuse.

Output: per-tool notes in `research/prior-art/`.

### W3 — Discourse & practitioners
Mine forums and communities for real comprehension pain points: Hacker News, r/programming, r/ExperiencedDevs, Lobsters, dev.to, GitHub discussions, X threads on "AI slop" / "context loss" / "repo understanding".

Goal: collect concrete failure stories to validate the comprehension gap and the three AI modes (AI SLOP / AI DEV / DEV).

Output: annotated findings in `research/discourse/`.

### W4 — Experiments with real repositories (read-only)
Run small, throwaway probes (not the SSRL prototype) on real codebases — e.g., a Python project — to test cheap extraction feasibility: module structure, function/event discovery, call graphs using existing tools (Python stdlib `ast`, grep-level heuristics). This de-risks D-2/D-4/D-6 with hard data.

Output: probe reports in `research/probes/`.

### W5 — Synthesis & decisions
Consolidate W1–W4 into a decision record: primary projection (RN-1), target language (D-2), storage direction (D-3), parser strategy (D-4), hypothesis source (D-5), vector necessity (D-6), integration surface (D-7).

Output: ADRs in `research/decisions/` + updated requirements/architecture docs + paper update.

---

## 4. Sources (seed list, not exhaustive)

- Papers: SSRL-related (Code Property Graphs; architecture recovery surveys; comprehension-measurement studies; GraphRAG papers).
- Tools to operate/read docs of: CodeQL, Sourcegraph, Sourcetrail, Semgrep, tree-sitter, Cursor, Copilot, Claude Code, Aider/Cline, MCP spec.
- Forums: hn.algolia.com for Hacker News, Reddit search, Lobsters, dev.to, GitHub Discussions.
- Repos for probes: any small open-source Python repo (or the author's own Python projects).

---

## 5. Deliverables

- `research/literature/`, `research/prior-art/`, `research/discourse/`, `research/probes/`, `research/decisions/` populated
- ADRs resolving RN-1, D-2…D-7
- Updated `docs/requirements.md`, `docs/architecture.md`
- Updated position paper (v0.3)
- **Gate decision record**: primary projection chosen *with evidence*

---

## 6. Gates

### Gate G1 — Evidence enough to write code
Research Phase 1 reaches **G1** when:

- Primary projection resolved (RN-1 → becomes FR-6 concrete).
- Target language + parser strategy + storage direction chosen.
- Comprehension benefit has at least correlational support from W2/W3/W4.
- Requirements and architecture docs updated to v1.0.

**No implementation code (parser, storage, UI) starts before G1. Prototype code lives only in `research/probes/` as throwaway experiments until then.**

After G1: prototype phase (roadmap Phase 3+).