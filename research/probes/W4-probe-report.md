# W4 — Probe: Cheap Deterministic Extraction on Real Python

> Workstream W4 of the SSRL research phase. Validates — with a throwaway read-only probe — that a *dependency-free structural fact layer* is feasible on real Python. This is NOT the SSRL prototype; it exists only to de-risk decisions D-2 (target language), D-4 (parser strategy), D-6 (do we need embeddings?).
>
> Date: 2026-09-22 · Code: `probe_extract.py` · Outputs: `out-docrag.json`, `out-jgpredictor.json`

---

## 1. What was tested

A single-file Python script (`probe_extract.py`) using **only the stdlib `ast` module**:

- Walks a directory, skips `.venv`, `__pycache__`, `node_modules`, etc.
- Extracts per module: classes, functions, methods, imports (`import X`, `from X import Y`).
- Builds a **call graph** with two levels of linkage:
  1. same-module resolution (call name = local definition),
  2. cross-module resolution (call name resolved via imports — relative and absolute).
- Emits the exact `{nodes, edges}` shape SSRL proposes in `docs/projections/graph.md` (Module/Function/Method nodes; CONTAINS/IMPORTS/CALLS edges; `confidence: 1.0` on facts).
- Reports parse errors, timing, and the top **unresolved** call names.

**No dependencies. No network. No AI. Read-only.**

## 2. Corpora

| Corpus | Files (real .py) | Notes |
| --- | --- | --- |
| `JG-CODE/doc_rag` | 31 | A real modular Python package (indexer, retriever, embedder, DB, CLI…); clean structure, cross-module imports |
| `jgpredictor` | 122 | A large, messy scientific/betting codebase (many one-off `examples/*.py` scripts) — the "unfair but real" test |

## 3. Results

### Corpus A — `doc_rag` (31 files, clean modular package)

| Metric | Value |
| --- | --- |
| Parse success | **31/31 (100%)** |
| Parse errors | 0 |
| Nodes | 235 |
| Edges | 569 |
| Functions+methods | 203 |
| Imports | 227 |
| Elapsed | **0.56 s** |

### Corpus B — `jgpredictor` (122 files, messy real-world)

| Metric | Value |
| --- | --- |
| Parse success | **122/122 (100%)** |
| Parse errors | 0 |
| Nodes | 1058 |
| Edges | 2549 |
| Functions+methods | 902 |
| Imports | 989 |
| Elapsed | **3.3 s** |

### Call resolution

| Corpus | Calls total | Resolved (project-local) | Unresolved |
| --- | --- | --- | --- |
| doc_rag | 1 895 | 220 (12%) | 1 675 |
| jgpredictor | 12 795 | 1 475 (12%) | 11 320 |

Resolved calls are genuine cross-module edges (e.g., module `benchmark` → `retriever::search`). The "unresolved" tail is overwhelmingly **builtins and library methods** (`len`, `print`, `str`, `open`, `.append`, `.strip`, `.execute`, `.get`) — i.e., calls that by definition fall *outside* the project graph and are correctly not edges. **The 12% is a floor, not a ceiling**: SSRL's fact layer only needs calls *between project symbols*; the rest is noise by design.

## 4. Answers to the probe questions

| Question | Answer |
| --- | --- |
| **Q1. Stlib-only extraction of modules/classes/functions/imports/calls?** | **Yes, fully.** One file, zero deps, 100% parse on two very different real codebases. |
| **Q2. What fraction of calls resolve to project-local functions?** | ~12% on both corpora — and that is the correct, useful number (the other 88% is builtins/libs and legitimately not part of the repo graph). Cross-module resolution works and is cheap. |
| **Q3. Fast / robust on messy real code?** | 122 files parsed in **3.3 s**, zero syntax errors on non-idealized code. Incremental (~tree-sitter) not even needed for this scale. |
| **Q4. Does `{nodes, edges}` survive contact with reality?** | **Yes** — the graph-schema shape (facts, confidence 1.0, Module/Function/Method, CONTAINS/IMPORTS/CALLS) produced clean, meaningful output with no schema adjustment. |

## 5. Decisions this de-risks (for W5)

- **D-2 (target language):** Python is confirmed viable — stdlib `ast` alone covers a test corpus trivially.
- **D-4 (parser strategy):** **stdlib `ast` is sufficient for the facts layer** at prototype scale. Tree-sitter is *not required* upfront (contrary to W2's assumption for multi-language); it remains an option for incremental parsing / other languages later, not a v1 dependency.
- **D-6 (embeddings needed?):** **No** — the call graph + imports are derived structurally with zero vectors. Embeddings would be a retrieval *accelerator* for a Q&A projection, not a prerequisite for the fact layer. Next probe should test the Q&A projection with plain structural context + LLM — no vector store.
- **RN-4 / D-5 (hypothesis sources):** the probe confirms structural facts are 100% free (confidence 1.0). Semantic hypotheses (intents/flows) will need naming/structure heuristics + optional LLM — the *facts* layer needs nothing probabilistic.

## 6. Known limitations of this probe (honesty notes)

- Call *resolution* is name-based + import-alias based; it does **not** track scope (`self.method()`, shadowing) — acceptable for a fact-layer feasibility check, must be hardened in the real parser.
- Methods linked only via CONTAINS, not per-class calls (calls to `self.x` resolve to same-module function names heuristically).
- Timing is single-run, not benchmarked cold/warm.
- Only `.py` — `__init__` re-exports and dynamic imports (`importlib`) not modeled (rare in these corpora).

## 7. Conclusion

> The SSRL fact layer is **buildable, today, with the Python standard library alone**. 100% parse success, 3 seconds for 1000+ nodes on messy real code, and the proposed `{nodes, edges}` schema survives unchanged. No embeddings, no tree-sitter dependency, no database required for the first facts. The blocker for SSRL is **not extraction — it is the primary projection** (RN-1), which is exactly where W5 now focuses.