# REPORT-P8 — Phase 8: End-to-End & Agent/AI Surface

**Version:** v0.6.0 · **Date:** 2026 · **Status:** complete
**Governance:** roadmap.md Phase 8; ADR-006 (CLI first, MCP second) — this phase
delivers the v1.5 MCP surface plus the CI impact report ADR-006 deferred as a
*supporting* surface.

---

## 1. Goal & success criteria

- Goal: complete the pipeline plus an AI consumer — *code → facts →
  hypotheses → primary projection (Q&A + narrative), incrementally*.
- Success criterion: **humans and agents consume the same layer coherently.**

## 2. What was built

| Component | File | Notes |
| --- | --- | --- |
| Impact report ("what does this PR affect?") | `ssrl/impact.py` | deterministic, JSON-safe |
| MCP server (zero-dep, stdio) | `ssrl/mcp.py` | JSON-RPC 2.0, newline-delimited transport |
| CLI wiring | `ssrl/cli.py` | `impact` + `mcp` subcommands |
| Lab driver (scripted MCP session) | `lab/p8_lab.py` | live corpus |
| Version bump | `ssrl/__init__.py` | 0.5.0 → 0.6.0 |

### 2.1 `impact` — CI impact report (supporting surface)

`impact_changed(artifact, changed_files)` maps repo-relative changed files to
their module nodes (`module_id`) and computes the blast radius from the index:

- **affected modules** — the changed module(s) + their contained symbols;
- **importers** — who directly imports a changed module;
- **callers** — functions that CALL a changed function/method ("may break");
- **entry points touched** — changed symbols that are public entry points
  (`index.entry_points()`) → the PR touches public API;
- **flows affected** — Flow hypotheses (calibrated) whose *entry* or *steps*
  pass through changed code;
- **reverse dependencies** — transitive IMPORTS + CALLS dependents.

CLI: `ssrl impact <repo> FILES... [--git BASE] [--json] [--no-enrich]`.
`--git BASE` combines with `git diff --name-only BASE` so it drops into CI.
Deterministic: all lists sorted, node ids stable (ADR-003).

### 2.2 `mcp` — agent/AI surface (ADR-006 v1.5)

A dependency-free MCP server over **stdio** (stdlib only, ADR-002):
JSON-RPC 2.0 messages, **newline-delimited JSON** transport (the MCP stdio
boundary — no Content-Length framing). Handshake:

| Direction | Message | Server response |
| --- | --- | --- |
| client → | `initialize` | protocolVersion, capabilities.tools, serverInfo |
| client → | `notifications/initialized` | *(none)* |
| client ⇄ | `ping` | `{}` |
| client → | `tools/list` | 6 tool schemas |
| client → | `tools/call` | `{content:[{type:text}]}` or `{isError:true}` |

Tools (each answer grounded, evidence-preserving — RQ-3):

| Tool | Args | Returns |
| --- | --- | --- |
| `ask` | `question` | grounded Q&A: FACTS (conf 1.0, file:line) separated from HYPOTHESES (calibrated conf) |
| `why` | `node` | evidence behind a node id (id → [FACT] + source) |
| `narrative` | — | living narrative (H3) |
| `stats` | — | fact-model stats (files/reparsed/from_cache/nodes/edges/…) |
| `audit` | — | calibration table (every hypothesis, conf + note) |
| `impact` | `changed_files` | the §2.1 CI impact report |

Launch (both work): `python -m ssrl.mcp --repo <root> [--enrich]` or
`ssrl mcp <repo> [--enrich]`. Cache is **on by default** (`--no-cache` to
disable): warm incremental builds (D-8), same cache dir as other commands;
the server never writes to the corpus (NFR-5). One repo context per server.

## 3. Lab: scripted MCP session on a real corpus (doc_rag, 31 files, enrich)

```
[handshake] initialize -> protocolVersion=2025-06-18 server=ssrl-mcp
[tools/list] ask,why,narrative,stats,audit,impact
> ask  {question: 'who calls init_db'}
Callers of `init_db`: build, embed, stats, purge, search, index_scripts,
remove_project_scripts (7 facts, confidence 1.0).
FACTS: Function `build` (indexer.py:275) … search (retriever.py:197) …
> stats
files=31 reparsed=0 ok=31 errors=0 from_cache=31 elapsed_s=0.374
nodes=306 edges=741 functions=204 imports=227 calls=209
> impact {changed_files: ['context.py', 'db.py']}
2 changed file(s); 2 module(s) affected; 6 direct importer(s);
28 caller(s) may break; 3 entry point(s) touched; 3 flow(s) affected.
  module context (context.py): id module::context (3 symbol(s))
  module db (db.py): id module::db (8 symbol(s))
  imports context: module::cli …    imports db: module::indexer, …
  callers of func::db::connect: … (12 callers, incl. func::indexer::build, …)
  entry point touched: func::context::search_for_context …
  flow affected: flow::func::context::search_for_context …
  reverse dependency: module::benchmark … module::scripts
> why {node: 'init_db'}            -> [FACT] func::db::init_db: … evidence db.py:92
> audit                             -> 62 calibration rows
> narrative                         -> 259 lines
```

Server startup on a warm cache: **0.37 s** to first tool answer; handshake
completes before any build work (build is lazy, on first `tools/call`).

### Coherence check (Phase 8 success criterion)

The same question, `"who calls init_db"`, answered through **CLI** and through
the **MCP `ask` tool** against the same layer:

```
CLI head: 'Callers of `init_db`: build, embed, stats, purge, search,
           index_scripts, remove_project_scripts (7 facts, confidence 1.0)'
MCP contains the same head  ->  coherent: True
```

### CI smoke on SSRL itself

`ssrl impact .. --git main` (our own PR vs `main`): 3 changed files →
3 modules, 36 callers may break, 11 entry points touched, 9 flows affected —
a working drop-in CI report.

## 4. Verification

- **67 unit tests green** (~0.7 s), including `TestImpact` (5), `TestMCPServer`
  (13: handshake, notification, ping, tools/list, each tool, unknown
  tool/method, parse-error, stdio round-trip) and `TestLLMProposer` (8, added
  in Phase 9).
- TestImpact regression locked real bug: duplicate importer rows (two IMPORTS
  edges) — `_node_ids` now dedupes.
- Determinism re-verified on doc_rag (identical artifacts across runs).
- `compileall` clean.

## 5. Honest limits

- **Impact granularity is per-module** (whole file → module node); intra-file /
  line-level analysis is deferred (roadmap Phase 10 projections).
- The MCP server is stdio-only with a single repo context; protocol pinned to
  `2025-06-18`. Deferred: LSP/IDE, resources with full artifact read, streaming.
- `impact --git BASE` relies on the `git` binary and resolves the *working-tree*
  diff against `BASE` (it does not fetch).