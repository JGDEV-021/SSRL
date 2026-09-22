"""SSRL MCP server (Phase 8) — agent/AI surface (ADR-006 v1.5).

A dependency-free MCP (Model Context Protocol) server over stdio using only the
stdlib: JSON-RPC 2.0 messages with newline-delimited JSON transport
(no Content-Length framing — the MCP stdio transport).

Handshake: `initialize` -> `notifications/initialized`, then `tools/list` and
`tools/call`. Every tool answer carries provenance (RQ-3): facts are kept
separate from calibrated hypotheses (confidence model, ADR-005 H1/H3).

Tools (each answer is grounded, deterministic text):
  ask(question)           grounded Q&A — facts + hypotheses separated
  why(node)               evidence behind a node id
  narrative()             living narrative (H3)
  stats()                 fact-model statistics
  audit()                 calibration table (every hypothesis + its confidence)
  impact(changed_files)   CI impact report: "what does this PR affect?"

Launch:  python -m ssrl.mcp --repo <root> [--enrich]
Cache is on by default (warm incremental builds, D-8); never touches the corpus.
"""

import argparse
import json
import os
import sys

from . import confidence, extract, index as indexmod, narrative as narr, qa
from . import impact as impactmod
from . import semantics

PROTOCOL_VERSION = "2025-06-18"
VERSION = "0.6.0"
DEFAULT_CACHE = os.path.join(os.path.expanduser("~"), ".ssrl", "cache")

TOOLS = [
    {
        "name": "ask",
        "description": ("Answer a plain-language question about the codebase. "
                        "Facts (confidence 1.0) come with file:line evidence; "
                        "semantic hypotheses are listed separately with calibrated "
                        "confidence. Examples: 'who calls init_db', 'where is save', "
                        "'what does context do', 'what entry points exist'."),
        "inputSchema": {"type": "object",
                        "properties": {"question": {"type": "string"}},
                        "required": ["question"]},
    },
    {
        "name": "why",
        "description": "Show the evidence behind a node id (why it exists / its confidence).",
        "inputSchema": {"type": "object",
                        "properties": {"node": {"type": "string",
                                                "description": "e.g. func::db::save or a name like 'save'"}},
                        "required": ["node"]},
    },
    {
        "name": "narrative",
        "description": "Regenerate the living narrative (H3) of the repository.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "stats",
        "description": "Fact-model statistics (files, reparsed/from_cache, nodes, edges, imports, calls).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "audit",
        "description": "Confidence calibration table: every semantic hypothesis with its confidence and note.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "impact",
        "description": ("CI impact report: given changed file paths, what does this PR affect? — "
                        "affected modules, importers, callers that may break, entry points touched, "
                        "flows affected, reverse dependencies."),
        "inputSchema": {"type": "object",
                        "properties": {"changed_files": {"type": "array", "items": {"type": "string"}}},
                        "required": ["changed_files"]},
    },
]


def _cache_dir_for(repo):
    repo = os.path.abspath(repo)
    return DEFAULT_CACHE + "/" + (repo.replace(":", "").replace(os.sep, "_") or "repo")

def _loc(node):
    return node["evidence"][0]["source"] if node.get("evidence") else "-"


def _render_answer(ans):
    out = [ans["answer_text"]]
    if ans["facts"]:
        out.append("FACTS (confidence 1.0):")
        for f in ans["facts"]:
            out.append(f"  [{f['label']}]")
            for r in f["rows"]:
                out.append(f"    - {r['type']} `{r['name']}` ({r['loc']})")
    if ans["hypotheses"]:
        out.append("HYPOTHESES (calibrated):")
        for h in ans["hypotheses"]:
            out.append(f"  - {h['type']} `{h['name']}` conf={h['confidence']} ({h['note']}) id={h['id']}")
    return "\n".join(out)


class MCPServer:
    """JSON-RPC 2.0 MCP endpoint over stdio (newline-delimited JSON)."""

    def __init__(self, repo_root, enrich=False, cache_dir=None):
        self.root = os.path.abspath(repo_root)
        self.repo = os.path.basename(os.path.normpath(self.root))
        self.enrich = enrich
        self.cache_dir = cache_dir
        self.artifact = None
        self.index = None

    # ---- build -------------------------------------------------------------

    def _ensure_built(self):
        if self.index is None:
            art = extract.build(self.root, cache_dir=self.cache_dir, verbose=False)
            if self.enrich:
                art = semantics.enrich(art, verbose=False)
            self.artifact = art
            self.index = indexmod.Index(art)

    # ---- dispatch ----------------------------------------------------------

    def handle(self, msg):
        if not isinstance(msg, dict):
            return self._error(None, -32600, "invalid request")
        method = msg.get("method")
        rid = msg.get("id")
        if method == "initialize":
            return self._response(rid, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ssrl-mcp", "version": VERSION},
            })
        if method in ("notifications/initialized", "notifications/cancelled"):
            return None
        if method == "ping":
            return self._response(rid, {})
        if method == "tools/list":
            return self._response(rid, {"tools": TOOLS})
        if method == "tools/call":
            return self._tools_call(rid, msg.get("params") or {})
        if method == "resources/list":
            return self._response(rid, {"resources": []})
        if method == "resources/read":
            return self._error(rid, -32602, "no resources exposed")
        return self._error(rid, -32601, f"method not found: {method}")

    def _tools_call(self, rid, params):
        name = (params or {}).get("name")
        args = (params or {}).get("arguments") or {}
        if not any(t["name"] == name for t in TOOLS):
            return self._error(rid, -32602, f"unknown tool: {name}")
        try:
            self._ensure_built()
            text = self._run_tool(name, args)
        except Exception as ex:  # tool execution error -> isError result
            return self._response(rid, {"content": [{"type": "text", "text": f"error: {ex}"}],
                                        "isError": True})
        return self._response(rid, {"content": [{"type": "text", "text": text}]})

    # ---- tools -------------------------------------------------------------

    def _run_tool(self, name, args):
        if name == "ask":
            q = args.get("question")
            if not isinstance(q, str) or not q.strip():
                raise ValueError("'question' is required (non-empty string)")
            return _render_answer(qa.answer(self.index, q))
        if name == "why":
            key = args.get("node")
            if not isinstance(key, str) or not key.strip():
                raise ValueError("'node' is required")
            n = self.index.node(key) or next(iter(self.index.find(key) or []), None)
            if n is None:
                raise ValueError(f"not found: {key}")
            return confidence.why(n)
        if name == "narrative":
            return narr.narrative(self.index)
        if name == "stats":
            s = self.artifact["stats"]
            return ("files={files} reparsed={parsed} ok={parse_ok} errors={parse_errors} "
                    "from_cache={from_cache} elapsed_s={elapsed_s}\n"
                    "nodes={nodes} edges={edges} functions={functions} "
                    "imports={imports} calls={calls}").format(**s)
        if name == "audit":
            hyp = [n for n in self.artifact["nodes"]
                   if n["type"] in {"DomainConcept", "Flow", "Intent", "Service"}]
            rows = confidence.audit(hyp)
            return "\n".join(f"{r['id']:<70} {r['type']:<14} conf={r['confidence']:<6} {r['note']}"
                             for r in rows) or "(no hypotheses)"
        if name == "impact":
            files = args.get("changed_files")
            if not isinstance(files, list) or not all(isinstance(f, str) for f in files):
                raise ValueError("'changed_files' must be a non-empty list of file paths")
            report = impactmod.impact_changed(self.artifact, files, index=self.index)
            return impactmod.render_impact(report)
        raise ValueError(f"unhandled tool: {name}")

    # ---- protocol plumbing -------------------------------------------------

    @staticmethod
    def _response(rid, payload):
        return {"jsonrpc": "2.0", "id": rid, "result": payload}

    @staticmethod
    def _error(rid, code, message, data=None):
        err = {"code": code, "message": message}
        if data is not None:
            err["data"] = data
        return {"jsonrpc": "2.0", "id": rid, "error": err}

    def serve_stdio(self, stdin=None, stdout=None):
        stdin = stdin or sys.stdin
        stdout = stdout or sys.stdout
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                resp = self._error(None, -32700, "parse error")
            else:
                resp = self.handle(msg)
            if resp is not None:
                stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                stdout.flush()


def main(argv=None):
    p = argparse.ArgumentParser(prog="ssrl-mcp", description="SSRL MCP server (zero-dep, stdio).")
    p.add_argument("--repo", required=True, help="repository root (read-only)")
    p.add_argument("--enrich", action="store_true", help="enable semantic hypotheses")
    p.add_argument("--no-cache", action="store_true", help="disable the D-8 incremental cache")
    args = p.parse_args(argv)
    cache_dir = None if args.no_cache else _cache_dir_for(args.repo)
    server = MCPServer(args.repo, enrich=args.enrich, cache_dir=cache_dir)
    server.serve_stdio()


if __name__ == "__main__":
    main()