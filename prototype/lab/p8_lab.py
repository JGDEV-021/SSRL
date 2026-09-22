"""Phase 8 lab — end-to-end agent surface demo (MCP over stdio).

Drives a real `ssrl.mcp` server lifecycle over a subprocess pipe:
  initialize -> notifications/initialized -> tools/list -> tools/call
for ask / why / stats / audit / impact / narrative, then closes cleanly.

Also does a coherence check: the same question answered via the CLI and via
the MCP tool must agree (humans and agents consume the same layer — Phase 8
success criterion).

Usage:
    python lab/p8_lab.py [corpus-root]   (default: doc_rag)
"""

import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(ROOT)
sys.path.insert(0, SRC)
if os.name == "nt":
    os.environ.setdefault("PYTHONUTF8", "1")

DEFAULT_CORPUS = r"C:\Users\joaog\Downloads\JG-CODE\doc_rag"


def main():
    corpus = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CORPUS
    print(f"=== SSRL Phase 8 lab: MCP agent surface over `{corpus}` ===")
    print(f"server: python -m ssrl.mcp --repo {corpus} --enrich (zero-dep, stdlib)\n")

    proc = subprocess.Popen(
        [sys.executable, "-m", "ssrl.mcp", "--repo", corpus, "--enrich"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="replace", bufsize=1,
    )

    def rpc(req, expect=True):
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()
        if not expect:
            return None
        line = proc.stdout.readline()
        return json.loads(line) if line.strip() else None

    req = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    print("[handshake] initialize ->", f"protocolVersion={req['result']['protocolVersion']}",
          f"server={req['result']['serverInfo']['name']}")
    rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}, expect=False)

    listing = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = [t["name"] for t in listing["result"]["tools"]]
    print("[tools/list]", ",".join(tools), "\n")

    def tool(name, args):
        r = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                 "params": {"name": name, "arguments": args}})
        return r["result"]["content"][0]["text"]

    print("> tools/call ask {question: 'who calls init_db'}")
    print(tool("ask", {"question": "who calls init_db"}))
    print()
    print("> tools/call stats")
    print(tool("stats", {}))
    print()
    print("> tools/call impact {changed_files: ['context.py', 'db.py']}  (PR report)")
    print(tool("impact", {"changed_files": ["context.py", "db.py"]}))
    print()
    print("> tools/call why {node: 'init_db'}  (first 8 lines)")
    why = tool("why", {"node": "init_db"})
    print("\n".join(why.splitlines()[:8]))
    print()
    print("> tools/call audit (count of hypothesis rows)")
    audit = tool("audit", {})
    print(f"  {len(audit.splitlines())} calibration rows")
    print()
    print("> tools/call narrative (length)")
    narr = tool("narrative", {})
    print(f"  {len(narr.splitlines())} lines")
    print()

    # ---- coherence: CLI vs MCP, same layer --------------------------------
    from ssrl import cli
    from ssrl import extract, index as indexmod, qa, semantics
    art = extract.build(corpus, cache_dir=cli._cache_dir_for(corpus))
    art = semantics.enrich(art, verbose=False)
    ans_cli = qa.answer(indexmod.Index(art), "who calls init_db")
    ans_mcp = tool("ask", {"question": "who calls init_db"})
    coherent = ans_cli["answer_text"].split(".")[0] in ans_mcp
    print(f"[coherence] CLI head '{ans_cli['answer_text'].split('.')[0]}' "
          f"{'<-' if coherent else '!= not'} in MCP answer -> {coherent}")

    rpc({"jsonrpc": "2.0", "id": 4, "method": "ping"})
    proc.stdin.close()
    proc.wait(timeout=30)
    print("\n[session] ping ok, stdin closed, server exited cleanly:", proc.returncode == 0)
    if proc.returncode != 0:
        print(proc.stderr.read())
    return 0


if __name__ == "__main__":
    sys.exit(main())