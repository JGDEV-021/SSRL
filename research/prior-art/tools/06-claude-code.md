# Claude Code — Prior Art Note

> Research date: 2026-09-22 · Sources: code.claude.com/docs (subagents, agents, plugins-reference), Anthropic "Claude Code Advanced Patterns" PDF (resources.anthropic.com), third-party guides.

## What it is
Anthropic's **agentic CLI coding tool**. Not an IDE with autocomplete — an agent that reads files, runs commands (bash, terminal), and executes multi-step tasks; surfaces: terminal, GitHub Actions (Agent SDK), MCP tools.

## How it manages codebase understanding (the parts SSRL cares about)
- **Agentic exploration**: uses Explore subagent (read-only: Read/Grep/Glob/WebFetch/WebSearch) for file discovery/code search; Plan subagent for research in plan mode; general-purpose for explore+modify. Exploration results are kept **out of the main context window** (subagent has its own context; returns only a summary).
- **Subagents**: run in isolated context windows with custom prompts, tool allow/deny lists, permission modes; background by default; can be 3 layers deep; **forks** inherit the parent conversation. Purpose: keep verbose tool output (tests, logs, searches) out of the main conversation; parallelize independent work. Explicitly a *context-hygiene* mechanism.
- **Project memory / self-updating narrative**: **CLAUDE.md** (walks up the directory tree, project-scoped standing context; `.claude/rules/*.md` with path scoping), **skills** (reusable instructions, injected when relevant), **hooks** (deterministic pre/post-tool/command/session automation: auto-format, run tests after edits, backups), **MCP** (external tools/DBs/browser), **plugins** (bundled skills/agents/hooks/MCP/LSP).
- **Worktrees + agent teams + dynamic workflows** (scripted multi-subagent runs with cross-checks) for parallelization.

## Where comprehension stops
- Understanding is **per-session, per-agent, ephemeral**. The only persistent "knowledge" is hand-maintained **CLAUDE.md / rules** — i.e., a *manually curated* living narrative that rots if nobody maintains it (exactly the SSRL "narratives must be derived, not hand-maintained" premise).
- No fact graph, no call-level impact analysis, no confidence/evidence on answers; grounding relies on the model reading files at ask-time.
- Hooks are deterministic automation but *behavioral policy* (formatting/testing), not semantic comprehension.

## Relevance to SSRL
- Confirms the **contextwindow-budget** framing: modern agents spend engineering effort isolating *noise* (subagents), not *acquiring durable knowledge*. SSRL's layer removes that noise at the source (facts/precomputed evidence), so H1 Q&A over SSRL is a strictly better context source than agent-exploration.
- **CLAUDE.md = the manual precursor of H3** (living narrative) and H2 (zoom/overview); SSRL's derived-layer version removes the manual-maintenance failure mode. Strong supporting precedent: the *practice* already exists, only its automation is missing.
- **Hooks + MCP = the integration surface for SSRL Phase 8/9** (agent-facing): a PreToolUse hook can serve SSRL evidence to the agent; MCP can expose the layer. (Same conclusion as Cody/Cline.)
- Subagent context-isolation is a UI pattern to reuse in SSRL's H1 projection (answer grounded in separate window, evidence cited back).

## Licensing / constraints
Anthropic proprietary / subscription for Claude Code itself; the **Agent SDK & MCP protocol are open**. No components to embed. Behavior/architecture (docs) reusable as design reference.