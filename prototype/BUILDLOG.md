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
- `prototype/REPORT-P8.md` — Phase 8 report (MCP agent surface, impact report, coherence check).
- `prototype/README.md` — quick-start, package map, verified properties, measured stats.
- `roadmap.md` — Phase 3–6.5 + Phases 7–9 close-out marks; Phase 10 next.
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

## 8. Phase 8 — End-to-End & Agent/AI Surface

Per roadmap.md:186. New modules `ssrl/impact.py` + `ssrl/mcp.py` (v0.6.0), CLI
subcommands `impact` and `mcp`, lab driver `lab/p8_lab.py`, report
`prototype/REPORT-P8.md`.

- **Impact report (ADR-006 supporting surface):** `impact_changed(artifact,
  changed_files)` maps changed files → affected modules, importers, breaking
  callers, entry points touched, flows affected, reverse dependencies.
  Deterministic (sorted lists, stable ids). CLI `impact <repo> FILES...
  [--git BASE]` — `--git BASE` feeds `git diff --name-only BASE` (CI drop-in).
  Regression locked during development: duplicate importer rows when a module
  had multiple IMPORTS edges (dedupe in `_node_ids`).
- **MCP server (ADR-006 v1.5), zero-dep:** JSON-RPC 2.0 over stdio with
  newline-delimited JSON (MCP stdio transport, no Content-Length framing).
  Handshake `initialize` → `notifications/initialized`; tools `ask`, `why`,
  `narrative`, `stats`, `audit`, `impact`. Every tool output is grounded and
  evidence-preserving (RQ-3; facts vs calibrated hypotheses). Build is lazy and
  cache-on by default (D-8, corpus never touched — NFR-5).
- **Lab (doc_rag, enrich, warm cache):** handshake ~0 s, first tool answer in
  **0.37 s** (`from_cache=31`, 306/741). `ask "who calls init_db"` → 7 callers
  with file:line evidence (indexer.py:275…, retriever.py:197…).
  `impact ['context.py','db.py']` → 2 modules, 6 importers, 28 callers may
  break, 3 entry points, 3 flows. **Coherence (success criterion)**: CLI and
  MCP answers to the same question are identical.
- **CI smoke on SSRL itself:** `impact .. --git main` → 3 files, 3 modules,
  36 callers, 11 entry points, 9 flows.
- **Tests:** `TestImpact` (5) + `TestMCPServer` (13) → suite **59 green**.

---

## 9. Phase 9 — Micro-LLM proposer (ADR-008)

Implemented per roadmap.md:198 (experimental-validation groundwork) + the
author directive: the LLM component is a **micro model (Qwen3-0.6B class)** —
proponent only, small contexts, speed-focused. New module `ssrl/llm.py` (v0.7.0),
CLI subcommand `propose`, lab driver `lab/p9_lab.py`, report
`prototype/REPORT-P9.md`, decision `research/decisions/ADR-008-micro-llm-proponent.md`.

- **Where it works (ADR-008):** exactly one optional stage — `propose` between
  enrichment and projection. The deterministic pipeline (`build`→`enrich`→
  `ask`/`narrative`) never calls the LLM (RN-4 / ADR-007); `propose` is pure:
  it only materializes hypotheses, and `--out` is required to persist them.
- **What it answers (closed tasks):** Task A `flow_intent` — ≤6-word name for a
  Flow chain (from facts: signature/callees); Task B `unit_role` — a unit labeled
  from a closed taxonomy `persistence|model|service|config|infra|entrypoint|
  controller|ui|util|unknown`. Output={"label"|"role", confidence, rationale},
  temperature 0, parsed leniently (`parse_flow_decision`/`parse_unit_decision`),
  drift/off-taxonomy → rejected (counted, never crashes).
- **What context is passed (tiny evidence bundles):** facts only — ids, signature,
  callees, contained units, imports (`flow_bundle` ≤ 2600 chars;
  `unit_bundle` ≤ 2200 chars). Measured on doc_rag: flow bundles
  min=223 median=553 max=1279 chars (≈ 345 tokens at ~3.7 chars/tok) — a micro
  model's whole window is plenty.
- **Model proposes, structure disposes:** accepted proposals become `Intent`
  nodes with evidence `LLMProposal` capped at **conf 0.5**
  (`SOURCE_CEILING["LLMProposal"]`), edge `SUPPORTS_INTENT`, metadata
  `origin:"llm"`, rationale, `llm_conf`. Deterministic evidence is never
  overwritten; already-covered intents are skipped.
- **Providers (zero-dep, ADR-002):** `OllamaProvider` (`/api/chat`, qwen3:0.6b),
  `OpenAICompatProvider` (`/v1/chat/completions`), `MockProvider` (deterministic,
  offline/tests). Probe gates the run; unreachable endpoint → exit 3 with a
  friendly message. Budget: timeout 30 s, no retries, failure → None (no error,
  artifact unchanged).
- **Lab (`lab/p9_lab.py`, doc_rag, offline → mock):** scope=all → 49 requests /
  49 proposals (10 flows + 39 units), 0 covered, 0 errors; ~0.004 s mock;
  deterministic across runs (ids+names+rationales identical).
- **Experiment seed (roadmap Phase 9, "ask-the-agent" baseline):** the lab writes
  `lab/p9_experiment_seed.jsonl` with questions × two contexts — *baseline*
  (raw unit names, naive agent) vs *SSRL-grounded* (deterministic evidence
  bundles) — to be answered and graded in the controlled RQ-3 study.
  Seed regenerated with q2 = "where is embed" (the original `save` has no symbol
  in doc_rag; gold must be derivable from facts).
- **Study — draft automated pass (executed live, `lab/p9_study.py`, qwen3:0.6b):**
  6 questions × 3 conditions (baseline / ssrl / deterministic layer-`ask`
  reference), entity-level F1 vs a facts-derived gold. Means: baseline 0.022,
  ssrl 0.338, layer 0.315; enumeration questions flip 0 → ssrl 0.84 (entry
  points) / 0.83 (deps). Pilot findings: grounded evidence is what makes a micro
  LLM answerable; the 0.6B stays format-fragile (refuses open extraction or
  echoes the asked entity — q2→`embed`, q3→`db`); prompt wording shifts which
  questions succeed, so the definitive study uses human grading + a mid-size
  model + closed-task arms (full plan: REPORT-P9 §6.1). Artifacts:
  `lab/p9_study_results.{json,md}`, `lab/p9_study_graded.jsonl`.
  Findings documented with the worst-case CPU-only hardware (REPORT-P9 §5.1).
- **Refusal probe battery (`lab/p9_probe.py`, REPORT-P9 §6.2):** A/B over
  evidence rendering (json vs answer-framed assertions) × prompt contract
  (lookup vs deterministic-CLI vs CLI+few-shot) × think on/off, classified
  reject/empty/answer + entity F1. Findings: (1) refusals were a **prompt
  artifact** — the CLI contract ("authoritative tool, reproduce verbatim, one
  per line, do not refuse") answered 30/30 where `lookup` slotted rejected q5 6/6;
  (2) best variant `json_cli` mean 0.61; `answer_*` scoring 1.00/0.65–0.68 are
  read-off ceilings; (3) answer-framed render had a **mutation bug** (JSON render
  popped `question` from shared rows so the assertion branches never fired) —
  fixed, results re-measured; (4) evidence size is the residual killer (q3's 30
  importer rows flooded the 0.6B → importer evidence noise-filtered to rows that
  import the asked module, 30 → 4); (5) temp 0 is not byte-reproducible (±0.3 F1
  run-to-run), so conclusions use variant means.
- **Context-system improvement + study re-run:** adopted the CLI agent contract
  in `lab/p9_study.py` and the importer evidence filter (`lab/p9_lab.py`), then
  re-ran the draft study live: **ssrl 0.338 → 0.613** (recall 1.0 on all 6
  questions) at lower prompt tokens (2631 vs 3173); baseline 0.022 → 0.153 (name
  soup + CLI + nondeterminism); layer unchanged 0.315. The seed was regenerated
  with the corrected evidence (`lab/p9_experiment_seed.jsonl`, q3 = 4 rows).
- **Tests:** `TestLLMProposer` (8) → suite **67 green** (compileall clean,
  determinism re-verified end-to-end).

---

## 9.5. Explainable AI for external coding agents (ADR-009)

**Goal (author directive):** developers no longer read or write code — coding AIs
do. The missing capability is **self-explanation** ("o que ela fez, o porquê,
como"); and the "pulo do gato" for moving from Python/JS to whatever the AI
produces next. Target: **external** coding AIs (Claude, Codex, …), not the
internal micro-LLM. Design-first: `ADR-009` written and ratified ("implemente")
before any code — **"the AI is the witness, the layer is the notary."**

**Surfaces added (all deterministic, stdlib-only, no model in the layer):**

| Piece | Where | What |
| --- | --- | --- |
| Auditor + WHAT/WHY/HOW | `ssrl/explain.py` (new) | `explain_node` / `explain_changed` (reuses `impact_changed`), `verify_explanation`, renderers. Citations: quoted identifiers → present/external/`invented`; unquoted identifier-like tokens resolve as hits and **never** count invented (non-resolving → `unresolved_tokens`); sentences citing nothing → `unsupported_claims`; asserted relations → structural consistency. Verdict PASS iff groundedness ≥ 0.8 and invented == 0, else REVIEW. No semantic entailment. |
| MCP tools | `ssrl/mcp.py` | `explain` (node XOR files) + `verify_explanation` (files + narration) |
| CLI verbs | `ssrl/cli.py` | `explain [--node] [--git]`, `verify [--git] [--explanation|--explanation-file]`; narration on stdin; `--json` |
| Tests | `tests/test_explain.py` (new) | 21 tests incl. MCP wiring (5) + determinism re-verification |
| Battery | `lab/p10_eai.py` + `p10_eai_seed.json` | 4 narrations on real change sets → `p10_eai_results.{json,md}` |

**Bugs found & fixed during 9.5:**

1. **`_IDENT_RE` had a capturing group** (`explain.py`): `re.findall` then
   returned the group content, so counts matched identifiers, not spans. Switched
   to `(?:…)` non-capturing groups.
2. **Dotted citations didn't resolve** (`explain.py`): `models.validate` matched
   nodes by name only. Now resolved across the token (final segment vs the
   dotted id, e.g. → `func::models::validate` first, then module-scoped name).
3. **CLI `call` regex was singular** (`cli.py`): `_CALL_STAGE_RE` matched
   `call()` only, not `calls()`. Made the plural-agnostic — real narrations
   ("it calls X") now consistency-check.
4. **`except Exception as ex` shadowed module `ex`** (`cli.py::cmd_verify`):
   Python binds `ex` over the module name in handler scope. Renamed to `exc`.
5. **`--node` was a positional arg** (`cli.py::cmd_explain`): design's `--node`
   flag also collided with argparse ambiguity. Made it an explicit flag.
6. **Module form didn't resolve** (`explain.py`): `module::db::db` style and
   bare `db` on module nodes missed via `idx.node`. Added module id / last-segment
   fallbacks.
7. **Double backticks noisy** (narration hygiene): `` ``x`` `` (markdown in
   prose) broke the quote tokenizer. Normalized ` `` ` → `` ` `` before tokenize.
8. **`_pair_consistent` was asymmetric** (`explain.py`): for-pair direction
   checks were one-sided. Made symmetric so a reversed-assertion pair is an
   inconsistency either way.

**Battery — Explainable AI validation (`lab/p10_eai.py`):**

Narrations authored by an **opencode subagent on model `opencode/big-pickle`**
(the synthetic coding AI, frontier-class) over live change sets of `ssrl` itself;
scenario `explain-fabricated-citation` is a deliberately dishonest narration
(references a `sanitize_claims` helper that does not exist).

| Scenario | Kind | Verdict | Groundedness | Present | Invented |
| --- | --- | --- | --- | --- | --- |
| explain-add-auditor | faithful | **PASS** | 1.0 | 3 | 0 |
| impact-add-projection | faithful | **PASS** | 1.0 | 3 | 0 |
| llm-provider-safety | faithful | **PASS** | 1.0 | 4 | 0 |
| explain-fabricated-citation | adversarial | **REVIEW** | 0.67 | 2 | 1 |

Ceiling **3/3** (faithful narrations reach groundedness 1.0, invented 0);
fabricated citation **1/1 caught**. Full write-up: `REPORT-P10.md`.

- **Tests:** 21 new → suite **88 green** (compileall clean; determinism
  re-verified by double-run asserts in `test_explain.py`).

---

## 9.6. Live demo fallout (coin-toss) — three issues found & fixed

After 9.5, a live demonstration ran the ADR-009 loop for real: an opencode
subagent acting as an external coding AI built an interactive "cara ou coroa"
CLI (`Downloads\coin_toss\coin.py` + `game.py`), ran the SSRL pipeline on it,
wrote its own WHY/HOW narration and audited it with `verify` (faithful → PASS
1.0; an adulterated narration inventing `coin.cheat_coin` → REVIEW, invented 2).
The demo surfaced three gaps, all fixed and regression-tested:

1. **Duplicate `IMPORTS` edges** (`extract.py`): `from coin import flip, other`
   emitted one edge per imported symbol, all collapsing to the same target
   module → duplicate `module::game → module::coin` and an inflated imports
   count (4 instead of 3). Fixed with an end-of-`build()` dedupe (covers both
   freshly-parsed and D-8 cached replay). Demo corpus: imports 4 → 3, edges
   17 → 16. Test `test_imports_deduped_per_module`.
2. **Auditor consistency grammar was EN-only** (`explain.py`): PT narrations
   resolved citations but `claims.checked` stayed 0 — asserted relations in
   Portuguese ("`X` chama `Y`", "depende de", "importa", "usa", "contém") were
   never consistency-checked against the artifact. Fixed: EN+PT relation
   patterns. Call forms deliberately narrowed (exact `usa`/`usam`/`usar`, not
   the gerund "usando") to avoid false positives. After the fix the faithful
   demo narration reports `claims.checked=2 failures=0`; the adulterated one
   `checked=2 unsupported=1` (still caught via invented citations). Tests
   `test_pt_relation_consistency_checked` / `_inconsistency_caught`.
3. **QA intent parser was EN-only** (`qa.py`): "quem chama flip" fell back to
   name lookup and "o que play_round chama" answered *"couldn't find `chama`"*.
   Fixed: PT question patterns (callers/callees/where/summary/imports/
   importers/deps/revdeps/entry/functions/classes/fluxos/ajuda) + PT stopwords
   in target extraction. Now the demo corpus answers both correctly. Tests
   `test_pt_callers` / `test_pt_callees` / `test_pt_where` / `test_pt_summary`.

**Verification:** suite 88 → **95 green**; battery re-run unchanged (ceiling
3/3, adversarial 1/1); demo evidence re-captured in
`Downloads\coin_toss\_evidence\`.

---

## 10. Remaining (post-Phase 9.5)

- Definitive RQ-3 study: human-graded multi-arm (Source-only vs Source+SSRL vs
  raw-agent), ≥ 3 graders, a mid-size model arm in addition to qwen3:0.6b,
  accuracy + time-to-understand (draft automated pass done — REPORT-P9 §6.1).
- Explainable-AI (ADR-009) outreach: real Claude/Codex-grade MCP integration
  session + larger narration battery to tune the PASS threshold from data
  (REPORT-P10 §8).
- H2 progressive-zoom drill-down and H4 graph navigation (supporting projections).
- Line-level/intra-file impact (whole-module today) and MCP resources/streaming.