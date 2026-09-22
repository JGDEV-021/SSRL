# W2 — Prior Art & Market: How Existing Tools Actually Work

> Workstream W2 of the SSRL research phase. Goal (per `research/plan.md` §3-W2): analyze how existing tools actually work — why they do or do not deliver comprehension — and capture licensing/model constraints relevant to SSRL reuse. Everything below comes from live web research (2026-09): vendor docs, engineering blogs, official changelogs, GitHub repos. Facts are cited where it matters; unverified pricing is flagged.
>
> Companion to `../literature/w1-literature.md` (academic side). This file is the handoff to W5 (decisions).

---

## 1. The pattern across all tools (the one-liner that matters)

Every comprehension-adjacent tool in 2026 reduces to the same three-layer shape:

```
code → [index: syntax/symbol graphs, embeddings, or text] → [LLM layer: chat/agents "explain"]
```

- The **index** layer stores *mechanical facts* (definitions, references, invocations, imports, AST chunks) — never meaning.
- The **LLM** layer is where "understanding" is *supposed* to happen, per request, inside a context window.
- **Nothing persists comprehension.** No tool keeps a durable, queryable record of *what the system means that survives the session*. That is the exact hole SSRL occupies.

Supporting observations from this workstream:

1. **The tool that tried to be a pure comprehension surface (Sourcetrail) died.** Archived in 2021; maintainers could not sustain multi-language/multi-platform indexers. A branded "graph-first comprehension" product did not survive market contact.
2. **The company with the best code-understanding platform (Sourcegraph) gave up selling the assistant to individuals.** Cody Free/Pro killed July 2025; Cody is enterprise-only; the individual path is now Amp (frontier agent). Sourcegraph's own 7.0 notes say agent tool-calling "made some problems disappear overnight" — and their remaining hard problem is *code understanding in large enterprises*, which they acknowledge is unsolved.
3. **Cursor's entire index is a similarity map, not a structure.** Third-party teardowns are unanimous: embeddings store "looks like", not "calls/extends/implements"; there are no resolved edges; it cannot answer "who calls X?". The most popular coding tool on the market does not model relationships at all.
4. **The only persistent fact-layer at scale is Glean (Meta), and it stops at mechanical facts.** Glean stores typed, schema-defined, incremental, immutable facts — with a Datalog query language and derived facts — but it deliberately stores no meaning. It is the strongest validation of SSRL's *fact model*, and its language-onboarding cost is the cautionary tale for D-2/D-4.
5. **Chunked-RAG approaches (Copilot, Cursor, existing GraphRAG) treat staleness as a constant.** Indexes are rebuilt on demand or on ~3–5 min cycles; cost concerns dominate (GraphRAG itself is in maintenance mode). SSRL's incremental, derivation-based layer is the documented alternative.
6. **Documentation frameworks (Diátaxis) already encode the "meaning needs" SSRL's projections serve** — reference mirrors structure like a map; explanation answers *why*. H2/H3 are essentially automating what skilled docs authors do.

---

## 2. Per-tool notes (index)

| # | Tool | File | Comprehension delivered? |
|---|------|------|--------------------------|
| 1 | Sourcetrail | `tools/01-sourcetrail.md` | Graph exploration; died on maintenance |
| 2 | Sourcegraph / Cody / Amp | `tools/02-sourcegraph-cody.md` | Code Intelligence (SCIP) + RAG; agent shift |
| 3 | CodeQL | `tools/03-codeql.md` | Precise relational code facts; security lens; licensing |
| 4 | GitHub Copilot | `tools/04-copilot.md` | Agent-based on-demand search; no durable layer |
| 5 | Cursor | `tools/05-cursor.md` | Embeddings = similarity only; no resolved edges |
| 6 | Claude Code | `tools/06-claude-code.md` | Subagent context isolation; project memory via CLAUDE.md |
| 7 | Cline / Aider | `tools/07-cline-aider.md` | Aider repo map = cheapest structural layer |
| 8 | Glean (Meta) | `tools/08-glean.md` | The reference fact-store; mechanical facts only |
| 9 | GraphRAG systems | `tools/09-graphrag-systems.md` | LLM-built graphs; cost/fabrication limits (see W1 §5) |
| 10 | Docs-as-code (Diátaxis et al.) | `tools/10-docs-as-code.md` | Structured human docs; the "why" content SSRL automates |

Full per-tool notes: see `tools/`. The rest of this file is the synthesis for W5 decisions.

---

## 3. Synthesis → SSRL decisions

### RN-1 / RQ-2 — Primary projection

- **H4 (graph-first) as a primary product surface is empirically risky.** Sourcetrail (the pure graph comprehension IDE) is archived; Sourcegraph's code graph is infrastructure behind RAG, not the user surface. Cursor ships a graph-free embedding index and still wins on UX. If SSRL ships H4 as the primary surface, it inherits both Sourcetrail's maintenance problem and the "graph ≠ meaning" problem. **H4 remains the default challenger only because of prior-art strength; market evidence now argues against it as primary.**
- **H1 (grounded Q&A) is converging on every major vendor** (Copilot agent, Claude Code, Amp, Cursor, Cody Enterprise). This is the baseline SSRL must beat — and its differentiation (persistent, evidence-labeled layer) is precisely what none of them have.
- **H3 (living narrative) has an adoption-ready frame**: Diátaxis "explanation" + "reference" are recognized doc categories with proven demand; H3 automates exactly that content, kept in sync by the layer. Of the four hypotheses, H3 is the one with *no direct market competitor* — nobody ships a self-updating explanation of your codebase. Least contested space.

### D-2 / D-4 — Target language, parser strategy

- Tree-sitter is the de-facto parsing substrate (Cursor AST chunking, Aider repo map, Sourcegraph syntax search, Copilot intent detection). **SSRL should assume tree-sitter for the facts layer.** Glean shows the alternative (compiler-accurate per-language parsers) has a brutal onboarding cost; tree-sitter-wide incremental grammars are the cheap path and match W4 probes.
- **Incremental indexing is non-negotiable and proven** (Glean O(changes) stacked immutable DBs; Cursor Merkle-tree sync; Aider per-file map refresh). Staleness is the #1 killer of every index product (GraphRAG maintenance mode; Copilot index staleness notes). This directly validates SSRL P4/P5 (derivation, continuity).

### D-3 — Storage direction

- **Fact stores are, in the wild, either RDBMS + graph layers or typed fact DAGs** (Glean: immutable facts, RocksDB, Datalog query). SSRL's "stable model format + facts/hypotheses" is closer to Glean's design than to vector stores. **Vector storage is a retrieval accelerator, not a comprehension layer** (Cursor: no edges; Hallucination-era RAG studies). W1 §5 also shows vectors are the weak link for cross-file structure. → Weakens D-6 "vector necessity".
- Sourcetrail + Glean + Sourcegraph all confirm: **the schema is the hard part**, not storage. Glean explicitly lets each language define its own schema with language-neutral abstractions derived on top — same shape as SSRL's core concepts layer.

### D-5 — Hypothesis source (RN-4)

- **LLM-only sources are the current default everywhere and demonstrably ungrounded**: cursor embeddings trained on agent traces still answer "where is X" via look-alike semantics; Cody validates + thresholds generation; Aider REPO MAP (deterministic tree-sitter + PageRank) is the cheapest hypothesis source and measurably reduces invented symbols on legacy code. → Supports *structure/naming first, LLM last* (SSRL default).
- Derived-fact machinery exists in Angle (Glean): rules derive new facts from base facts with **ownership propagation across stacked DBs** — a procedure SSRL can map directly onto "hypotheses derived from facts, with evidence links".

### D-6 / D-7 — Vector necessity, integration surface

- D-7: **the integration surface that won is the code editor/agent protocol, not a standalone tool.** Copilot, Cursor, Claude Code, Cline all live in the editor; agents extend via MCP (Claude Code, Cline, Cody agentic MCP). SSRL should expose the layer over **MCP / LSP** (agent-facing and IDE-facing), consistent with Phase 8's "agent protocol like MCP". Cody's own docs: MCP tools only, admins opt-in — a practical SSRL integration constraint to honor.

### Licensing / model constraints (required by plan §3-W2)

- **CodeQL (GitHub CodeQL Terms, per-user license, NOT OSI OSS):** free for *academic research*, demonstration, and OSS codebases on GitHub; **cannot generate databases for CI/CD or analyze non-OSS codebases without GitHub Advanced Security** license; no reverse engineering, no hosted-service offering. → CodeQL is usable as a research reference and for validation queries on open projects, but is **not embeddable** in a product that serves private codebases. Do not build on it. (SSRL's own layer must be permissively licensed to be embeddable.)
- **Glean (Apache-2.0, facebookincubator):** open source; Angle query language; SCIP/LSIF import for Go/Java/Rust/TS/Python. Reusable conceptually and as schema/derivation reference. Open-source parser support is thin (C++/Hack/Flow + SCIP/LSIF bridge), i.e., the *indexers* are the bottleneck, not the store.
- **Tree-sitter (MIT)** — freely embeddable, cross-language, fast, incremental. The safe foundation.
- **MCP (open protocol)** — no licensing barrier for the agent-facing surface.
- **Copilot/Cursor/Claude Code/Amp:** subscription/API-metered SaaS; no components to reuse; their behavioral details (indexing cadence, tool lists) are open-source documented in places (Cody harness open-source, VS Code Copilot docs) and reusable as design references only.
- **Aider / Cline:** open source (Apache-2.0-ish per repo heuristics); Aider's repo-map approach is documented and could be replicated; both are terminal/IDE agents, not sources of indexing components.

---

## 4. What this means for the SSRL thesis (inputs to W5)

1. **Confirmed gap:** the most advanced tools model code as *text similarity + mechanical symbols*; "understanding" is re-derived per request by an LLM and then discarded. No persistent semantic layer exists in the 2026 market. (Strengthens the position paper's core claim.)
2. **Confirmed feasibility:** deterministic fact extraction at scale, incrementally, with derived facts and queries, is proven by Glean at Meta scale. SSRL's "facts first, hypotheses second" is buildable with MIT components.
3. **De‑risked by the market:** graph-first-as-surface failed (Sourcetrail); pure-RAG indexes lack structure (Cursor); LLM-only grounding is the known failure mode (W1: hallucination + cost). SSRL's bet — cheap deterministic facts + labeled hypotheses + persistent layer — has no direct incumbent.
4. **Constraint discovered:** CodeQL-style proprietary terms mean SSRL must be its own, permissively-licensed fact layer, exactly as the architecture docs already assume.

---

## 5. Open items / follow-ups for W2 continuation (optional)

- Verify Aider/Cline license identifiers precisely from their repos before any reuse claim.
- Try tree-sitter incremental parsing on the W4 target language (Python) — feasibility gate for D-4.
- If needed, exercise the CodeQL academic-research license on an open repo to harvest query patterns for SSRL's own fact queries (allowed for research, not for product).