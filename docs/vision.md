# SSRL Vision

> The layer between software and understanding.

- Version: 0.2
- Status: Draft
- Audience: contributors, researchers, future SSRL developers

---

## 1. Why SSRL exists

For decades, the bottleneck of software engineering was *producing* software. Each generation of tooling drove that cost down: high-level languages, frameworks, IDEs, automated testing, and finally AI code generation.

Today, generating code with AI is nearly free. The bottleneck moved.

**The new bottleneck is comprehension.**

Teams routinely end up with codebases nobody fully understands. AI-assisted development accelerates the problem: it is fast to *produce* software and slow to *understand* it. The result is a widening gap between people who generate code and people who understand code.

### The comprehension gap

Three modes describe today's code producers:

| Mode | Use of AI | Understanding | Outcome |
| --- | --- | --- | --- |
| **AI SLOP** | Generates code blindly | None | Cannot judge, fix, explain, or trust the code |
| **AI DEV** | Generates code deliberately | Local, of what they wrote | Can judge and maintain their own output |
| **DEV** | Builds structure and logic themselves | Deep, systemic | Full control and the mental model of the system |

The leap from SLOP to DEV — and from AI DEV to DEV — is a leap in **understanding**, not in code generation.

**SSRL's mission: compress that leap.** Make the knowledge a senior engineer carries in their head — structure, intent, dependencies, risks, "why does this exist" — explicit, derived from code, and available on demand to anyone (human or AI) who needs it.

---

## 2. Thesis

> Software can be represented as a **semantic layer** — distinct from source code — that captures what the system is, how it behaves, and what it means, with enough fidelity and honesty that understanding becomes inexpensive.

Central claims:

1. **Understanding can be served, not just carried.** Code carries knowledge implicitly; a semantic layer makes it explicit and queryable.
2. **Representation is not output.** The value is the layer, not any single rendering of it.
3. **Honesty is structural.** Claims about meaning must be distinguished from claims about structure, and carry confidence plus evidence.
4. **It must stay in sync.** A representation that goes stale is misinformation.

---

## 3. Objectives

### Primary objective

Provide a semantic representation layer for software that lets developers — and AI agents — answer comprehension questions quickly, with evidence, without reading the entire codebase.

### Specific objectives

- **O1.** Extract deterministic structural facts from source code (modules, functions, events, calls, imports, dependencies).
- **O2.** Enable semantic interpretation over those facts (intent, flows, domain concepts, business meaning).
- **O3.** Attach explicit confidence and evidence to every interpretation.
- **O4.** Keep the layer continuously in sync with the code (incremental regeneration).
- **O5.** Resolve the primary interaction model through research and deliver it in a dev-friendly form.
- **O6.** Serve human developers and AI agents as first-class consumers.

---

## 4. Non-goals

SSRL is **not**:

- A replacement for source code. Code remains the source of truth; the layer is always derived, never authoritative.
- A documentation generator. Documentation is one possible output, not the product.
- A static analysis or security tool. SSRL complements CodeQL/Semgrep; it does not compete with them.
- A graph database, knowledge-graph product, or visualization tool. Graphs and views are projections.
- A new programming language or compiler.
- A promise of "perfect" semantics. SSRL never promises certainty; it manages uncertainty explicitly.

---

## 5. Design principles

- **P1 — Code is the source of truth.** Everything in the layer is derived from code and traceable to it. The layer never overrides code.
- **P2 — Facts and hypotheses never mix.** Deterministic facts and probabilistic interpretations are distinct categories, always labeled.
- **P3 — No claim without evidence.** Every hypothesis carries confidence, origin, and extraction method. "Why does SSRL believe this?" always has an answer.
- **P4 — Continuity by design.** Sync is incremental, automatic, and part of the core design — never a manual or scheduled afterthought.
- **P5 — Dev-friendly or it fails.** The bar is not "how powerful is the analysis" but "how little does it cost a developer to get value." Friction above value is death.
- **P6 — Projections are views, not the product.** The layer is the product; graphs, narratives, and dashboards are projections of it.
- **P7 — AI is a worker, not an oracle.** AI proposes hypotheses; evidence disposes. LLM output is never the source of truth.
- **P8 — Comprehension is the metric.** Success is measured by comprehension outcomes (speed, accuracy, confidence), not by artifact beauty or graph density.

---

## 6. What success looks like

- A developer on a fresh codebase reaches working comprehension in minutes, not days.
- An AI agent produces changes that respect the actual structure and intent of the system, not just its syntax.
- Understanding survives the original author leaving — or the model that generated the code being replaced.
- "Nobody knows" becomes a rare answer.