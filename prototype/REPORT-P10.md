# REPORT-P10 — Phase 9.5: Explainable AI for External Coding Agents (ADR-009)

**Version:** v0.7.0 · **Date:** 2026 · **Status:** complete — ADR-009, the
deterministic self-explanation surface (`explain` + `verify_explanation`, MCP &
CLI) and the initial Explainable-AI battery executed with an opencode big-pickle
subagent as the synthetic coding AI
**Governance:** roadmap.md **Phase 9.5** (Explainable AI for external coding
agents); **ADR-009** (new — grounded self-explanation contract + explanation
auditor); extends ADR-006 (D-7: CLI first, MCP second) and ADR-007/ADR-008
"model proposes, structure disposes" to the *external* process.

---

## 1. Goal & the author directive

The author's strategic reframe (verbatim direction):

> "o problema hoje é que os devs não leem mais o código, e não escrevem mais.
> AIs de hoje não exigem que você escreva. O que falta é o **Explainable AI** —
> a capacidade de uma IA de se **auto-explicar**: o que ela fez, o porquê ela
> fez, como ela fez daquela maneira. É nesse ponto que a gente tem que melhorar
> MUITO, e esse é o pulo do gato para a gente transicionar do Python/JavaScript
> para QUALQUER outra coisa que a IA fizer." — and clarified: **external coding
> AIs** (Claude, Codex, …) and the **external process**, not the micro model
> inside SSRL.

Design-first: ADR-009 was written and ratified before any code (§2). The chosen
lane is "the AI is the witness, the layer is the notary": the external coding AI
writes its natural-language self-explanation (why/how), but the WHAT always comes
from the structure, and the WHY/HOW is treated as an *audited claim*, never as
truth.

## 2. ADR-009 — the design (ratified first)

`research/decisions/ADR-009-explainable-ai-external-agents.md` fixes:

- **Contract:** every audited explanation is a WHAT (structural, from
  `impact`/index) / WHY (AI narration as a claim + SSRL evidence trail) / HOW
  (derivation trail: build → enrich → propose → projections).
- **Audit rules:** quoted identifiers are **citations** → *present* (resolves to
  an artifact id), *external* (resolves to an external import target), or
  *invented* (fabricated reference). Unquoted identifier-like tokens resolve as
  hits and **never** count as invented. Sentences citing nothing are
  **unsupported claims**; sentences asserting a relation are structurally
  consistency-checked (does the claimed calls/imports/contains edge exist?).
- **Honest ceilings:** no semantic entailment (a narration can be fully grounded
  and state the wrong reason); identifier extraction is heuristic.
- **Battery design:** narrations drafted by an **opencode subagent running
  `opencode/big-pickle`** as the synthetic external coding AI (frontier-class,
  not the layer's 0.6B proponent); ground-truth faithful narrations form the
  ceiling (must reach groundedness 1.0, invented 0); an adversarial narration
  must be caught (REVIEW + invented > 0).

## 3. Implementation map

| Piece | Where | Notes |
| --- | --- | --- |
| Auditor + WHAT/WHY/HOW | `ssrl/explain.py` (new) | `explain_node` / `explain_changed` / `verify_explanation` + renderers; stdlib, deterministic, no model |
| MCP tools | `ssrl/mcp.py` | `explain` (node XOR files) + `verify_explanation` (files + narration) |
| CLI verbs | `ssrl/cli.py` | `explain [--node] [--git] [--json]`, `verify [--git] [--explanation|--explanation-file] [--json]`; narration via stdin |
| Tests | `tests/test_explain.py` (new) | 21 tests incl. MCP wiring; `test_mvp.py` tool list updated |
| Battery | `lab/p10_eai.py` + `lab/p10_eai_seed.json` | results → `lab/p10_eai_results.{json,md}` |

The auditor is a pure function of (artifact, files, narration): deterministic,
JSON-safe, all evertebrate lists sorted. The layer's internal micro-LLM
(ADR-008) is untouched.

## 4. The self-explanation loop (as an external coding AI would use it)

```
coding AI edits repo                (Claude / Codex / Cline / Copilot …)
   -> ssrl watch / impact           build artifact on HEAD
   -> SSRL WHAT                     deterministic impact bundle (unchanged facts)
   -> coding AI writes WHY/HOW      natural-language narration (its own words)
   -> SSRL verify_explanation       auditor -> PASS/REVIEW + groundedness
   -> grounded report               what = structure, why/how = claimed + verified
```

A Claude Code / Cline / Cursor session reaches this natively through the MCP
tools; a developer pastes the same narration into `ssrl verify --git main`.

## 5. Battery — Explainable AI validation (`lab/p10_eai.py`)

Scenarios are real change sets on the prototype itself (`ssrl/explain.py`,
`ssrl/impact.py`, `ssrl/llm.py`). Narration authorship is recorded in the seed
and results: **drafted by an opencode subagent on model `opencode/big-pickle`**
acting as the synthetic coding AI; the auditor is deterministic and never
consulted a model.

| Scenario | Kind | Verdict | Groundedness | Present | Invented | Scope |
| --- | --- | --- | --- | --- | --- | --- |
| explain-add-auditor | faithful | **PASS** | 1.0 | 3 | 0 | 2/3 |
| impact-add-projection | faithful | **PASS** | 1.0 | 3 | 0 | 3/3 |
| llm-provider-safety | faithful | **PASS** | 1.0 | 4 | 0 | 4/4 |
| explain-fabricated-citation | adversarial | **REVIEW** | 0.67 | 2 | 1 (`sanitize_claims`) | 2/2 |

Aggregate: **ceiling = True (3/3 faithful narrations reach groundedness 1.0 with
zero invented citations); adversarial fabricated reference = 1/1 caught.**
The auditor dropped groundedness to 0.67 and flagged `verify_explanation`'s
invented delegate `sanitize_claims` — exactly the fabrication class Phase 9
warned about, now measurable on the external process.

## 6. Verification

- **Tests:** 95 green (incl. MCP wiring for both new tools, determinism
  double-runs, empty-narration REVIEW, the external-import-not-invented case,
  the PT relation-consistency pair, PT QA routing and the IMPORTS-dedupe
  regression).
- **CLI e2e:** `ssrl explain <repo> --node func::db::save` (WHAT/WHY/HOW with
  callers/callees + deriving stage) and `ssrl verify <repo> file.py
  --explanation-file narration.txt` → `VERDICT: PASS groundedness=1.0
  invented=0` over the fixture corpus.
- **Determinism:** identical inputs → byte-identical result dicts (unit-tested).

## 7. Honest limits

- **No semantic entailment.** Groundedness is about *references* (real symbols,
  real relations), not whether the stated reason is the right reason. A coding AI
  can be grounded and wrong. This is a designed ceiling (§2), not a bug.
- **Identifier extraction is heuristic.** Unquoted CamelCase / snake_case /
  dotted tokens are resolved when they hit the artifact; only *explicitly
  quoted* strings can ever be flagged invented — which keeps the metric fair at
  the cost of some misses (conservative by design).
- **Consistency checks are token-level.** A sentence asserting "X calls Y" is
  checked against the artifact's edge set; phrasing nuances are not parsed.
  False-PASS is possible when the mentioned relation doesn't square with the
  verb (e.g. "removed the call to X" is not parsed as a removal).
- **Single-artifact context.** The auditor reasons over the current artifact
  (ADR-003); narrations about pre-HEAD state (deleted code) naturally cite
  symbols the layer no longer has → the review team must read those as
  "recently deleted", which is visualized via `impact`'s missing-module path.

## 8. Open items (Phase 10)

- Real Claude/Codex-grade integration day: wire the MCP server into an agent
  session (Claude Code / Cline) and collect naturally-produced narrations for a
  larger battery.
- Verdict threshold tuning from data (0.8 / invented==0 is the v0.8 default,
  per ADR-009 §5).
- Reference a "deleted-symbols" view (from `watch` history) so narrations about
  removals are audit-able instead of missing-module REVIEW noise.
- The definitive Phase 9 human-graded multi-arm study is unchanged and still
  required for the publication claims (see REPORT-P9 §6.1).

## 9. Live demo — three fixes shipped

A real external-coding-AI loop (an opencode subagent building an interactive
"cara ou coroa" CLI and self-explaining against SSRL, faithful → PASS 1.0,
an adulterated narration inventing `coin.cheat_coin` → REVIEW, invented 2)
surfaced three gaps that the static battery hadn't stressed:

1. **Duplicate `IMPORTS` edges** — `from coin import flip, other` emitted one
   edge per imported symbol, all collapsing to the same target module
   (imports 4 instead of 3 on the demo corpus). Fixed with an end-of-`build()`
   dedupe covering fresh and D-8 cached paths (`extract.py`).
2. **Auditor relation grammar was EN-only** — PT narrations resolved citations
   but `claims.checked` stayed 0, so asserted relations like "`X` chama `Y`"
   were never consistency-checked. Fixed with EN+PT patterns (`explain.py`);
   call forms narrowed (exact `usa`, not the gerund "usando") to avoid false
   positives. Post-fix, the faithful narration shows `checked=2 failures=0`
   and the adulterated one `checked=2 unsupported=1`.
3. **QA intent parser was EN-only** — "quem chama flip" fell back to name
   lookup and "o que play_round chama" answered *couldn't find `chama`*.
   Fixed with PT question patterns + PT stopwords (`qa.py`); the demo corpus
   now answers both correctly.

Each has a regression test; battery re-run unchanged (ceiling 3/3,
adversarial 1/1); suite 88 → **95 green**. Full trace: BUILDLOG §9.6.

## 10. To run

```console
python -m unittest tests.test_mvp tests.test_explain        # 95 tests
python -m ssrl.cli explain tests/fixtures/pkgapp --node func::db::save
printf 'I changed `db.py`: `save` now calls `models.validate`.' | \
  python -m ssrl.cli verify tests/fixtures/pkgapp db.py
python lab/p10_eai.py                                       # battery, writes results
```

The battery is deterministic given the seed: narrations (authored by
opencode/big-pickle) are checked into `lab/p10_eai_seed.json` so results are
reproducible without any model at runtime.