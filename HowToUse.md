# How To Use SSRL

**SSRL = Semantic Software Representation Layer.** A deterministic,
evidence-backed representation of Python codebases: structural *facts*
(confidence 1.0) plus labeled semantic *hypotheses* (calibrated confidence),
surfaced through a grounded Q&A, a living narrative, CI impact reports, and —
since Phase 9.5 — a grounded **self-explanation + audit** surface for coding AI
agents ("the AI is the witness, the layer is the notary", ADR-009).

This guide is the practical entry point for **humans and AI agents**. For the
deeper "how do I teach an AI to use this" material, see the
[`AI LAYER/`](AI%20LAYER/README.md) folder. If you are an opencode agent working
in this repository, load the bundled `ssrl` skill (`.opencode/skills/ssrl/`)
instead of reading this file ad hoc.

---

## 0. Requirements

- Python 3.10+ (developed on 3.13). **Zero dependencies** — stdlib `ast` (ADR-002).
- Nothing to install: the package lives in `prototype/ssrl/` and runs with
  `python -m ssrl.cli ...`.

All commands below assume:

```console
cd prototype
```

## 1. Cold start — 60 seconds to first value

```console
python -m ssrl.cli stats    <repo>            # fact-model stats (fast, deterministic)
python -m ssrl.cli enrich   <repo>            # build + semantic hypotheses
python -m ssrl.cli ask      <repo> "who calls search"
python -m ssrl.cli narrative <repo>           # the living narrative (H3)
```

`<repo>` is any directory with `.py` files. SSRL never writes to your corpus —
everything lands in a per-repo cache under `~/.ssrl/cache` (D-8 incremental
cache, warm rebuilds for free).

Use `--cache` on individual commands to opt into the same incremental cache.

## 2. The projections

| Command | What it gives you | Details |
| --- | --- | --- |
| `ask <repo> "question"` | Grounded Q&A (H1) — facts split from hypotheses | `where is X`, `who calls X`, `what does X do`, `imports of X`, `entry points`, `flows` (EN and PT) |
| `narrative <repo>` | Living narrative (H3) | Overview, entry points, module map, key flows, parse health |
| `impact <repo> file.py [--git main]` | "What does this PR affect?" | modules, importers, callers that may break, entry points, flows, reverse deps |
| `deleted <repo> --cache` | **Deleted-symbols view** (Phase 10) | modules / symbols / relations removed since the previous cached build |
| `explain <repo> --node func::x::y` | Grounded WHAT/WHY/HOW | for one node *or* a change set |
| `verify <repo> file.py --explanation-file n.txt` | Explanation **auditor** | groundedness + PASS/REVIEW |
| `json <repo> --out art.json [--enrich]` | Full artifact export | deterministic, JSON-safe |
| `propose <repo> --mock` | Micro-LLM hypothesis proposals (optional, ADR-008) | hypotheses only, confidence ≤ 0.5 |
| `watch <repo> --enrich` | Continuous no-manual-sync regeneration | poll + delta-only re-parse |

## 3. The Explainable-AI axis (ADR-009) — how to self-explain correctly

When you are a coding agent that just changed a file and must explain yourself:

1. **Ground first.** Run `impact <repo> file.py` (or MCP `impact`) for the
   change scope, and `deleted <repo> --cache` if you removed anything.
2. **Narrate with quoted identifiers.** The auditor treats only *explicitly
   quoted* identifiers (`` `name` `` / ``"name"`` / `'name'`) as citations.
   Unquoted names resolve as heuristics and are never audited as citations.
3. **Audit yourself:** `verify <repo> file.py --explanation-file narration.txt`.

Auditor contract (all deterministic, no model):

- A quoted identifier that **resolves** in the artifact → `present`.
- A quoted identifier that matches an **external import** → `external` (not invented).
- A quoted identifier that resolves to a **recently-deleted symbol** (history
  view) → `deleted` (real removal, not invented).
- A quoted identifier that **resolves to nothing** → `invented` (fabricated).
- A sentence citing nothing → `unsupported`; a sentence asserting a relation
  (`calls`, `imports`, `uses`, `depends on`, `contains` — **EN and PT**) is
  **consistency-checked** against the artifact's edge set.

**Verdict:** `PASS` iff `groundedness >= 0.8` **and** `invented == 0`, else
`REVIEW`. Groundedness = `present / (present + invented)` (external and deleted
citations are excluded). The default threshold sits inside the safe band
measured by the battery — see `prototype/lab/p10_eai_results.md`.

Narrate via `--explanation-file`, `--explanation "..."` or stdin. With
`--git BASE`, the change set is read from git automatically.

## 4. MCP — connect a coding agent

The MCP server (`python -m ssrl.mcp --repo <repo> [--enrich]`) exposes the full
surface over stdio: `ask`, `why`, `narrative`, `stats`, `audit`, `impact`,
`explain`, `verify_explanation`, `deleted`. Step-by-step wiring for opencode,
Claude Code, Cline, and Cursor is in
[`AI LAYER/MCP-CONNECT.md`](AI%20LAYER/MCP-CONNECT.md).

## 5. Teach an AI agent to do this

See the [`AI LAYER/`](AI%20LAYER/README.md) folder: the full recipe to onboard a
coding AI onto the layer (contract, prompt template, workflow), the MCP
connection guide, and the bundled opencode skill.

## 6. Tests & verification

```console
python -m unittest discover -s tests -v     # 104 tests, stdlib unittest
python lab/p10_eai.py                        # Explainable-AI battery (writes results)
```

Determinism (NFR-4): identical inputs → byte-identical node/edge sets. The
battery is seeded (`lab/p10_eai_seed.json`) and runs without any model.

## 7. Artifact shape (ADR-003 — derived, regenerable)

```
nodes: Repository, Module, Class, Function, Method   (facts, confidence 1.0)
       Flow, Intent, Service, DomainConcept          (hypotheses, confidence < 1.0)
edges: CONTAINS, IMPORTS, CALLS                      (facts)
       PARTICIPATES_IN, SUPPORTS_INTENT, RELATED_TO  (hypotheses)
ids:   module::<mid> · class::<mid>::<name> · func::<mid>::<name>
```

Plus, when building with a cache dir, `artifact["deleted"]` carries the
deleted-symbols view (has_history, modules/symbols/relations removed).

## 8. Where everything lives

| File | Purpose |
| --- | --- |
| `prototype/README.md` | Prototype quick start + verified properties |
| `prototype/ssrl/` | The package (stdlib only) |
| `prototype/BUILDLOG.md` | Per-phase build log |
| `prototype/REPORT-V1.md` / `REPORT-P7..P10.md` | Delivery + phase reports |
| `docs/` | Vision, concepts, requirements, architecture |
| `research/decisions/` | ADR-001…009 |
| `AI LAYER/` | How to teach an AI to use SSRL + MCP connection |
| `.opencode/skills/ssrl/` | Bundled opencode skill for agents |