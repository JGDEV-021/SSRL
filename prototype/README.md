# SSRL Prototype — V1 MVP + Phases 7–8

**SSRL = Semantic Software Representation Layer.** A deterministic, evidence-backed
representation of Python codebases: structural *facts* (confidence 1.0) plus
labeled semantic *hypotheses* (calibrated confidence), surfaced through a
grounded Q&A (H1) and a living narrative (H3).

Chosen directions locked in ADR-001…007 (Gate G1 passed). Zero runtime
dependencies — stdlib `ast` only (ADR-002).

## Status

```text
V1 MVP complete: extract -> enrich -> calibrate -> Q&A -> narrative -> CLI
Roadmap Phase 7 (lab integration: `watch`, continuous regeneration) and
Phase 8 (agent surface: MCP over stdio + CI impact report) complete (v0.6.0).
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
| `impact.py` | CI impact report: "what does this PR affect?" — modules, importers, callers, entry points, flows (Phase 8) |
| `watch.py` | Continuous no-manual-sync regeneration (Phase 7, NFR-3): stat-poll diff + D-8 incremental rebuild |
| `mcp.py` | Dependency-free MCP server over stdio (Phase 8, ADR-006 v1.5): `ask/why/narrative/stats/audit/impact` tools |
| `cli.py` | `build|enrich|ask|why|narrative|audit|stats|json|watch|impact|mcp` (ADR-006) |
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
python -m ssrl.cli watch     <repo> --enrich   # continuous regen (Phase 7)
python -m ssrl.cli impact    <repo> path.py [--git main]  # "what does this PR affect?" (Phase 8)
python -m ssrl.mcp           --repo <repo> --enrich      # MCP agent surface over stdio (Phase 8)
```

`watch` regenerates the layer whenever the corpus changes, re-parsing only the
delta (D-8 cache replays the rest); cache is on by default for this command.
`impact` maps changed files to affected modules, importers, breaking callers,
entry points and flows; with `--git BASE` it reads the diff from git for CI.
`mcp` speaks JSON-RPC 2.0 (newline-delimited) over stdin/stdout so MCP-capable
agents (Claude Code, Cline, Cursor) consume grounded answers with evidence:
`ask`, `why`, `narrative`, `stats`, `audit`, `impact`. Cache is on by default
(never touches the corpus).
See `REPORT-P8.md` for the scripted agent session and coherence check.

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
| Test suite | `unittest`: 59 tests green (extract, cache, semantics, confidence, index, qa, narrative, watch, impact, mcp) |

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
- `watch` re-parses only the delta per change; the D-8 cache is *single-version per
  file*, so reverting to a previously-seen file version re-parses it once (correct,
  just not replayed). Poll interval must be ≥ the regeneration time for back-to-back
  bursts (documented in `REPORT-P7.md`).
- Impact granularity is whole-module; MCP is stdio-only with a single repo context
  and a pinned protocol version (documented in `REPORT-P8.md`).