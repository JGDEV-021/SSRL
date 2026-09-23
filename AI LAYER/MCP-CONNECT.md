# Connecting the SSRL MCP server

The SSRL MCP server exposes the whole layer surface to coding agents over
**stdio**: `ask`, `why`, `narrative`, `stats`, `audit`, `impact`, `explain`,
`verify_explanation`, `deleted`.

```
python -m ssrl.mcp --repo <absolute-path-to-corpus> [--enrich] [--cache]
```

- The package lives in `prototype/ssrl/`. Run the server from `prototype/` (or
  set `PYTHONPATH` to `prototype`), since it is stdlib-only and not pip-installed.
- `--enrich` builds hypotheses on first contact (warm-up). Without it, tools
  that need semantics still trigger a build on demand.
- `--cache` enables the incremental cache (D-8) so reconnects are fast.
- The server **never writes to the corpus**; all derived data lives in the
  per-repo cache.
- Windows: set `PYTHONUTF8=1` so non-ASCII paths/names survive stdio.

### Verify it is alive (MCP inspector / any MCP client)

`tools/list` must return the nine tools above. A smoke call:

```
tools/call  name: "stats"  arguments: {}
```

---

## opencode

Add to `opencode.json` (project or user) — repo is a *list* of the command
argv; use the `cwd`/absolute path pointing at `prototype`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "ssrl": {
      "type": "local",
      "command": ["python", "-m", "ssrl.mcp", "--repo", "C:\\abs\\path\\to\\corpus", "--enrich", "--cache"],
      "enabled": true
    }
  }
}
```

Opcodes note: `command` is an argv array (not a shell string). After editing the
config, restart opencode — MCP config is not hot-reloaded.

In this repository the matching project config is `.opencode/` (see
`.opencode/skills/ssrl/SKILL.md` for the agent-side workflow).

## Claude Code

```console
claude mcp add ssrl -- python -m ssrl.mcp --repo C:\abs\path\corpus --enrich --cache
```

(from `prototype/`, or prefix the command with your `python` path.)

## Cline / Cursor

Add an MCP server of type **stdio** with command:

```text
python -m ssrl.mcp --repo C:\abs\path\corpus --enrich --cache
```

working directory: `C:\Users\joaog\Downloads\SSRL\prototype`.

## Calling order that gets auditable answers

1. `stats` — one look at scale + parse health.
2. `ask` / `why` — grounded Q&A, facts split from hypotheses.
3. `impact` — blast radius before a change.
4. `deleted` — view symbols removed since the previous build.
5. `explain` — grounded WHAT/WHY/HOW for a node or change.
6. `verify_explanation` — **audit your own narration**: PASS iff
   `groundedness >= 0.8` and `invented == 0` (ADR-009).