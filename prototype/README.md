# SSRL Prototype — V1 MVP

**SSRL = Semantic Software Representation Layer.** A deterministic, evidence-backed
representation of Python codebases: structural *facts* (confidence 1.0) plus
labeled semantic *hypotheses* (calibrated confidence), surfaced through a
grounded Q&A (H1) and a living narrative (H3).

Chosen directions locked in ADR-001…007 (Gate G1 passed). Zero runtime
dependencies — stdlib `ast` only (ADR-002).

## Status

```text
V1 MVP complete: extract -> enrich -> calibrate -> Q&A -> narrative -> CLI
Roadmap Phase 3 (facts), Phase 4 (Q&A projection), Phase 5 (semantic
enrichment), Phase 6 (confidence engine) all implemented for the MVP.
```

## Package layout (`prototype/ssrl/`)

| Module | Responsibility |
| --- | --- |
| `model.py` | Node/edge taxonomy, stable ids, `make_edge` (ADR-003) |
| `extract.py` | AST fact extractor: Repository/Module/Class/Function/Method, CONTAINS/IMPORTS/CALLS, incremental cache (D-8) |
| `semantics.py` | Hypothesis enrichment: Flows, Intents, Services/DomainConcepts (RN-2/RN-3) |
| `confidence.py` | Calibration, `why`, `audit` (RQ-3 / FR-4) |
| `index.py` | In-memory index: find, callers/callees, imports/deps, entry points |
| `qa.py` | Grounded, deterministic Q&A with FACTS vs HYPOTHESES separation (H1, FR-6a) |
| `narrative.py` | Living narrative, generated at build-time (H3) |
| `cli.py` | `build|enrich|ask|why|narrative|audit|stats|json` (ADR-006) |
| `__main__.py` | `python -m ssrl ...` entry point |

## Quick start

```console
cd prototype
python -m ssrl.cli stats     <repo>            # fact-model stats
python -m ssrl.cli enrich    <repo> [--cache]  # build + hypotheses
python -m ssrl.cli ask       <repo> "who calls search"
python -m ssrl.cli why       <repo> func::db::save
python -m ssrl.cli narrative <repo>
python -m ssrl.cli audit     <repo>            # calibration table
python -m ssrl.cli json      <repo> --out art.json [--enrich]
```

Run tests (zero deps, stdlib `unittest`):

```console
cd prototype
python -m unittest discover -s tests -v
```

## Verified properties (MVP)

| Property | Evidence |
| --- | --- |
| Parse robustness | 100% parse on both corpora, 0 syntax errors (31 + 122 files) |
| Determinism (NFR-4) | Repeated runs produce identical nodes and edges (verified: doc_rag x2, jgpredictor x2, unit tests) |
| Traceability (NFR-2) | Every node lists `evidence: [{type, source: "rel.py:line"}]` |
| Fact confidence | Structural facts carry `confidence: 1.0`; hypotheses are `< 1.0` and labeled (FR-3/FR-4) |
| Incremental cache (D-8) | File-level sha256 cache: cold 0 hits → warm 31/31 from_cache, artifact identical |
| Call resolution | Same-module + cross-module (import-alias and attribute-prefix) linkage, labeled `resolution:` |
| Test suite | `unittest`: 33 tests green (extract, cache, semantics, confidence, index, qa, narrative) |

## Measured stats (V1)

### Facts-only (`build`/`stats`)

| Corpus | Files | Parsed | Errors | Nodes | Edges | Functions | Imports | Calls | Elapsed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `JG-CODE/doc_rag` | 31 | 31 | 0 | 244 | 679 | 204 | 227 | 209 | ~0.5 s |
| `jgpredictor` | 122 | 122 | 0 | 1117 | 2913 | 936 | 989 | 808 | ~1.2 s |

### Enriched (`enrich` — +hypotheses)

| Corpus | Nodes(+hyp) | Flows | Intents | Services/Domain |
| --- | --- | --- | --- | --- |
| `JG-CODE/doc_rag` | 306 | 10 | 48 | 4 |
| `jgpredictor` | 1316 | 1 | 174 | 24 |

## Artifact shape (ADR-003 — derived, regenerable)

```json
{
  "graph_version": "0.4",
  "nodes": [ { "id": "func::benchmark::bench", "type": "Function", "name": "bench",
               "confidence": 1.0, "evidence": [{"type": "parser", "source": "benchmark.py:82"}] },
             { "id": "flow::func::benchmark::main", "type": "Flow", "confidence": 0.88,
               "evidence": [{"type": "CallGraph", "weight": 0.88, "source": "linker"}] } ],
  "edges": [ { "source": "func::main::main", "target": "func::main::greeting",
               "relationship": "CALLS", "confidence": 1.0, "metadata": {"resolution": "same-module"} } ],
  "stats": { "...": "..." }
}
```

Node types: `Repository`, `Module`, `Class`, `Function`, `Method` (facts) +
`Flow`, `Intent`, `Service`, `DomainConcept` (hypotheses).
Edges: `CONTAINS`, `IMPORTS`, `CALLS` (facts) + `PARTICIPATES_IN`,
`SUPPORTS_INTENT`, `RELATED_TO` (hypotheses).
Ids are stable (`module::<id>`, `class::<mid>::<name>`, `func::<mid>::<name>`).

## Known limits (honest, V1)

- Call resolution is name/alias based — no type inference; `self.method()` and
  shadowed names resolve heuristically. Facts are exact; *linkage* is best-effort
  and labeled.
- Hypotheses come from naming/structure heuristics + call-graph evidence (RN-4).
  An LLM would only *propose* hypotheses; SSRL recalibrates with structural
  evidence — not implemented in the MVP (ADR-007).
- Flat-scope methods: two methods with the same name in different classes of the
  same module share a `func::` id; CONTAINS edges still attach them to the right
  class (documented limitation of flat func ids).
- `from . import X` relative imports resolve within the scanned root; package
  identity outside the root is unknown.
- No watch/regenerate-on-change loop yet; cache is manual via `--cache`.