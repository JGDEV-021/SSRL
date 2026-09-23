# AI LAYER

> How to teach a coding AI to use SSRL — and how to connect it over MCP.
> "The AI is the witness, the layer is the notary" (ADR-009).

This folder is written **for the AI that will read a codebase** (opencode,
Claude, Codex, Cline, Copilot), not for the SSRL implementer. It assumes SSRL is
already installed/available and answers two questions:

1. **How do I (an AI) correctly use SSRL to understand, change, and explain a
   codebase?** → [start here](#the-onboarding-recipe)
2. **How is the MCP server connected so the AI can call the layer at all?**
   → [`MCP-CONNECT.md`](MCP-CONNECT.md)

---

## The onboarding recipe (for an AI agent)

Read this list in order. It takes an agent from "I can see files" to "I can
answer *what this system does, what breaks if I change X, and what I did — with
proof*".

### Step 0 — Locate the layer

- If you are an opencode agent in this repository, load the bundled **`ssrl`**
  skill (`.opencode/skills/ssrl/SKILL.md`) — it encodes everything below.
- Otherwise, use the CLI: `cd prototype && python -m ssrl.cli --help`.
- If an MCP server is configured, prefer MCP tools (`stats`, `ask`, `impact`,
  `explain`, `verify_explanation`, `deleted`) over ad-hoc file reading.

### Step 1 — Calibrate ground truth before judging

Never trust your memory of a codebase. The layer is the source of structural
truth. Start any task with:

```console
python -m ssrl.cli stats   <repo>
python -m ssrl.cli ask     <repo> "who calls X" / "what does X do"
```

Ask closed, checkable questions. The answer splits **facts** (definitely true)
from **hypotheses** (plausible, with confidence). Treat hypotheses as
hypotheses; never present a hypothesis as a fact.

### Step 2 — Before you change anything, map the blast radius

```console
python -m ssrl.cli impact <repo> path/to/file.py
python -m ssrl.cli deleted <repo> --cache   # only if you may remove symbols
```

`impact` names modules, importers, reverse callers, entry points and flows the
change touches. This is the skeleton of a correct "what breaks if I change X"
answer.

### Step 3 — After the change, narrate against the layer

Write your self-explanation **with quoted identifiers** (`` `name` `` /
`"name"` / `'name'`) — every quoted identifier becomes an auditable citation.
Never quote a symbol you did not verify against the artifact. Unquoted names
are only heuristic; they do not count as citations.

### Step 4 — Audit yourself before you answer

```console
python -m ssrl.cli verify <repo> file.py --explanation-file narration.txt
```

Apply the verdict contract mechanically:

- `invented > 0` → you fabricated something. Fix it. **Never ship a REVIEW.**
- `unsupported` sentences → add a real citation or drop the claim.
- Node/relation consistency violations → you described structure wrong. Recheck
  with `ask`/`explain`.
- `PASS` requires `groundedness >= 0.8` **and** `invented == 0`.

The layer can tell a grounded self-explanation from a fabricated one. Use it.

### Step 5 — What the layer will never do for you

The layer answers *what*, *who*, *how*, *what breaks* — with doubts marked.
It does not replace your judgment on *why the change is worth making*. That
intent belongs to the human; keep your narration honest about the difference.

---

## Prompt template (paste into any coding AI)

If you cannot ship the skill, paste this into the agent's system prompt:

> Always ground your claims about this codebase in the SSRL layer.
> Run `cd prototype && python -m ssrl.cli stats <repo>` and
> `python -m ssrl.cli ask <repo> ...` before answering "what does this do" or
> "what breaks if I change X". Before changing a file, run
> `python -m ssrl.cli impact <repo> path/file.py`. After changing it, write
> your self-explanation with quoted identifiers and run
> `python -m ssrl.cli verify <repo> path/file.py --explanation-file n.txt`.
> You must resolve every REVIEW: never narrate an unverified identifier
> (`invented`) and never leave a claim without a citation (`unsupported`).
> Facts and hypotheses are never the same: label uncertainty.

---

## Contents

- [`MCP-CONNECT.md`](MCP-CONNECT.md) — wire the MCP server into opencode,
  Claude Code, Cline, Cursor.
- Bundled opencode skill: `.opencode/skills/ssrl/SKILL.md` (this whole recipe,
  machine-readable, auto-loadable).
- Human starting point: [`../HowToUse.md`](../HowToUse.md).