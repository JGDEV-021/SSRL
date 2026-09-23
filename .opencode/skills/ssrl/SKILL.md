---
name: ssrl
description: Use when working on or answering questions about a Python codebase that has the SSRL semantic layer available (the `prototype/ssrl` package, `python -m ssrl.cli ...` / `ssrl.mcp` MCP server, the `explain`/`verify_explanation` auditor, the `deleted` history view, ADR-009). Use it to ground every claim about code structure, to size the blast radius of a planned change, and to write auditable self-explanations after editing. Do NOT use for SSRL's own internals.
---

# SSRL — Semantic Software Representation Layer

SSRL is a dependency-free, deterministic layer over Python code: structural
**facts** (confidence 1.0) plus labeled semantic **hypotheses** (calibrated
confidence, evidence-backed). The agent surface speaks the ADR-009 contract:
**the AI is the witness, the layer is the notary.**

This skill is the machine-readable companion to `HowToUse.md` and
`AI LAYER/`. Load it whenever you touch code that SSRL can see.

## When you use it

- Any question of the form "what does this do / who calls X / what imports X /
  what breaks if I change X / entry points / flows".
- Before editing an SSRL-indexed file (get the blast radius first).
- After editing, to write and audit your self-explanation.

## Grounding rules (never skip)

1. Facts and hypotheses never mix. The layer labels them; do the same.
   A hypothesis is not a fact, no matter how plausible.
2. Quote identifiers you cite: `` `name` `` / `"name"` / `'name'`. Only quoted
   identifiers count as citations for the auditor.
3. Never quote a symbol you have not verified against the artifact.
4. Never settle for a REVIEW verdict.

## Command recipes

All run from `prototype/` (package not installed; stdlib only). `<repo>` is an
absolute path. If an MCP server is configured, prefer the equivalent tools.

| Intent | CLI | MCP tool |
| --- | --- | --- |
| Overview + parse health | `python -m ssrl.cli stats <repo>` | `stats` |
| Build semantic hypotheses | `python -m ssrl.cli enrich <repo>` | (auto on `--enrich` server) |
| Grounded Q&A (EN/PT) | `python -m ssrl.cli ask <repo> "who calls X"` | `ask` |
| Narrative (H3) | `python -m ssrl.cli narrative <repo> [--json]` | `narrative` |
| Blast radius of a change | `python -m ssrl.cli impact <repo> path/file.py [--git BASE]` | `impact` |
| Deleted-symbols view | `python -m ssrl.cli deleted <repo> [--json] [--cache]` | `deleted` |
| Explain a node / change | `python -m ssrl.cli explain <repo> --node func::x::y` | `explain` |
| Audit a narration | `python -m ssrl.cli verify <repo> file.py --explanation-file n.txt` | `verify_explanation` |
| Hypothesis proposal (optional) | `python -m ssrl.cli propose <repo> --mock` | — |

Example reasoning against the layer, using quoted identifiers:

```
impact: "func::io::compress touches 2 modules, 1 importer (module::io_utils),
3 reverse callers, entry point func::bench::main, flow: env inbound"
→ cite exactly those ids in the narration.
```

## The audit contract (`verify_explanation`, deterministic)

- Quoted identifier resolves in artifact → `present`.
- Quoted identifier matches an external import → `external` (never invented).
- Quoted identifier resolves to a recently-deleted symbol (history view) →
  `deleted` (real removal, not invented).
- Quoted identifier resolves to nothing → `invented` (fabrication).
- Sentence citing nothing → `unsupported`.
- Asserted relation (`calls`, `imports`, `uses`, `depends on`, `contains` —
  **EN and PT**) → consistency-checked against the edge set.

**Verdict:** `PASS` iff `groundedness >= 0.8` **and** `invented == 0`, else
`REVIEW`. Groundedness = `present / (present + invented)` (external/deleted
excluded). The default threshold sits in the battery-measured safe band
(`prototype/lab/p10_eai_results.md`).

**Workflow after editing a file:**
1. `impact <repo> <file>` — scope.
2. `deleted <repo> --cache` — if you removed symbols.
3. Write narration with quoted identifiers.
4. `verify <repo> <file> --explanation-file n.txt`.
5. Resolve every REVIEW: fix invented quotes (`ask`/`explain` to find the real
   id), and give unsupported sentences a citation or drop them.

## PT support

The Q&A intent parser and the relation grammar accept Portuguese (`quem chama`,
`o que faz`, `importa`, `usa`, `depende de`, `contém`). English always works.

## Canonical references

- ADR-009: `research/decisions/ADR-009-explainable-ai-external-agents.md`
- Battery + results: `prototype/lab/p10_eai.py`, `prototype/REPORT-P10.md`
- Human guide: `HowToUse.md`; agent guide: `AI LAYER/README.md` and
  `AI LAYER/MCP-CONNECT.md`