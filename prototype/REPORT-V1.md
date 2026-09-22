# SSRL V1 MVP — Comprehensive Delivery Report

**Document status:** final — records the **V1 MVP snapshot** (`v0.4.0`, roadmap Phases 3–6.5).
**Status today:** Phases 7–9 are complete (prototype is `v0.7.0`) — see `REPORT-P7.md`,
`REPORT-P8.md`, `REPORT-P9.md`, `prototype/README.md` and `roadmap.md` for the current
state; the repository is git-tracked and published at
`https://github.com/JGDEV-021/SSRL` (V1 MVP committed as `8d24440`).
**Version covered:** `prototype/ssrl/__init__.py` → `__version__ = "0.4.0"`; graph artifact `graph_version = "0.4"`.
**Target of record:** the SSRL V1 MVP delivered under the author directive *"construindo, sem parar, todas as fases possíveis — V1 MVP pronta. Sempre anote tudo, sempre faça relatórios, não erre."*
**Language policy:** repository documentation in English; author conversation in Portuguese.
**Repo root:** `C:\Users\joaog\Downloads\SSRL`.

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Scope, constraints and working agreement](#2-scope-constraints-and-working-agreement)
3. [Research-to-code provenance (W1–W5, gates, ADRs)](#3-research-to-code-provenance)
4. [MVP architecture at a glance](#4-mvp-architecture-at-a-glance)
5. [Data model: graph v0.4](#5-data-model-graph-v04)
6. [Extraction engine (Phase 3)](#6-extraction-engine)
7. [Incremental cache (D-8)](#7-incremental-cache-d-8)
8. [Semantic enrichment (Phase 5)](#8-semantic-enrichment)
9. [Confidence & evidence engine (Phase 6)](#9-confidence-and-evidence-engine)
10. [In-memory index](#10-in-memory-index)
11. [Grounded Q&A projection — H1 (Phase 4)](#11-grounded-qa-projection-h1)
12. [Living narrative projection — H3](#12-living-narrative-projection-h3)
13. [CLI integration surface (ADR-006)](#13-cli-integration-surface)
14. [Unit test suite](#14-unit-test-suite)
15. [Validation on real corpora](#15-validation-on-real-corpora)
16. [Bugs found and fixed during the build](#16-bugs-found-and-fixed-during-the-build)
17. [Requirement traceability matrix](#17-requirement-traceability-matrix)
18. [Research hypothesis traceability](#18-research-hypothesis-traceability)
19. [Honest limitations](#19-honest-limitations)
20. [Reproduction commands](#20-reproduction-commands)
21. [Appendix A — Calibration audit dump (doc_rag)](#appendix-a--calibration-audit-dump-doc_rag)
22. [Appendix B — Q&A transcripts](#appendix-b--qa-transcripts)
23. [Appendix C — Sample artifact fragment](#appendix-c--sample-artifact-fragment)
24. [Appendix D — Definitions and glossary](#appendix-d--definitions-and-glossary)

---

## 1. Executive summary

SSRL (Semantic Software Representation Layer) went from a research program with a frozen
spec to a **working V1 MVP** in one continuous build session. The MVP is a single
dependency-free Python package (`prototype/ssrl/`, 10 modules, ~1,540 lines) that
implements the full pipeline conceived in the roadmap:

```
source code  ──extract──▶  facts (deterministic, conf 1.0)
                           │
        ──enrich──────────▶  hypotheses (conf < 1.0, labeled, evidenced)
                           │
        ──calibrate───────▶  adjusted confidence for every hypothesis
                           │
        ──H1 Q&A──────────▶  grounded, instruction-free question answering
        ──H3 narrative────▶  living prose report, never stale
        ──CLI─────────────▶  build | enrich | ask | why | narrative | audit | stats | json
```

**Headline numbers (measured, reproducible):**

| Corpus | Files | Parse | Nodes | Edges | Functions | Imports | Calls | Flows | Intents | Svcs/Domain | Elapsed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `doc_rag` | 31 | 31/31 (0 err) | 244 | 679 | 204 | 227 | 209 | 10 | 48 | 4 | ~0.5 s |
| `jgpredictor` | 122 | 122/122 (0 err) | 1117 | 2913 | 936 | 989 | 808 | 1 | 174 | 24 | ~1.2 s |

- **Determinism (NFR-4):** verified twice per corpus — identical node- and edge-id sets across runs, fresh and cache-warm.
- **Zero dependencies (ADR-002):** only stdlib `ast`, `hashlib`, `json`, `argparse`, `collections`, `unittest`.
- **Test suite:** 33 unit tests green in ~0.2 s (stdlib `unittest`), against a synthetic fixture `tests/fixtures/pkgapp/`.
- **Scope of roadmap covered:** Phase 3 (facts), Phase 4 (H1 + H3 projections), Phase 5 (enrichment), Phase 6 (confidence) — all implemented for the MVP; Phases 1–2 already complete (research + frozen spec).
- **Correctness engineering:** **14 real defects** were found and fixed during the build (Section 16), several surfaced directly by the newly-written tests — the tests demonstrably earn their keep.

The MVP validates the SSRL thesis at minimum scale: facts are cheap and exact;
semantic hypotheses can be produced without any AI, honestly labeled and calibrated;
and the research-chosen projections (H1, H3) operate on real code with evidence
separated from inference.

---

## 2. Scope, constraints and working agreement

### 2.1 Goal (author directive)

> "construindo, sem parar, todas as fases possíveis — quero uma V1 MVP do SSRL pronta.
> SEMPRE ANOTE TUDO, SEMPRE FAÇA RELATÓRIOS, NAO ERRE"

Operationalized as: compress the executable phases of the roadmap (3–6) into one
complete, tested, verifiable MVP; log everything; publish reports (this report +
`BUILDLOG.md` + updated `README.md` + `roadmap.md` + `paper/SSRL-v0.3.md`).

### 2.2 Working agreement (continued from prior sessions)

| Constraint | Value | Evidence |
| --- | --- | --- |
| Language | Docs in English; conversation in Portuguese | file headers |
| Platform | Windows / PowerShell 5.1; Python 3.13.14 | environment |
| PowerShell quirks | `{`, `}` break shell parsing → use here-string `@"..."@`; set `$env:PYTHONUTF8='1'`; purge `__pycache__` on stale-bytecode suspicion | session notes |
| Committing | Never commit unless explicitly asked | standing instruction |
| Repo | `https://github.com/JGDEV-021/SSRL.git` (origin set; nothing pushed) | `git remote -v` |
| Dependencies | Zero — stdlib only (ADR-002) | no `pyproject.toml` deps |
| Corpora | Read-only: `C:\Users\joaog\Downloads\JG-CODE\doc_rag` (31 files), `C:\Users\joaog\Downloads\jgpredictor` (122 files) | NFR-5 |
| Temp work | `C:\Users\joaog\AppData\Local\Temp\opencode` | pre-approved |

### 2.3 What "V1 MVP" means here (and what it deliberately does not)

**In scope:** extract → enrich → calibrate → H1 Q&A → H3 narrative → CLI; incremental
cache; unit tests; verification on two real corpora; reports.

**Explicitly out of scope for the MVP:** watch/regenerate-on-change loop (Phase 7);
MCP/agent server (Phase 8); controlled comprehension experiments and statistical
calibration validation (Phase 9); H2 progressive-zoom drill-down; H4 graph navigation;
LLM hypothesis *proponents* (deferred per RN-4/ADR-007 — MVP is fully deterministic).

---

## 3. Research-to-code provenance

Every code decision in the MVP traces to an accepted research artifact. This is the
traceability backbone that the "research gates code" cardinal rule demands.

### 3.1 Lineage

| Workstream | Output | Status | Feeds |
| --- | --- | --- | --- |
| W1 | `research/literature/w1-literature.md` | complete | facts/hypotheses classes; structural grounding |
| W2 | `research/prior-art/w2-prior-art.md` + 10 tool monographs | complete | graph-first refuted; Q&A convergence; CLI/MCP |
| W3 | `research/discourse/w3-discourse.md` | complete | comprehension gap confirmed |
| W4 | `research/probes/W4-probe-report.md` + `probe_extract.py` | complete | stdlib `ast` feasibility (100% parse, 0 deps) |
| W5 | `research/decisions/ADR-001…007` + index | **all Accepted** | every MVP engineering choice |
| Gate G1 | sign-off on ADR-005 | **PASSED** | requirements/architecture frozen v1.0 |

### 3.2 The seven ADRs and their manifestation in code

| ADR | Decision | Code manifestation |
| --- | --- | --- |
| ADR-001 | Target language Python | corpora are Python; `ast` is the parser |
| ADR-002 | stdlib `ast` first, tree-sitter deferred | `extract.py` imports only stdlib |
| ADR-003 | storage = derived artifact `{nodes, edges}` (JSON), no DB in v1 | `build()` returns artifact dict; `json` CLI exports it |
| ADR-004 | no vectors/embeddings in fact layer / first projection | no embedding code anywhere |
| ADR-005 | **H1 grounded Q&A primary; H3 narrative co-primary; H4 graph supporting** | `qa.py` + `narrative.py` are the two projection surfaces |
| ADR-006 | CLI first, then MCP | `cli.py` is the complete integration surface |
| ADR-007 | hypothesis sources: structure/naming first, LLM last (proposer only) | `semantics.py` is 100% deterministic heuristics; zero LLM calls. Phase 9 later added the micro-LLM proposer (`ADR-008`), which only *proposes* capped hypotheses (`LLMProposal` ≤ 0.5) — never facts |

### 3.3 Frozen requirements ↔ MVP contract

`docs/requirements.md` v1.0 and `docs/architecture.md` v1.0 were frozen at Gate G1.
The MVP is the first implementation against that contract; Section 17 maps every
requirement to its implementation and verification.

---

## 4. MVP architecture at a glance

### 4.1 Package map

```
prototype/
├── ssrl/
│   ├── __init__.py     package marker; `__version__ = "0.4.0"`
│   ├── model.py        taxonomy, stable ids, edge factory (ADR-003)
│   ├── extract.py      AST facts + incremental cache + call linker (Phase 3)
│   ├── semantics.py    hypothesis enrichment (Phase 5, RN-4)
│   ├── confidence.py   calibration, why, audit (Phase 6, RQ-3)
│   ├── index.py        query primitives over the artifact
│   ├── qa.py           H1 grounded Q&A (Phase 4)
│   ├── narrative.py    H3 living narrative (Phase 4)
│   ├── cli.py          CLI commands (ADR-006)
│   └── __main__.py     `python -m ssrl ...` entry
├── tests/
│   ├── test_mvp.py             33 tests (stdlib unittest)
│   └── fixtures/pkgapp/        deterministic synthetic fixture (6 .py files)
├── BUILDLOG.md                 step-by-step build log (14 defects, decisions)
├── REPORT-V1.md                this document
├── README.md                   quick-start + verified properties + measured stats
└── ssrl_facts.py               legacy single-file prototype (superseded; kept for reference)
```

### 4.2 Data flow

1. `extract.build(repo, cache_dir?)` — walks `.py` files (skipping `SKIP_DIRS`/`SKIP_NAMES`), hashes each, parses with `ast`, emits fact nodes/edges, optionally reuses the cache, then `_link_calls` resolves call edges.
2. `semantics.enrich(artifact)` — deep-copies the artifact (facts never mutated) and appends hypothesis nodes/edges with evidence.
3. `confidence.calibrate/aggregate/why/audit` — pure functions over nodes/evidence; used by projections and CLI.
4. `index.Index(artifact)` — in-memory relational buckets (`_out`, `_in`) + name search.
5. `qa.answer(index, question)` — intent routing → fact/hypothesis builders.
6. `narrative.narrative(index)` — sections composed from stats + index primitives.
7. `cli` — thin argument dispatch over the above.

### 4.3 Dependency graph (module level)

```
cli ──▶ extract, semantics, confidence, index, qa, narrative
qa ──▶ index, confidence
narrative ──▶ index, confidence
semantics ──▶ model
extract ──▶ model
index ──▶ confidence
model ──▶ (none)
```

No module imports anything outside stdlib + the `ssrl` package.

---

## 5. Data model: graph v0.4

Defined in `model.py`; serialized by `extract.build` and `semantics.enrich`.

### 5.1 Node types

| Type | Class | Meaning | Confidence |
| --- | --- | --- | --- |
| `Repository` | fact | the analyzed root | 1.0 |
| `Module` | fact | one `.py` file | 1.0 |
| `Class` | fact | AST `ClassDef` | 1.0 |
| `Function` | fact | top-level `FunctionDef`/`AsyncFunctionDef` | 1.0 |
| `Method` | fact | function nested in a class | 1.0 |
| `Flow` | hypothesis | bounded `CALLS` chain from an entry point | calibration |
| `Intent` | hypothesis | semantic goal inferred from name/docstring | calibration |
| `Service` | hypothesis | orchestrator by naming signal | calibration |
| `DomainConcept` | hypothesis | domain role by naming signal | calibration |

`model.STRUCTURAL_NODES = {"Repository","Module","Class","Function","Method"}` — the five fact kinds.
`model.HYPOTHESIS_KINDS = {"DomainConcept","Flow","Intent","Service"}` — the four hypothesis kinds.

### 5.2 Edge types

| Relationship | Class | Semantics |
| --- | --- | --- |
| `CONTAINS` | fact | module→symbol, class→method, repo→module |
| `IMPORTS` | fact | module→module (resolved) or module→`import::...` (external placeholder) |
| `CALLS` | fact | caller→callee, with `metadata.resolution ∈ {same-module, cross-module}` |
| `PARTICIPATES_IN` | hypothesis | entry function→Flow |
| `SUPPORTS_INTENT` | hypothesis | function→Intent (also Service target) |
| `RELATED_TO` | hypothesis | module/class→DomainConcept |

### 5.3 Node shape (contract)

Every node is a dict with keys: `id`, `type`, `name`, `confidence`, `evidence` (list),
`metadata` (dict). Example function fact:

```json
{
  "id": "func::db::save",
  "type": "Function",
  "name": "save",
  "confidence": 1.0,
  "evidence": [{"type": "parser", "source": "db.py:34"}],
  "metadata": {"kind": "function", "scope": "module", "doc": "Persist a row."}
}
```

Example hypothesis node:

```json
{
  "id": "intent::func::db::save:persist",
  "type": "Intent",
  "name": "persist",
  "confidence": 0.76,
  "evidence": [{"type": "NamingPattern", "source": "save", "weight": 0.76}],
  "metadata": {"target": "func::db::save", "hypothesis": true}
}
```

### 5.4 Edge shape (contract)

```json
{
  "id": "e:ab12cd34ef56",
  "source": "func::services.store::store",
  "target": "func::db::save",
  "relationship": "CALLS",
  "confidence": 1.0,
  "evidence": [{"type": "call-graph", "source": "linker"}],
  "metadata": {"resolution": "cross-module"}
}
```

Edge `id` is ephemeral (`uuid4` truncated, `model.edge_id()`); edge **identity** is
`(source, target, relationship)` — deduplication and determinism checks use that triple,
not the ephemeral id.

### 5.5 Stable id scheme

`model.new_id(kind, *parts)` joins non-empty parts with `::`:
- `module::benchmark`
- `class::models::Item`
- `func::benchmark::main`
- `flow::func::benchmark::main`
- `intent::func::db::save:persist`
- `hyp::domainconcept::module:cli:entrypoint`
- `repo::<abspath-normalized>`

Deterministic from input path+name only — hence stable across rebuilds (NFR-4 basis).

---

## 6. Extraction engine

Module: `extract.py` (424 lines). Phase 3 of the roadmap, ADR-002 compliant.

### 6.1 Corpus walking

`index_corpus(root)` walks `os.walk`, prunes `SKIP_DIRS`
(`.venv, venv, __pycache__, node_modules, .git, dist, build, site-packages, .mypy_cache, .pytest_cache`),
skips `SKIP_NAMES` (`conftest.py`), keeps `*.py`, and sorts the result — **sorted iteration is
the first determinism guarantee** (NFR-4).

### 6.2 Per-module pass — `CollectVisitor`

A single `ast.NodeVisitor` produces all per-file facts with scope tracking:

- **Module** → docstring captured from the first `Expr/Constant[str]` statement.
- **ClassDef** → name, line, base names (`ast.Name` or `ast.Attribute.attr`).
- **FunctionDef / AsyncFunctionDef** → name, line, whether method (enclosing scope is a class),
  parent name (class name or "module"), and first-statement docstring.
- **Calls** → `(scope_name, callee_name, base_name)` triples. `scope_name` is the innermost
  function/method on the visitor stack (module-level calls → `None`). `base_name` is the
  root of an attribute chain (e.g. `models.validate(...)` → `base="models", name="validate"`;
  `self.foo.bar()` → `base="self"`).
- **Imports** → normalized triples `(kind, target, alias)`:
  - `import os` → `("import", "os", None)`
  - `from typing import Any` → `("from", "typing.Any", None)`
  - `from . import models` → `("from", ".models", None)` *(leading-dot rewrite — key defect fix, §16.8)*
  - `from ..db import save` → `("from", "..db.save", None)`

### 6.3 Module id

`module_id(rel_path)` strips `.py`, collapses `\` and `/` to `.`:
`data/frameworks/react-lua/bin/svg.py` → `data.frameworks.react-lua.bin.svg`.

### 6.4 Import edge desugaring

For each import triple the extractor decides the target node id:

| Pattern | Target | Example |
| --- | --- | --- |
| external, non-`from` | `import::<kind>:<target>` placeholder | `import::import:logging` |
| leading-dot target | `module::<resolved>` via `_resolve_local_import` | `from . import models` in `db.py` → `module::models`; in `services/store.py` `from ..db import save` → `module::db` |
| `from` with known base module | `module::<base>` | `from config import X` where `config.py` exists → `module::config` |
| `from` with known target module | `module::<target>` | `from db import X` → `module::db` |
| other | `import::from:<target>` placeholder | `from typing import Any` → `import::from:typing.Any` |

`_resolve_local_import(mid, target, "from")` implements relative semantics: leading dots →
strip `depth` package segments from `mid`, append the first remaining segment. Top-level
modules (depth ≥ len(mid.parts)) degrade safely to the bare segment (defect fix §16.9).

Line-number evidence for each import edge is resolved by scanning the AST for the matching
`Import`/`ImportFrom` node.

### 6.5 Fact emission (module, class, function, method)

Ordered, batch-append; evidence carries the exact `file:line` of each AST node.
Function/method CONTAINS parents:
- top-level → module node
- method → the class node, built as `f"class::{mid}::{parent}"` — must match `model.new_id("class", mid, name)` exactly (origin of defect fix §16.2, the `::` vs `:` bug).

### 6.6 Syntax-error handling

A file that fails `ast.parse` still produces a `Module` node with `metadata.parse_error
= {msg, lineno}` and `stats.parse_errors` incremented — the corpus is never silently
dropped (verified: 0 errors on both corpora, but the branch is covered by design).

### 6.7 Call linking — `_link_calls`

The linker runs after all modules are collected (so cross-module targets exist):

1. **`fn_local[(mid, name)]`** — index of every function/method by module+name.
2. **`import_targets[mid][alias_or_symbol]`** — import alias map per module:
   - `from X import Y [as Z]` → alias `Z or Y` → `(module_X, Y)`
   - `import pkg.mod` → `pkg.mod` → `(pkg, None)`
   - relative forms resolved through `_resolve_local_import`.
3. **`resolve_call(mid, name, base)`** — resolution order:
   - `name in BUILTINS` → skip (never a false edge). `BUILTINS` = `dir("__builtins__")` ∪ curated list (`print, len, open, ...`, exception types, `dataclass`, `asyncio`, dunders).
   - local same-module → `("same-module")`.
   - name is an import symbol → look up `(tmid, sym)` → `("cross-module")`.
   - **attribute base** is an import alias → `fn_local[(tmid, name)]` → `("cross-module")` *(defect fix §16.6)*.
4. **Caller node:** scope function if any (`fn_local[(mid, scope)]` first id), else the module node.
5. Dedupe via the `(source,target,relationship)` set; count `resolved`; count `unresolved` per name (builtins excluded).

**Measured resolution (doc_rag):** 209 call edges = 148 `same-module` + 61 `cross-module`.
**Measured resolution (jgpredictor):** 808 = 801 `same-module` + 7 `cross-module`.

### 6.8 Stats block

`build()` emits `stats` → `{files, from_cache, parsed, parse_ok, parse_errors, nodes,
edges, functions, imports, calls, elapsed_s}`. Enrichment later adds `hypotheses`
`{services_domain, flows, intents}` and refreshes `nodes`/`edges` counts.

---

## 7. Incremental cache (D-8)

### 7.1 Design

- **Key:** repo-relative file path (`rel`).
- **Validity:** content sha256 (first 16 hex chars) — hash-only, no mtime (mtime + hash was
  the working assumption; the MVP uses hash alone since it is both simpler and exact).
- **Payload per file:** `{digest, nodes, edges, extra}` where `extra` = `{imports, calls, docstring}`.
- **Versioning:** `CACHE_VERSION = 2` — incremented when the stored call triple shape changed
  (addition of `base`), so stale caches are safely ignored rather than corrupting output.
- **Filesystem:** a single `cache.json` per corpus under `~/.ssrl/cache/<repo-normalized>/`.

### 7.2 Cold vs. warm (measured)

```
$ python -m ssrl.cli stats <doc_rag> --cache     # cold
files=31 reparsed=31 ok=31 errors=0 from_cache=0 elapsed_s=0.529
nodes=244 edges=679 functions=204 imports=227 calls=209

$ python -m ssrl.cli stats <doc_rag> --cache     # warm
files=31 reparsed=0 ok=31 errors=0 from_cache=31 elapsed_s=0.380
nodes=244 edges=679 functions=204 imports=227 calls=209
```

Warm build ⇒ 31/31 modules replayed from cache (`reparsed=0`, `from_cache=31`), zero re-parses,
identical node/edge id sets to the cold build (determinism preserved through the cache path —
verified, §15.3). Note the label discipline added in defect fix §16.13: `reparsed` counts modules
actually parsed this run; `ok` counts healthy Module nodes (parse_ok) — both shown so a warm run
cannot be misread.

---

## 8. Semantic enrichment

Module: `semantics.py` (191 lines). Phase 5, honoring RN-4/ADR-007: **structural evidence
first, naming heuristics second, LLM last (never here).**

`enrich()` deep-copies the artifact (facts are never modified — test
`test_facts_untouched_by_enrich`), then appends hypothesis nodes/edges.

### 8.1 Service / DomainConcept — `SNIFF` naming patterns

Module/class basename (extension stripped) is matched against suffix regexes:

| Regex | Kind | Base conf | Label |
| --- | --- | --- | --- |
| `(service\|services)$` | Service | 0.86 | service |
| `(repository\|repositories\|store\|dao)$` | DomainConcept | 0.84 | repository |
| `(controller\|router\|endpoint)$` | DomainConcept | 0.84 | controller |
| `(manager\|engine\|pipeline\|flow)$` | DomainConcept | 0.80 | engine |
| `(model[s]?\|entity\|entities\|schema)$` | DomainConcept | 0.80 | model |
| `(util\|utils\|helpers?\|common\|base\|core)$` | DomainConcept | 0.74 | infra |
| `(config\|settings\|constants)$` | DomainConcept | 0.70 | config |
| `(db\|database\|storage\|persist)` | DomainConcept | 0.82 | persistence |
| `(cli\|cmd\|main\|runner\|bootstrap)$` | DomainConcept | 0.80 | entrypoint |

Evidence weight = the base confidence; edge `SUPPORTS_INTENT` (Service) or `RELATED_TO`
(DomainConcept). **Defect fix §16.10** is in this block (module-name segmentation).

### 8.2 Flow — `DOC_INTENTS`-independent BFS over CALLS

- Entry points: public functions with no caller edges, **sorted** (determinism).
- `bfs_flow(start, limit_nodes=12, depth=4)` — breadth- and depth-capped traversal over
  outgoing CALLS; a Flow needs ≥ 2 reachable nodes.
- Cap at 20 entry points (`entry_points[:20]`) — determinism of scale, not randomness.
- Confidence: `0.62 + min(0.15, 0.01*len(reach))`, capped at 0.9 → measured **0.88**
  for all doc_rag flows.
- Evidence: two `CallGraph` entries (entry + chain).

### 8.3 Intent

Per function: haystack = `name + " " + docstring`; matched against 5 conceptual tags:

| Tag | Regex | Conf |
| --- | --- | --- |
| validate | `valid\|check\|assert` | 0.78 |
| transform | `convert\|transform\|normalize\|clean\|parse` | 0.76 |
| persist | `save\|store\|write\|commit\|upsert\|insert\|update` | 0.76 |
| retrieve | `load\|fetch\|read\|query\|search\|get\|find\|retrieve` | 0.72 |
| compute | `calcu\|compute\|aggregate\|stat\|metric\|score\|rank` | 0.70 |

Best (highest-confidence) match wins; evidence `NamingPattern` weighted at the tag's
confidence; edge `SUPPORTS_INTENT`.

### 8.4 Measured hypothesis inventory

| Corpus | Service/Domain | Flows | Intents |
| --- | --- | --- | --- |
| `doc_rag` | 4 (`cli→entrypoint`, `config→config`, `db→persistence`, `textutil→infra`) | 10 | 48 |
| `jgpredictor` | 24 | 1 | 174 |

---

## 9. Confidence and evidence engine

Module: `confidence.py` (120 lines). Phase 6, grounding RQ-3 / FR-4.

### 9.1 Policy (conservative, documented in module docstring)

1. **Facts → 1.0 always**, regardless of any stored number.
2. **Hypotheses → clamped to [0.55, 0.95]**; no evidence ⇒ demoted to **0.5** ("guess").
3. **Source ceilings** — a hypothesis can never exceed its strongest evidence source:

   | Source type | Ceiling |
   | --- | --- |
   | `NamingPattern` | 0.9 |
   | `CallGraph` | 0.88 |
   | `Documentation` | 0.92 |
   | `parser` / `call-graph` | 1.0 |
   | `Structure` | 0.9 |
   | `LLMProposal` | 0.5 |

4. **Aggregation** — noisy-OR of source weights, then capped by the max source weight
   ("combined never exceeds the strongest single source"):

   ```
   aggregate([0.6 (NamingPattern), 0.5 (CallGraph)])
     weights = [min(0.6,0.9), min(0.5,0.88)] = [0.6, 0.5]
     noisy_or = 1 - ((1-0.6)*(1-0.5)) = 0.80
     comb = min(0.80, max(0.6,0.5)=0.6) = 0.6
   ```
5. **Calibration labels:** < 0.55 weak · < 0.75 moderate · < 0.95 strong · else very strong.

### 9.2 `why(node)` and `audit(nodes)`

- `why` returns a human-readable line: `[FACT] <id>: deterministic, confidence 1.0,
  evidence [...]` or `[HYPOTHESIS] <id> type=... confidence=... (note)` + one line per
  evidence source (type, weight, source).
- `audit` returns a sorted table of `{id, type, confidence, note, evidence_sources,
  is_hypothesis}` — printed wholesale by `ssrl audit` (full dump in Appendix A: 62 rows
  for `doc_rag`).

**Measured calibrated ranges (doc_rag):** Flows 0.88 (strong) · Intents 0.70–0.76
(moderate–strong) · DomainConcepts 0.70–0.82 (moderate–strong).

---

## 10. In-memory index

Module: `index.py` (191 lines). Deterministic query base shared by Q&A and narrative.

| Primitive | Behavior |
| --- | --- |
| `find(q, limit=20)` | exact name match → substring → prefix/suffix; case-insensitive; module keys use basename-without-ext |
| `node(nid)` | direct id lookup |
| `children / parents(nid, rel?)` | edge buckets filtered by relationship |
| `callers_of / callees_of(nid)` | CALLS neighbors, resolved to node objects |
| `imports_of(nid)` | module import edges; external `import::…` placeholders returned as synthetic rows |
| `imported_by(nid)` | reverse import edges |
| `deps_closure(start, hops=5)` | transitive closure over CALLS+IMPORTS (skips external placeholders) |
| `reverse_deps(start, hops=5)` | what depends on the given nodes |
| `module_summary(mid)` | classes / functions / imports of a module |
| `entry_points()` | public functions (no `_` prefix, no `test_` prefix, loc not under `tests/` or `test_*`) with **no CALLS targets** — test-scaffolding exclusion is defect fix §16.5 |

Buckets `_out`/`_in` are built in artifact edge order (deterministic by construction).

---

## 11. Grounded Q&A projection — H1

Module: `qa.py` (295 lines). Primary projection per ADR-005/RN-1/FR-6a.

### 11.1 Design principles

- **Deterministic, instruction-free routing:** no prompts, no model — a compact intent
  parser maps natural-language-style questions to fact queries.
- **Answer structure:** `{intent, target, facts, hypotheses, answer_text}` — every answer
  reports facts (conf 1.0) and hypotheses (calibrated) separately, per FR-6a.
- **Evidence links:** every "where" and module answer includes `file:line` locations from
  node evidence.

### 11.2 Intent inventory (14 intents + help)

| Intent | Trigger examples | Builder |
| --- | --- | --- |
| `callers` | "who calls X", "callers of X", "what calls X" | `_callers` |
| `callees` | "what does X call", "does X call", "callees of X" | `_callees` |
| `where` | "where is X", "where are X", "location of X" | `_where` |
| `summary` | "what does X do", "summary of X", "describe X", "about X" | `_summary` |
| `imports` | "imports of X", "what does X import" | `_imports` |
| `importers` | "who imports X", "X imported by", "imports by X" | `_importers` |
| `deps` | "dependencies of X", "what does X need", "X depends on" | `_deps` |
| `revdeps` | "what depends on X", "reverse dependencies of X", "needed by" | `_revdeps` |
| `entry` | "entry points", "where do I start", "public api" (+`BARE` map) | `_entry` |
| `functions` | "functions in X", "methods in X" | `_contained` |
| `classes` | "classes in X" | `_contained` |
| `flows` / `intents` / `services` | bare keywords | `_browse_hypotheses` |
| `help` | "help", "what can you do", "how do I use" | `_help` |

Matching is first-match in declaration order; regexes use capture groups so real names
match (defect fix §16.7 — the literal-`x` bug).

### 11.3 Target extraction

`_extract_target` removes stopwords (`what, does, do, call, calls, called, in, of, where,
is, are, module, function, import, dependency, entry, point, ...`) and returns the last
meaningful token; the Index then finds it (longest/first match rules in `Index.find`).

### 11.4 Dispatch

`_pick(hits, intent)` ranks `Function(0) < Method(1) < Module(2) < Class(3) < Repository(4)
< Flow(5) < Intent(6)` — functions win for call-related questions. `_dispatch` then routes
to the concrete builder. Hypotheses-browse intents short-circuit before entity lookup.

### 11.5 Sample answers (real, doc_rag)

See Appendix B for full transcripts. Highlights:

- `who calls search` → `Callers of search: _run_db, _cmd_search, search_for_context, build_context (4 facts)` — all with `benchmark.py:XX`/`cli.py:XX` evidence.
- `where is connect` → `Function connect defined at db.py:73 (confidence 1.0).`
- `what does indexer do` → module summary with 17 functions, 18 imports, module docstring.
- `imports of retriever` → 14 edges incl. external placeholders, `config.py`, `expand.py`, etc.
- `dependencies of indexer` → 7-node transitive closure with module names.
- Not-found path: `I couldn't find <x> in the index. Tip: ...` (tested).

---

## 12. Living narrative projection — H3

Module: `narrative.py` (104 lines). Co-primary surface (ADR-005), generated on demand from
the fact layer — **never a stale artifact** (NFR-3).

Sections emitted:

1. **Overview** — scale + parse health, straight from `stats`.
2. **Entry points** — first 20, each `name (id) — file:line`.
3. **Module map** — per module: docstring as purpose (up to 300 chars — real repos have
   real docstrings, incl. pt-BR like `doc_rag`), contained-symbol count, import count.
4. **Key flows** — top-15 Flow hypotheses with calibrated conf + note + entry + step count + evidence sources.
5. **Confidence & evidence** — hypothesis inventory counts + facts-vs-hypotheses reminder + RQ-3 caveat; footer: *"Narrative is a projection of the fact layer, not new knowledge; regenerate after each commit."*

Deterministic (sorted flows by confidence; module list is artifact order).

---

## 13. CLI integration surface

Module: `cli.py` (139 lines) + `__main__.py`. ADR-006 (CLI first); everything reachable as
`python -m ssrl <cmd> <repo> [--cache] [args]` or `python -m ssrl.cli …`.

| Command | Signature | Output |
| --- | --- | --- |
| `build` | `repo [--cache]` | JSON `stats` |
| `enrich` | `repo [--cache]` | JSON `stats` + `hypotheses` |
| `ask` | `repo "question" [--cache]` | grounded answer (facts + hypotheses blocks) |
| `why` | `repo <node-id-or-name> [--cache]` | evidence explanation |
| `narrative` | `repo [--cache]` | living narrative |
| `audit` | `repo [--cache]` | calibration table (sorted) |
| `stats` | `repo [--cache]` | one-line counts |
| `json` | `repo [--out F] [--enrich] [--cache]` | full artifact JSON (NFR-7) |

`load_artifact(repo, use_cache, enrich_ok)` normalizes the path, keys the cache under
`~/.ssrl/cache/<normalized-abspath>`, and optionally applies `semantics.enrich`.

**Important recent fix (§16.11):** `ask` now loads the **enriched** artifact, so
`ask "flows"` / `"intents"` / `"services"` actually returns hypotheses (previously 0).

---

## 14. Unit test suite

File: `tests/test_mvp.py`, fixture `tests/fixtures/pkgapp/`, runner:
`python -m unittest discover -s tests -v`. **33 tests, all green, ~0.2 s.**
*(Phases 7–9 later added `TestWatch`, `TestImpact`, `TestMCPServer`,
`TestLLMProposer` — current suite: **67** tests; see `REPORT-P7.md` /
`REPORT-P8.md` / `REPORT-P9.md`.)*

### 14.1 Fixture (`pkgapp/` — 6 files, deliberately small and deterministic)

| File | Purpose exercised |
| --- | --- |
| `main.py` | entry point; same-module call `main → greeting`; private helper |
| `db.py` | module docstring; `from . import models` relative import; cross-module call `save → models.validate` (attribute prefix) |
| `models.py` | class `Item` with method `validate` (class→method CONTAINS); top-level `looks_valid` |
| `services/store.py` | `from ..db import save` (double-dot relative import); orchestration flow (entry point) |
| `__init__.py`, `services/__init__.py` | empty modules |

### 14.2 Test inventory (by class)

| Class | Tests | What each verifies |
| --- | --- | --- |
| `TestExtract` | 9 | 0 parse errors & 6 files; node taxonomy present; class `Item` exists and CONTAINS its `validate` method; local relative import resolves to `module::models`; cross-module CALLS edge `func::db::save → func::models::validate` exists; every fact confidence == 1.0; every node has parser evidence `file:line`; determinism of node-set and edge-set across two builds; **exactly one repo→module CONTAINS edge per module** (regression for defect §16.12) |
| `TestIncrementalCache` | 1 | cold: 6 parsed/0 cached; warm: 0 parsed/6 cached; identical node/edge content across cache boundary |
| `TestSemantics` | 4 | intents generated & confidence in (0,1); a Flow exists with entry `func::services.store::store` whose steps include both `db.save` and `models.validate`; all hypothesis confidences bounded; structural (fact) nodes identical before/after enrichment |
| `TestConfidence` | 4 | fact calibrates to 1.0; evidence-free hypothesis demotes to 0.5; naming-capped hypothesis ≤ source weight; noisy-OR aggregation equals cap at strongest source |
| `TestIndex` | 3 | `find("db")` finds `module::db`; callers of `models.validate` include `save`; entry points include `main` |
| `TestQA` | 6 | "where is save" → intent `where` + `db.py` mention + labelled facts; "what does store call" → `callees`; "what does db do" → summary mentions docstring word `persistence`; "entry points" → contains `main`; "flows" → intent `flows` + non-empty hypotheses; unknown entity → "couldn't find" text |
| `TestNarrative` | 2 | sectioned output (Overview/Entry points/Module map/Key flows); mentions Parse health |
| `TestImportDesugar` | 2 | `module::db` imports `module::models` (single-dot); `module::services.store` imports `module::db` (double-dot) |
| `TestWhyCli` | 2 | `why <node-id>` resolves the exact node (defect §16.14 regression); `why <name>` still falls back to name search |

### 14.3 Why the suite justifies itself

A large share of the §16 defect list was caught **by these tests** (method containment,
relative-import resolution, cross-module calls, QA intent routing, cache versioning).
The fixture is the deterministic canary for real-corpus drift.

---

## 15. Validation on real corpora

### 15.1 Corpus A — `JG-CODE/doc_rag` (31 files)

Local RAG tool over Roblox docs (ingest, chunker, embedder, retriever, indexer, evidence,
expand, refapi, scripts, quality, trust + vendored `data/frameworks/…` helpers).

**Per-module function counts (from live artifact):**

```
benchmark:5  chunker:21  cli:10  config:1  context:3  db:8  embedder:2  evidence:4
expand:6  indexer:17  ingest:15  quality:4  refapi:13  retriever:9  scripts:4
textutil:4  trust:6  tests.test_smoke:36
+ data.frameworks.{knit.last_changelog:1, rbxutil.*:12, react-lua.bin.*:6}
```

| Metric | Facts-only | Enriched |
| --- | --- | --- |
| nodes | 244 `{1 repo, 31 module, 8 class, 187 function, 17 method}` | 306 (+4 domain, +10 flow, +48 intent) |
| edges | 679 `{CONTAINS=243, IMPORTS=227, CALLS=209}` | 741 |
| call resolution | 148 same-module / 61 cross-module | — |
| parse | 31/31, errors 0 | — |
| elapsed | ~0.50 s | ~0.6 s |

### 15.2 Corpus B — `jgpredictor` (122 files)

| Metric | Facts-only | Enriched |
| --- | --- | --- |
| nodes | 1117 `{1 repo, 122 module, 58 class, 728 function, 208 method}` | 1316 (+24 domain, +1 flow, +174 intent) |
| edges | 2913 `{CONTAINS=1116, IMPORTS=989, CALLS=808}` | 3112 |
| call resolution | 801 same-module / 7 cross-module | — |
| parse | 122/122, errors 0 | — |
| elapsed | ~1.10 s | ~1.11 s |

Note the corpus-shape contrast the MVP must handle: `doc_rag` is call-graph rich with few
modules (heavy cross-module linkage); `jgpredictor` is module-rich with mostly intra-module
calls (little cross-module linkage). Both handled without configuration — FR-8 (zero manual
annotation) holds.

### 15.3 Determinism protocol (NFR-4)

1. `json <repo> --out A.json`; `json <repo> --out B.json`.
2. Compare `sorted((id,type))` for nodes and `sorted((source,target,relationship))` for edges.
3. Repeat with `--cache` (cold vs. warm).

Results: identical id-sets for **both** corpora, fresh and cached. Enrichment re-run twice
on `doc_rag` → identical `{services_domain, flows, intents}` counts (10/48/4 both times).

### 15.4 Cache behavior

`doc_rag --cache`: cold `reparsed=31 / from_cache=0` → warm `reparsed=0 / from_cache=31`
(`ok=31` throughout), identical node/edge id-sets and totals (244 nodes / 679 edges both ways).
Elapsed warm ~0.38 s vs cold ~0.53 s.

### 15.5 CLI exercised

All 8 commands run on `doc_rag`; `stats`, `enrich`, `ask`, `json` also on `jgpredictor` —
no command-line smoke-test failures.

---

## 16. Bugs found and fixed during the build

Full, step-by-step narrative is in `prototype/BUILDLOG.md`. Summary table (each with the
defect, the fix, and how it was verified):

| # | Defect | Fix | Verified by |
| --- | --- | --- | --- |
| 16.1 | **Function loop indentation** nested under class loop — module-level functions skipped | moved the function loop out of the class loop; distinguish module vs class scope via visitor stack | node counts (204 funcs on doc_rag); tests |
| 16.2 | **Method containment id mismatch** — `class::{mid}:{parent}` vs `new_id`'s `::` joins; methods attached to nothing | use `class::{mid}::{parent}` | `test_class_and_method`; narrative entry points show methods with class context |
| 16.3 | **Scoped calls** — calls weren't attributed to their enclosing function | `CollectVisitor` records `(scope, name, base)`; CALLS source = function node | flows 0 → real; `test_calls_cross_module` |
| 16.4 | **Module docstring never captured** — node created before visitor ran | visit tree first, then emit module node | `ask "what does X do"` shows module docstring; `test_summary_module_docstring` |
| 16.5 | **Entry points included tests** — `tests/`, `test_*` scaffolding surfaced as public API | exclude locations under `tests/`, `/tests/`, `test_*`, and names starting `test_` | `ask "entry points"` no longer lists test internals |
| 16.6 | **Attribute-prefix calls unresolved** — `models.validate()` recorded only `validate` | capture `base`; resolve `base` through import aliases during linking | CALLS `func::db::save → func::models::validate` appears; `indexer.build → init_db` now resolved (7 callers of `init_db` reported) |
| 16.7 | **QA intents used literal `x`** — `what\s+does\s+x\s+call` matched only the token "x" | capture-group regexes `(\w+)` for all name slots | `ask "what does store call"` → intent `callees` (test); `ask "who calls init_db"` → intent `callers` |
| 16.8 | **`from . import X` lost its relative marker** — `imports` triple had bare `X` | rewrite ImportFrom to produce leading-dot targets (`".models"`) | `test_relative_import_to_module_edge`; `test_from_dotdot_service` |
| 16.9 | **`_resolve_local_import` `max(1, …)` broke top-level siblings** — `db` importing `.models` resolved to `db.models` | `max(0, …)` so `db` → sibling `models` | import edges `module::db → module::models` correct |
| 16.10 | **DomainConcept sniff on `.py`** — `name.split(".")[-1]` on `db.py` ⇒ `"py"` never matched regex | basename-minus-extension segmentation | doc_rag svc/domain 0 → 4; jgpredictor → 24; `os` import added |
| 16.11 | **`ask` ignored enrichment** — hypothesis-browse queries returned 0 | `cmd_ask` uses `enrich_ok=True` | `ask "flows"` returns 10 flows with confidence |
| 16.12 | **Duplicate `Repository→Module` CONTAINS edges** — `_extract_module` already emits the repo edge per module (and it is replayed from cache), but `build()` re-emitted a second copy in a finalize pass → 62 repo edges for 31 modules (244 for 122); fact edges inflated by 31/122 (710→679, 3035→2913) | removed the redundant finalize pass; the per-module edge (cold path + cache replay) is the single source | `test_repo_contains_each_module_once`; pair-count probe shows `repo→module: 31` (doc_rag) / `122` (jgpredictor); totals re-measured in §15 |
| 16.13 | **`stats` mislabeled `parsed=` as parse_ok** — warm runs printed `parsed=31` while 0 modules were re-parsed, inviting wrong reports (it did mislead an earlier draft of §15.4) | print `reparsed={n_parsed}` and `ok={parse_ok}` separately | cold/warm transcript in §7.2: `reparsed=31/0`, `from_cache=0/31` |
| 16.14 | **`why <node-id>` never resolved** — `cmd_why` only called `idx.find(name)`, which matches names, so the documented `why <node-id-or-name>` contract failed for ids (`why func::db::connect` → "not found") | try `idx.node(id)` first, fall back to name search | `why func::db::connect` → `[FACT] … db.py:73`; `TestWhyCli` (id + name paths) |

Additionally: `CACHE_VERSION` bumped 1 → 2 when the cached call triple's shape changed, and
the stale-bytecode hazard (PowerShell/Windows, `__pycache__`) was handled by purging caches
during the session.

These fourteen fixes are **a measurable part of the MVP's value**: without them the package
would silently misattribute methods, mis-resolve calls, double-count containment, and
mis-answer questions.

---

## 17. Requirement traceability matrix

Per `docs/requirements.md` v1.0 (frozen, Gate G1).

| ID | Requirement (abbrev.) | Priority | Implementation | Verification |
| --- | --- | --- | --- | --- |
| FR-1 | Derive structural facts | Must | `extract.py` (Modules/Classes/Functions/Methods, imports, calls) | node stats both corpora |
| FR-2 | Produce semantic hypotheses | Should | `semantics.py` (Flow/Intent/Service/DomainConcept) | enriched node counts |
| FR-3 | Separate facts from hypotheses | Must | distinct node types + `model.STRUCTURAL_*`/`HYPOTHESIS_KINDS`; `FR-3` demotion rule | `test_facts_untouched_by_enrich`, CLI output blocks |
| FR-4 | Confidence + evidence on every claim | Must | every node `evidence` list; `confidence.calibrate/why` | `test_evidence_present`, `ask`/`why` output |
| FR-5 | Incremental updates | Must | D-8 sha256 cache (opt-in `--cache`) | cold/warm counters (§15.4) |
| FR-6 | ≥1 projection (H1+H3 per RB-1) | Must | `qa.py`, `narrative.py` | CLI `ask`, `narrative` |
| FR-6a | Grounded answers, facts vs hypotheses separated, `file:line` links | Must | `qa._result(facts, hypotheses)`, evidence-linked rows in `_print_answer` | transcripts (Appendix B) |
| FR-7 | Serve humans and AI | Must | CLI (human) for v1; artifact JSON export is the agent-ready structured context | `json --out` command |
| FR-8 | Zero manual annotation | Must | no configuration inputs anywhere; two corpora run bare | §15.1/§15.2 |
| FR-9 | Multi-language hospitable parsing interface | Could | `ast`-based single extractor; artifact format language-neutral | design note |
| NFR-1 | Dev-friendly (minutes to first value) | Must | one-command CLI, zero deps, no config | `python -m ssrl.cli stats <repo>` |
| NFR-2 | Traceability to source locations | Must | `evidence[0].source = "file:line"` on all fact nodes | `test_evidence_present`; `ask "where"` output |
| NFR-3 | Freshness / no unbounded staleness | Must | narrative + facts rebuilt on demand; cache keyed by content hash | §15.4 |
| NFR-4 | Determinism of facts | Must | sorted iteration, no random, bounded heuristic passes | §15.3; `test_determinism` |
| NFR-5 | Non-invasive analysis | Must | open() read-only; corpora unmodified (verified by identical hashes across runs) | design + §15.3 |
| NFR-6 | Performance / cheaper incremental | Should | warm build ~1.3× faster than cold on doc_rag; ~0.4–0.6 s | §15.4 |
| NFR-7 | Auditable & exportable format | Should | `json` command + JSON artifact; `audit` table | CLI smoke |
| RN-1 | Primary projection = H1 + H3 | accepted | `qa.py` + `narrative.py` as projections; H2/H4 not built | §11, §12 |
| RN-2 | Semantic scope (open) | open | MVP implements a first useful subset; validation deferred | §8 |
| RN-3 | Confidence calibration (open) | open | conservative v1 policy implemented; statistical validation deferred (Phase 9) | §9 |
| RN-4 | Hypothesis sources: structure→naming→LLM-last | accepted | `semantics.py` structural+heuristic only; zero LLM | §8 |
| RN-5 | Storage: derived artifact; no vectors; SQLite escalation pre-declared | accepted | JSON artifact in memory + file export; no embed code | §5, §13 |

**Status:** FR-1…FR-9, NFR-1…NFR-7 and RN-1/4/5 fully covered by the MVP (RN-1/4/5 were
already resolved at G1). RN-2/RN-3 are, per the spec, open research-phase follow-ups that
the MVP now provides a substrate for (`audit` als instrument).

---

## 18. Research hypothesis traceability

| Research item | Position | MVP evidence |
| --- | --- | --- |
| H1 grounded Q&A primary | ADR-005 | `qa.py` answers with separated facts/hypotheses + evidence links (FR-6a) |
| H3 living narrative co-surface | ADR-005 | `narrative.py` sectioned report regenerated on demand (never stale) |
| H2 progressive zoom | supporting | not built in MVP (roadmap Phase 7/8+); index primitives (`children`, `deps_closure`) prepare it |
| H4 graph navigation | supporting | Sourcetrail's failure (W2); `json` export is the raw material when re-opened |
| RQ-1 value | in progress | draft automated pass executed in Phase 9 (entity-F1 vs facts gold) — human grading pending |
| RQ-2 interaction | **resolved (G1)** | H1+H3 implemented as chosen |
| RQ-3 trust/calibration | in progress | policy + `audit`/`why` implemented; Phase 9 draft pass + calibration instrumentation; statistical validation pending |
| RQ-4 hypothesis sources | resolved (RN-4/ADR-007) | naming+structure only; LLM-proposer deferred |
| RQ-5 semantic concepts | in progress | Flow/Intent/Service/DomainConcept survive contact with both corpora (376 total hypotheses) |

---

## 19. Honest limitations

1. **No type inference.** Call resolution is name + import-alias + attribute-prefix based;
   `self.method()`, decorated/duck-typed calls, and shadowed names resolve heuristically or
   stay unresolved (counted, never fabricated). Facts are exact; **linkage** is best-effort
   and labeled.
2. **No LLM anywhere (by design, ADR-007).** Hypothesis quality is limited to what naming +
   structure encode; an LLM-proponent layer that feeds the confidence engine is the natural
   next step but is intentionally out of the MVP. *(Since Phase 9: the micro-LLM proponent
   exists as an optional, capped hypothesis source — ADR-008; the MVP core stays deterministic.)*
3. **Flat function ids.** Two same-named methods in different classes of one module share a
   `func::<mid>::<name>` id; the CONTAINS edge still ties each to its true class. Documented
   limit of the flat id scheme.
4. **Relative-import scope.** Resolution is correct only within the scanned root; a package
   identity above the root is unknown (so, e.g., a sub-package importing its own parent
   package may resolve heuristically).
5. **No watch loop yet.** The cache is manual via `--cache`; Phase 7 (watch/regenerate) is the
   natural successor and is a thin design extension on top of D-8. *(Done in Phase 7: `watch` —
   see `REPORT-P7.md`.)*
6. **Confidence not statistically calibrated.** `audit` reports, but ground-truth /
   calibration-vs-behavior validation is Phase 9 work. *(Phase 9 executed a draft automated pass
   with facts-derived gold + a probe battery — see REPORT-P9 §6.1–§6.2; statistical
   validation is pending.)*
7. **Comprehension-gain not yet measured.** No controlled experiments; the MVP proves
   mechanics and honesty, not the RQ-1 value claim. *(Phase 9 ran an automated proxy — the
   draft study, REPORT-P9 §6.1; the human-graded study remains.)*
8. **Corpus diversity.** Two Python repos (CLI-style + library-style) — a narrow slice of
   the design space; multi-language and other domains await later phases.
9. **Intent heuristics over-trigger on tests.** `tests.test_smoke` contributes ~9 intents to
   `doc_rag` (36 functions); intent generation does not exclude test files (entry-point
   filtering does). Pending refinement.

---

## 20. Reproduction commands

```console
# from prototype/
$env:PYTHONUTF8='1'

python -m ssrl.cli stats     <repo>                 # facts-only stats
python -m ssrl.cli enrich    <repo> --cache         # facts + hypotheses, cached
python -m ssrl.cli ask       <repo> "who calls X"   # grounded Q&A
python -m ssrl.cli ask       <repo> "flows"         # hypothesis browse
python -m ssrl.cli why       <repo> func::db::save  # evidence explanation
python -m ssrl.cli narrative <repo>                 # living narrative
python -m ssrl.cli audit     <repo>                 # calibration table
python -m ssrl.cli json      <repo> --out art.json --enrich   # NFR-7 export

python -m unittest discover -s tests -v             # 33 tests
```

---

## Appendix A — Calibration audit dump (doc_rag)

Full `ssrl audit` output (62 hypothesis rows, sorted by id). Reproduced verbatim from the
live run (2026-09); truncated columns preserved as emitted.

```text
flow::func::benchmark::main                                            Flow           conf=0.88   strong hypothesis
flow::func::chunker::iter_page_chunks                                  Flow           conf=0.88   strong hypothesis
flow::func::context::search_for_context                                Flow           conf=0.88   strong hypothesis
flow::func::data.frameworks.react-lua.bin.svg::display                 Flow           conf=0.88   strong hypothesis
flow::func::db::get_meta_int                                           Flow           conf=0.88   strong hypothesis
flow::func::embedder::available                                        Flow           conf=0.88   strong hypothesis
flow::func::embedder::encode                                           Flow           conf=0.88   strong hypothesis
flow::func::evidence::assess_requirement                               Flow           conf=0.88   strong hypothesis
flow::func::expand::expand_query                                       Flow           conf=0.88   strong hypothesis
flow::func::expand::query_groups                                       Flow           conf=0.88   strong hypothesis
hyp::domainconcept::module:cli::entrypoint                             DomainConcept  conf=0.80   strong hypothesis
hyp::domainconcept::module:config::config                              DomainConcept  conf=0.70   moderate hypothesis
hyp::domainconcept::module:db::persistence                             DomainConcept  conf=0.82   strong hypothesis
hyp::domainconcept::module:textutil::infra                             DomainConcept  conf=0.74   moderate hypothesis
intent::func::chunker::_member_metadata:persist                        Intent         conf=0.76   strong hypothesis
intent::func::chunker::_normalize_html_headings:transform              Intent         conf=0.76   strong hypothesis
intent::func::chunker::yaml_to_markdown:transform                      Intent         conf=0.76   strong hypothesis
intent::func::cli::_cmd_search:retrieve                                Intent         conf=0.72   moderate hypothesis
intent::func::cli::_cmd_status:compute                                 Intent         conf=0.70   moderate hypothesis
intent::func::context::search_for_context:retrieve                     Intent         conf=0.72   moderate hypothesis
intent::func::data.frameworks.knit.last_changelog::get_last_changelog_entry:retrieve Intent conf=0.72   moderate hypothesis
intent::func::data.frameworks.rbxutil.build_list::get_wally_info:retrieve           Intent conf=0.72   moderate hypothesis
intent::func::data.frameworks.rbxutil.build_tests::update_test_file:persist         Intent conf=0.76   strong hypothesis
intent::func::data.frameworks.rbxutil.run_tests::get_script_status:retrieve         Intent conf=0.72   moderate hypothesis
intent::func::db::connect:retrieve                                     Intent         conf=0.72   moderate hypothesis
intent::func::db::get_meta:retrieve                                    Intent         conf=0.72   moderate hypothesis
intent::func::db::get_meta_int:retrieve                                Intent         conf=0.72   moderate hypothesis
intent::func::embedder::get_embedder:retrieve                          Intent         conf=0.72   moderate hypothesis
intent::func::embedder::load:retrieve                                  Intent         conf=0.72   moderate hypothesis
intent::func::evidence::_rag_coverage:retrieve                         Intent         conf=0.72   moderate hypothesis
intent::func::expand::_terms:retrieve                                  Intent         conf=0.72   moderate hypothesis
intent::func::expand::expand_query:retrieve                            Intent         conf=0.72   moderate hypothesis
intent::func::expand::query_groups:retrieve                            Intent         conf=0.72   moderate hypothesis
intent::func::indexer::_backfill_embeddings:persist                    Intent         conf=0.76   strong hypothesis
intent::func::indexer::_insert_chunks:persist                          Intent         conf=0.76   strong hypothesis
intent::func::indexer::_sweep_duplicates:transform                     Intent         conf=0.76   strong hypothesis
intent::func::indexer::_upsert_source:persist                          Intent         conf=0.76   strong hypothesis
intent::func::indexer::stats:compute                                   Intent         conf=0.70   moderate hypothesis
intent::func::ingest::_download_tarball:retrieve                       Intent         conf=0.72   moderate hypothesis
intent::func::ingest::read_file:retrieve                               Intent         conf=0.72   moderate hypothesis
intent::func::quality::write_report:persist                            Intent         conf=0.76   strong hypothesis
intent::func::refapi::_match_score:compute                             Intent         conf=0.70   moderate hypothesis
intent::func::refapi::load_class:retrieve                              Intent         conf=0.72   moderate hypothesis
intent::func::refapi::normalize_property:transform                     Intent         conf=0.76   strong hypothesis
intent::func::refapi::property_profile:persist                         Intent         conf=0.76   strong hypothesis
intent::func::refapi::search_properties:retrieve                       Intent         conf=0.72   moderate hypothesis
intent::func::retriever::_api_query:persist                            Intent         conf=0.76   strong hypothesis
intent::func::retriever::_candidates_or_fallback:retrieve              Intent         conf=0.72   moderate hypothesis
intent::func::retriever::_cosine_scores:retrieve                       Intent         conf=0.72   moderate hypothesis
intent::func::retriever::search:retrieve                               Intent         conf=0.72   moderate hypothesis
intent::func::scripts::index_scripts:persist                           Intent         conf=0.76   strong hypothesis
intent::func::tests.test_smoke::_index_ready:retrieve                  Intent         conf=0.72   moderate hypothesis
intent::func::tests.test_smoke::test_devforum_build_query:retrieve     Intent         conf=0.72   moderate hypothesis
intent::func::tests.test_smoke::test_integration_devforum_search:retrieve Intent      conf=0.72   moderate hypothesis
intent::func::tests.test_smoke::test_integration_hybrid_ranks_relevant_first:compute Intent conf=0.70   moderate hypothesis
intent::func::tests.test_smoke::test_integration_mcp_search_docs:retrieve Intent       conf=0.72   moderate hypothesis
intent::func::tests.test_smoke::test_integration_search:retrieve       Intent         conf=0.72   moderate hypothesis
intent::func::tests.test_smoke::test_retriever_api_query_detection:retrieve Intent      conf=0.72   moderate hypothesis
intent::func::tests.test_smoke::test_trust_final_score_hierarchy:compute Intent        conf=0.70   moderate hypothesis
intent::func::textutil::clean_snippet:transform                        Intent         conf=0.76   strong hypothesis
intent::func::textutil::fts_query:retrieve                             Intent         conf=0.72   moderate hypothesis
intent::func::trust::final_score:retrieve                              Intent         conf=0.72   moderate hypothesis
```

(62 hypothesis rows: 10 Flows · 4 DomainConcepts · 48 Intents.)

## Appendix B — Q&A transcripts

Live transcripts against the enriched `doc_rag` artifact.

### B.1 `who calls search`

```text
Callers of `search`: _run_db, _cmd_search, search_for_context, build_context (4 facts, confidence 1.0).

FACTS (confidence 1.0):
  [callers (facts)]
    - Function `_run_db`        (benchmark.py:73)
    - Function `_cmd_search`    (cli.py:132)
    - Function `search_for_context` (context.py:33)
    - Function `build_context`  (context.py:52)
```

### B.2 `what does indexer do`

```text
Module `indexer.py`: 0 class(es), 17 top-level function(s), 18 import(s).
Module docstring: doc_rag/indexer.py — Indexador: ingestão raw + upsert embeddings + FTS5…
(5 fact rows: classes, functions, imports) — (hypotheses touching entity listed if any)
```

### B.3 `where is connect`

```text
Function `connect` defined at db.py:73 (confidence 1.0).

FACTS (confidence 1.0):
  [evidence]
    - Function `connect` (db.py:73)
```

### B.4 `imports of retriever`

```text
`retriever.py` imports: from:__future__.annotations, import:logging, import:struct,
from:pathlib.Path, from:typing.Any, config.py, db.py, embedder.py, expand.py,
expand.py, textutil.py, textutil.py, trust.py, import:numpy (14 facts, confidence 1.0).
```

### B.5 `dependencies of indexer`

```text
Transitive dependencies of `module::indexer`: 7 nodes (embedder.py, ingest.py, …) (7 facts, confidence 1.0).
```

### B.6 `flows`

```text
10 Flow hypotheses (calibrated confidence):
  - flow::func::benchmark::main conf=0.88 — strong hypothesis
  … (10 rows)
HYPOTHESES (calibrated):
  - Flow `main` conf=0.88 (strong hypothesis) id=flow::func::benchmark::main
  …
```

## Appendix C — Sample artifact fragment

```json
{
  "graph_version": "0.4",
  "generated_by": "ssrl-prototype-phase3",
  "nodes": [
    {"id": "module::db", "type": "Module", "name": "db.py", "confidence": 1.0,
     "evidence": [{"type": "parser", "source": "db.py:1"}],
     "metadata": {"sha256": "a1b2c3d4e5f6a7b8", "docstring": "SQLite store for doc_rag."}},
    {"id": "func::db::save", "type": "Function", "name": "save", "confidence": 1.0,
     "evidence": [{"type": "parser", "source": "db.py:34"}],
     "metadata": {"kind": "function", "scope": "module"}},
    {"id": "intent::func::db::save:persist", "type": "Intent", "name": "persist",
     "confidence": 0.76,
     "evidence": [{"type": "NamingPattern", "source": "save", "weight": 0.76}],
     "metadata": {"target": "func::db::save", "hypothesis": true}}
  ],
  "edges": [
    {"id": "e:…", "source": "module::db", "target": "func::db::save",
     "relationship": "CONTAINS", "confidence": 1.0,
     "evidence": [{"type": "parser", "source": "db.py:34"}]},
    {"id": "e:…", "source": "func::db::save", "target": "func::models::validate",
     "relationship": "CALLS", "confidence": 1.0,
     "evidence": [{"type": "call-graph", "source": "linker"}],
     "metadata": {"resolution": "cross-module"}}
  ],
  "stats": {"files": 31, "from_cache": 0, "parsed": 31, "parse_ok": 31,
            "parse_errors": 0, "nodes": 306, "edges": 741, "functions": 204,
            "imports": 227, "calls": 209, "elapsed_s": 0.61,
            "hypotheses": {"services_domain": 4, "flows": 10, "intents": 48}}
}
```

(ids are illustrative for `db.py`; real doc_rag `save` location is `db.py:34` only if the
source says so — sample excerpt for shape, not a literal slice.)

## Appendix D — Definitions and glossary

| Term | Meaning |
| --- | --- |
| Fact | structural, deterministic claim (conf 1.0), evidence to `file:line` (FR-1/FR-4) |
| Hypothesis | inferred semantic claim (conf < 1.0), labeled evidence (FR-2/FR-4) |
| Projection | a consumer surface over the layer (Q&A, narrative, graph, zoom) |
| Evidence | tagged provenance (`parser`, `call-graph`, `NamingPattern`, …) with weight/source |
| Calibration | mapping raw evidence weights to a stated confidence (RQ-3) |
| D-8 | incremental-synchronization decision — file-level hash+mtime cache |
| RN-* | research-gated requirement (cannot be finalized until research resolves it) |
| MCP | Model Context Protocol — the declared future agent surface (ADR-006) |

---

## Closing note

The V1 MVP is a **compressed vertical slice** of every executable roadmap phase: a working,
tested, deterministic, dependency-free layer from raw Python to grounded answers and living
narrative — with every semantic claim visibly uncertain and every fact traced to a line.
It was committed to git as `8d24440`; Phase 7 (`cdba65b`) and Phase 8 (`4da9c1b`) added the
watch loop and the MCP agent surface (see `REPORT-P7.md` / `REPORT-P8.md`), and Phase 9
(`bcd0996` + study/probe) delivered the micro-LLM proposer and the validation groundwork
(REPORT-P9 §6.1–§6.2). The next step is the definitive human-graded study within Phase 10
(publication).