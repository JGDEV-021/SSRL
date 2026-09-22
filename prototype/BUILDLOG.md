# SSRL V1 MVP — Build Log

**Period:** 2026-09 (Phase 3 close-out → V1 MVP).
**Goal (from the author directive):** "*vetor vai construindo, sem parar, todas as fases possíveis — quero uma V1 MVP do SSRL pronta. Sempre anote tudo, sempre faça relatórios, não erre.*"

Every step below is traceable to a file; every claim reproduces with the commands shown.

---

## 1. Migration: single script → package

**Commit-of-work:** `prototype/ssrl/` package replaces `prototype/ssrl_facts.py`.

Files created (all stdlib-only, ADR-002):

| Module | Purpose | Status |
| --- | --- | --- |
| `model.py` | taxonomy, stable ids, `make_edge` (ADR-003) | ✅ |
| `extract.py` | AST extractor + incremental cache (D-8) | ✅ |
| `semantics.py` | hypotheses: flows / intents / services/domain | ✅ |
| `confidence.py` | calibrate / aggregate / why / audit | ✅ |
| `index.py` | in-memory index + query helpers | ✅ |
| `qa.py` | grounded Q&A (H1) | ✅ |
| `narrative.py` | living narrative (H3) | ✅ |
| `cli.py` + `__main__.py` | CLI `build|enrich|ask|why|narrative|audit|stats|json` | ✅ |
| `__init__.py` | package marker | ✅ |

**Bugs found & fixed during migration:**

1. **Indentation bug** (`extract.py`): function loop was nested inside the class loop — functions outside classes were skipped. Classified {{functions}} correctly relative to module + class scope.
2. **Scoped call capture** (`extract.py`): calls now carry `(scope_name, name)`; CALLS edge source is the containing function, not the module. Registered flows went 0 → real count.
3. **Method containment** (`extract.py`): `parent_node` used `class::{mid}:{parent}` with a single `:` but `model.new_id` joins with `::`. Methods falsely detached from classes. Fixed to `::`.
4. **Module docstring** (`extract.py`): module `metadata.docstring` was never populated (`v` visited after node creation). Reordered visit; docstrings now surface in `ask`/narrative.
5. **Integers/re.I in intents** (`qa.py`): tuple had arity mismatch — fixed.
6. **Entry points included tests** (`index.py`): `skip_tests` filter excludes `tests/`, `test_*` — verified: `doc_rag` entry points no longer list test scaffolding.
7. **QA intents used literal `x`** (`qa.py`): regexes like `what\s+does\s+x\s+call` matched only the literal token "x". Rewritten with capture groups (`(\w+)`) so real names route correctly (`what does store call` → `callees`).
8. **Cross-module attr-prefix calls unresolved** (`extract.py`): `models.validate(item)` recorded only `validate`, losing the `models.` prefix. `visit_Call` now records attribute base; linker resolves through import aliases. Verified: `func::db::save → func::models::validate` becomes a cross-module CALLS edge (fixture).
9. **Relative-import sibling resolution** (`extract.py`): `from . import X` / `from ..db import save` produced `pkg.sub`-style module ids. Rewrote `visit_ImportFrom` (leading-dot targets) and `_resolve_local_import` to resolve siblings within the scanned root. Verified with fixture edges `module::db → module::models`, `module::services.store → module::db`.
10. **DomainConcept sniff on module names** (`semantics.py`): `name.split(".")[-1]` on `db.py` yields `"py"`, never matching `(db|database|…)`. Switched to basename-minus-extension. `doc_rag` services/domain went 0 → 4; `jgpredictor` → 24. (`os` import was missing — fixed.)
11. **`ask` ignored enrichment** (`cli.py`): `cmd_ask` loaded facts-only, so `ask "flows"` returned 0 hypotheses. Now loads the enriched artifact.
12. **Duplicate `Repository→Module` CONTAINS edges** (`extract.py`): `_extract_module` already emits the repo edge per module (and cache replay preserves it), but `build()` re-emitted a second copy in a finalize pass — 62 repo edges for 31 modules (`doc_rag`), 244 for 122 (`jgpredictor`); fact-edge totals were inflated by exactly the module count (710→679, 3035→2913). Removed the finalize pass. Verified: new regression test `test_repo_contains_each_module_once` (33 tests total) + pair-count probe `repo→module: 31 / 122`.
13. **`stats` label lied about parsing** (`cli.py`): the `parsed=` column printed `parse_ok` (healthy modules), so warm runs displayed `parsed=31` while 0 modules were re-parsed — this actually misled an earlier draft of the §15.4 cache write-up. Now prints `reparsed={n_parsed}` and `ok={parse_ok}` separately. Verified: cold `reparsed=31 from_cache=0` → warm `reparsed=0 from_cache=31`.
14. **`why <node-id>` never resolved** (`cli.py`): `cmd_why` only called `idx.find(name)`, but `find` matches names — the documented `why <node-id-or-name>` contract silently failed for ids (`why func::db::connect` → "not found" even though the node exists). Now tries `idx.node(id)` first, then falls back to name search. Verified by smoke on `doc_rag` (`[FACT] func::db::connect … db.py:73`) + `TestWhyCli` (id and name paths).

---

## 2. Incremental cache (D-8)

Implemented in `extract.py` as file-level **sha256** cache, keyed by repo-relative path; `CACHE_VERSION=2` (bumped when the calls tuple shape changed to include the attribute base).

```console
$ python -m ssrl.cli stats <repo> --cache     # cold
files=31 reparsed=31 ok=31 errors=0 from_cache=0 …
$ python -m ssrl.cli stats <repo> --cache     # warm
files=31 reparsed=0 ok=31 errors=0 from_cache=31 …
```

Verified: warm artifact is byte-identical at the (id,type) / (source,target,relationship) level. Determinism preserved → NFR-4.

---

## 3. Enrichment (Phase 5) + Confidence (Phase 6)

- `semantics.enrich` produces **hypotheses only** (FR-3): `Flow` (CALLS chains from entry points, BFS breadth/depth capped — deterministic), `Intent` (entry-point naming + docstring signal), `Service`/`DomainConcept` (module/class naming sniff). Every hypothesis carries `evidence` and `confidence < 1.0`; facts untouched.
- `confidence`: `aggregate` = noisy-OR of per-source weights, **capped by the strongest single source's ceiling**; `calibrate` clamps hypotheses to `[0.55, 0.95]`, demotes no-evidence to `0.5`; `why` explains; `audit` tabulates.

---

## 4. Determinism & corpus validation

Determinism verified twice per corpus (fresh runs → identical node/edge id sets):

| Corpus | Files | Nodes | Edges | Determinism | Elapsed |
| --- | --- | --- | --- | --- | --- |
| `JG-CODE/doc_rag` | 31 | 244 | 679 | ✅ 2 runs identical | ~0.5 s |
| `jgpredictor` | 122 | 1117 | 2913 | ✅ 2 runs identical | ~1.2 s |

(Edge totals recomputed after defect 12 — duplicate `repo→module` CONTAINS edges fixed;
the pre-fix runs reported 710 / 3035, inflated by 31 / 122 respectively.)

Enriched (also deterministic — 2 runs identical):

| Corpus | Nodes(+hyp) | Flows | Intents | Services/Domain |
| --- | --- | --- | --- | --- |
| `JG-CODE/doc_rag` | 306 | 10 | 48 | 4 |
| `jgpredictor` | 1316 | 1 | 174 | 24 |

CLI commands exercised on both corpora: `stats`, `enrich`, `ask` (summary/where/callers/callees/imports/entry points/flows), `why`, `narrative`, `audit`, `json` (with/without `--enrich`).

---

## 5. Unit tests

`prototype/tests/test_mvp.py` — stdlib `unittest`, fixture repo `tests/fixtures/pkgapp/`
(`main.py`, `db.py`, `models.py`, `services/store.py`, `__init__.py` ×2).

```console
$ cd prototype && python -m unittest discover -s tests -v
Ran 33 tests in 0.2s — OK
```

Coverage surface (33 green):

- Extract: parse health, node/edge taxonomy, class→method containment, imports desugaring (local + `from .` + `from ..pkg`), same/cross-module calls, evidence presence, fact confidence == 1.0, determinism, exactly-one repo→module CONTAINS per module (defect 12 regression).
- Why CLI: `why` by node-id and by name fallback (defect 14 regression).
- Cache: cold vs warm hit counters, identical output.
- Semantics: intents/flows generated, confidence domain bounds, facts untouched by enrichment.
- Confidence: fact calibration, no-evidence demotion, source-ceiling cap, noisy-OR aggregation.
- Index: find, callers, entry points.
- QA: where/callees/summary-docstring/entry/browse-trends/not-found routing.
- Narrative: sectioned output, parse-health mention.

---

## 6. Reports

- `prototype/BUILDLOG.md` — this log.
- `prototype/REPORT-V1.md` — V1 MVP report (status, verification matrix, metrics, honest limits).
- `prototype/REPORT-P7.md` — Phase 7 lab report (watch design, lab measurements, live demo).
- `prototype/README.md` — quick-start, package map, verified properties, measured stats.
- `roadmap.md` — Phase 3–6.5 + Phase 7 close-out marks; Phase 8 next.
- `paper/SSRL-v0.2.md` → **v0.3** — position paper updated with prototype findings (see `paper/SSRL-v0.3.md`).

---

## 7. Phase 7 — Lab Integration (watch / no-manual-sync)

Implemented per roadmap.md:175-183. New module `prototype/ssrl/watch.py` (v0.5.0) +
CLI command `watch` and lab driver `prototype/lab/p7_lab.py`.

- **Design (zero-dep, ADR-002):** polling stat baseline `{rel: (mtime_ns, size)}`
  (`watch.scan`/`watch.diff`); on change, `extract.build(root, cache_dir)` with the
  D-8 cache replays unchanged modules → only the delta is re-parsed.
  `initial_sync()`/`step()` are directly callable (tests + lab), `run()` composes the
  timed loop. `--events` writes a JSON-lines log. Cache **on by default** for
  `watch` (incremental parsing is the point of continuous operation; other commands
  keep opt-in `--cache`).
- **Lab measurement (`lab/p7_lab.py`, doc_rag copy, enrich on):**

  | # | event | reparsed | from_cache | nodes | edges | Δnodes | elapsed_s |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | 1 | initial | 31 | 0 | 306 | 741 | — | 0.91 |
  | 2 | +fn in retriever | 1 | 30 | 307 | 742 | +1 | 0.44 |
  | 3 | +new module | 1 | 31 | 309 | 744 | +2 | 0.41 |
  | 4 | −new module | 0 | 31 | 307 | 742 | −2 | 0.41 |
  | 5 | body edit | 1 | 30 | 307 | 742 | 0 | 0.47 |
  | 6 | revert | 1 | 30 | 306 | 741 | −1 | 0.43 |

  Revert converges the artifact to the initial build exactly (306/741) — no drift.
- **Live read-only demo (`watch <jpredictor> --enrich`, interval 0.3 s):** initial
  sync `reparsed=0 from_cache=122` (all cached), then silent polls until a change —
  continuous operation, corpus untouched (sha256 before/after identical, NFR-5).
- **Known limitation, documented:** D-8 cache is single-version per file — reverting
  re-parses the reverted file once (correct, not replayed).
- **Tests:** `TestWatch` (6 tests: diff add/modify/remove, initial full-parse,
  delta-only re-parse, static no-op, deletion, revert convergence) → suite **39 green**.

---

## 8. Remaining (post-V1 MVP + Phase 7)

- Phase 7 lab: incremental watch/regenerate-on-change on a real evolving project. **DONE — see section 7 and `prototype/REPORT-P7.md`.**
- Phase 8: end-to-end agent surface (MCP server over `narrative`/Q&A).
- H2 progressive-zoom drill-down and H4 graph navigation (supporting projections).
- Full RQ-3 calibration study (Phase 9): controlled comprehension experiments.
- LLM as hypothesis *proponent* only, with structural re-scoring (RN-4 / ADR-007).