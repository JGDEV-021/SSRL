# Related Work — Research Leads

- Version: 0.2
- Status: Lead map — NOT a finished literature review

> This is a research **lead map** for roadmap Phase 1. It organizes the territory SSRL must study and records preliminary positions to be confirmed or overturned with evidence in the research phase. None of these notes are final; the actual literature review lives in `research/literature/` after Phase 1.

---

## How to use this document

Each area lists: why it is relevant, what to investigate, candidate references, and the question SSRL must answer about it.

---

## 1. Program analysis & intermediate representations

**Why:** The deterministic foundation of any extraction layer.
**Investigate:** AST, CFG, PDG, Code Property Graphs (CPG) — how Joern, CodeQL build them; tree-sitter's incremental parsing.
**Candidate refs:** *A Survey of Software Architectural Reconstruction*; Yamaguchi et al. on Code Property Graphs; tree-sitter docs.
**SSRL question:** What fractal facts are cheap and reliable, without committing to a heavyweight analysis stack?

## 2. Static analysis platforms

**Why:** Mature precedent for "code as queryable data."
**Investigate:** CodeQL, Semgrep, SonarQube — capabilities, query models, and their limits (structure-first, semantics-light).
**SSRL question:** What are these tools *not* answering that SSRL targets (why/exists/intent)?

## 3. Code search & navigation

**Why:** Baseline UX for "exploring a codebase fast."
**Investigate:** Sourcegraph, OpenGrok, grok — search, symbol navigation, usage graphs.
**SSRL question:** Where does symbol search stop being enough (comprehension, not just retrieval)?

## 4. Software architecture recovery

**Why:** Directly about reconstructing structure+intent from code.
**Investigate:** Clustering/clustering-based module recovery, architecture conformance checking, reflexion models.
**Candidate refs:** Murphy & Notkin on reflexion models; Duck et al. surveys.
**SSRL question:** Does recovery without explicit confidence create false confidence in developers?

## 5. Knowledge graphs, semantic web & ontologies

**Why:** Formalisms (RDF, OWL) for "knowledge about a domain," including software domains.
**Investigate:** Ontologies for program comprehension, semantic code graphs.
**SSRL question:** Which formal representation ideas transfer, without the schema rigidity that kills dev adoption?

## 6. Software knowledge graphs (research)

**Why:** Closest academic neighbor.
**Investigate:** Sourcetrail (UI-driven comprehension), research on code knowledge graphs.
**SSRL question:** Why haven't these gone mainstream? Adoption friction? Staleness? Value-per-effort?

## 7. Semantic code search & embeddings

**Why:** "Meaning-aware" retrieval.
**Investigate:** CodeBERT, CodeT5, embedding-based code search, faiss.
**SSRL question:** Do embeddings give comprehension or just similarity? (Hypothesis: retrieval ≠ understanding.)

## 8. RAG / GraphRAG for code

**Why:** Current mainstream approach to "AI understands my repo."
**Investigate:** Naive RAG vs GraphRAG on code; context-window limits; grounding and hallucination.
**SSRL question:** Does vector retrieval over source files substitute for structural/semantic representation? (Our thesis: no — it is retrieval, not a layer.)

## 9. LLMs for code understanding

**Why:** The tool every AI DEV already uses.
**Investigate:** Copilot, Cursor, Claude Code, Codex, Cline/Aider — how they claim "repo understanding," where they drift or hallucinate.
**SSRL question:** Can a semantic layer *ground* these tools and reduce unwarranted trust? (RQ-3)

## 10. Program comprehension research (psychology of SE)

**Why:** Comprehension has been measured in SE research for decades; SSRL's claims must use that evidence.
**Investigate:** Cognitive models (bottom-up/top-down comprehension), comprehension time metrics, eye-tracking studies of code reading.
**SSRL question:** How is "comprehension" actually measured, so SSRL's validation (Phase 9) is credible?

## 11. Repository intelligence / AI-native tooling

**Why:** Emerging product space (Glean, Sourcegraph Cody, GitHub Copilot Workspace, etc.).
**Investigate:** What "repo intelligence" products promise and how much is marketing vs grounded land.
**SSRL question:** Is there a real, unserved need — or is "ask the agent" already good enough for users?

## 12. Docs-as-code / living documentation

**Why:** Every "auto-doc" tool before SSRL died from staleness or low value.
**Investigate:** DocGen, Obsidian-style vaults, architecture decision records (ADRs), mkdocs.
**SSRL question:** What made previous auto-doc attempts fail, and does derived+synced representation avoid those failure modes?

## 13. Domain-driven design (DDD)

**Why:** A vocabulary (entities, events, aggregates, ubiquitous language) that already models domain meaning.
**Investigate:** Eric Evans' DDD; domain event modeling practices.
**SSRL question:** Can SSRL *auto-discover* the DDD-shaped structure that humans once hand-built?

## 14. Agent protocols (MCP and similar)

**Why:** AI agents are the most likely first real consumer.
**Investigate:** MCP spec, how Copilot/Claude tools consume context, tool/context limits.
**SSRL question:** What shape of context helps an agent most — and what evidence prevents over-trust?

## 15. Software knowledge preservation / archaeology

**Why:** "Understanding survives the original author/model."
**Investigate:** Software archaeology, knowledge retention in orgs, model-obsolescence risks.
**SSRL question:** Does a language-model-independent representation preserve knowledge where agents/models fail?

---

## Preliminary positioning

| System | Structure | Semantics | Trust/Evidence | Versioned | Dev-friendly |
| --- | --- | --- | --- | --- | --- |
| CodeQL | Yes | No | Partial | No | Medium |
| Semantic search | Partial | Partial | No | No | High |
| RAG/GraphRAG | No | Yes | No | No | Medium |
| Copilot/Cursor/Cody | Partial | Yes | Weak | No | High |
| Sourcetrail | Yes | No | No | No | High |
| **SSRL (target)** | Yes | Yes | Yes | Yes | **High** |

> These cells are *claims to test in Phase 1*, not conclusions — especially the **dev-friendly** column, which is the crux (NFR-1).

## Where SSRL sits

Complement, not replacement. Most existing systems answer *how the software works* or *where the code is*. SSRL's contested territory is **why it exists, what it means, with what confidence** — and doing it with so little friction that developers actually keep it.