"""SSRL CLI (ADR-006) — the v1 integration surface.

Commands:
  build  <repo> [--cache DIR]           extract facts (D-8 cache optional)
  enrich <repo> [--cache DIR]           build + semantic hypotheses
  ask    <repo> "question" [--cache DIR]  grounded Q&A (H1)
  narrative <repo> [--cache DIR]        living narrative (H3)
  audit  <repo> [--cache DIR]           confidence calibration table
  stats  <repo> [--cache DIR]           fact-model statistics
  json   <repo> [--cache DIR] [--out F] export full artifact (NFR-7)
  watch  <repo> [--interval S] [--enrich] [--events F] [--max N]
                                        continuous no-manual-sync regeneration
                                        (Phase 7); cache enabled by default
  impact <repo> FILES... [--git BASE]   "what does this PR affect?" — modules,
       [--json] [--no-enrich]           importers, callers, entry points, flows
                                        (Phase 8, ADR-006 supporting surface)
  explain <repo> --node ID | FILES...   grounded WHAT/WHY/HOW (ADR-009):
       [--git BASE] [--json]            the coding AI explains itself against the
       [--no-enrich]                    layer — node mode or change mode
verify <repo> FILES... [--git BASE]   explanation auditor (ADR-009): cross-check
       --explanation TEXT @|--file      a free-text self-explanation against the
        [--json] [--no-enrich]           artifact -> groundedness + PASS/REVIEW
   deleted <repo> [--json] [--cache]    deleted-symbols view (Phase 10): modules,
                                        symbols and relations removed since the
                                        previous D-8 cached build — keeps
                                        narrations about removals audit-able
  mcp    <repo> [--enrich]              MCP server over stdio for AI agents
                                        (Phase 8, ADR-006 v1.5)
  propose <repo> [--model qwen3:0.6b]   micro-LLM hypothesis proposer (Phase 9,
       [--provider ollama|openai|mock]  ADR-008): names flows + labels unit roles;
       [--scope flows|units|all]        output is LLMProposal hypotheses (cap 0.5),
                                        never facts

Zero dependencies. Deterministic. Every claim carries evidence.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ssrl import confidence, extract, explain as ex, history, impact as impactmod, index as indexmod, narrative as narr, qa, semantics, watch as watchmod


DEFAULT_CACHE = os.path.join(os.path.expanduser("~"), ".ssrl", "cache")


def _cache_dir_for(repo):
    repo = os.path.abspath(repo)
    return DEFAULT_CACHE + "/" + (repo.replace(":", "").replace(os.sep, "_") or "repo")


def load_artifact(repo, use_cache, enrich_ok=False):
    repo = os.path.abspath(repo)
    cdir = _cache_dir_for(repo) if use_cache else None
    if enrich_ok:
        art = extract.build(repo, cache_dir=cdir, verbose=False)
        art = semantics.enrich(art, verbose=False)
        return art, indexmod.Index(art)
    art = extract.build(repo, cache_dir=cdir, verbose=False)
    return art, indexmod.Index(art)


def _print_answer(ans):
    print(ans["answer_text"])
    if ans["facts"]:
        print()
        print("FACTS (confidence 1.0):")
        for f in ans["facts"]:
            print(f"  [{f['label']}]")
            for r in f["rows"]:
                print(f"    - {r['type']} `{r['name']}` ({r['loc']})")
    if ans["hypotheses"]:
        print()
        print("HYPOTHESES (calibrated):")
        for h in ans["hypotheses"]:
            print(f"  - {h['type']} `{h['name']}` conf={h['confidence']} ({h['note']}) id={h['id']}")


def cmd_build(args):
    art, _ = load_artifact(args.repo, args.cache)
    print(json.dumps(art["stats"], indent=2))


def cmd_enrich(args):
    art, _ = load_artifact(args.repo, args.cache, enrich_ok=True)
    print(json.dumps({**art["stats"], "hypotheses": art["stats"].get("hypotheses")}, indent=2))


def cmd_ask(args):
    _, idx = load_artifact(args.repo, args.cache, enrich_ok=True)
    ans = qa.answer(idx, args.question)
    _print_answer(ans)


def cmd_why(args):
    _, idx = load_artifact(args.repo, args.cache)
    n = idx.node(args.node) or next(iter(idx.find(args.node) or []), None)
    if n is None:
        print(f"not found: {args.node}")
        return
    print(confidence.why(n))


def cmd_narrative(args):
    art, idx = load_artifact(args.repo, args.cache, enrich_ok=True)
    print(narr.narrative(idx))


def cmd_audit(args):
    art, _ = load_artifact(args.repo, args.cache, enrich_ok=True)
    hyp = [n for n in art["nodes"] if n["type"] in {"DomainConcept", "Flow", "Intent", "Service"}]
    for row in confidence.audit(hyp):
        print(f"{row['id']:<70} {row['type']:<14} conf={row['confidence']:<6} {row['note']}")


def cmd_stats(args):
    art, _ = load_artifact(args.repo, args.cache)
    s = art["stats"]
    print(f"files={s['files']} reparsed={s['parsed']} ok={s['parse_ok']} errors={s['parse_errors']} "
          f"from_cache={s['from_cache']} elapsed_s={s['elapsed_s']}")
    print(f"nodes={s['nodes']} edges={s['edges']} functions={s['functions']} "
          f"imports={s['imports']} calls={s['calls']}")


def cmd_json(args):
    art, _ = load_artifact(args.repo, args.cache, enrich_ok=args.enrich)
    payload = json.dumps(art, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"wrote {args.out}")
    else:
        print(payload)


def cmd_impact(args):
    art, idx = load_artifact(args.repo, args.cache, enrich_ok=not args.no_enrich)
    files = list(args.files or [])
    if args.git:
        git_files = _git_changed(args.repo, args.git)
        if git_files is None:
            return 1
        files += git_files
    report = impactmod.impact_changed(art, files, index=idx)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(impactmod.render_impact(report))
    return 0


def cmd_mcp(args):
    from ssrl import mcp
    cache_dir = None if args.no_cache else _cache_dir_for(args.repo)
    server = mcp.MCPServer(args.repo, enrich=args.enrich, cache_dir=cache_dir)
    server.serve_stdio()
    return 0


def _git_changed(repo, base):
    try:
        out = __import__("subprocess").check_output(
            ["git", "diff", "--name-only", base],
            cwd=os.path.abspath(repo), stderr=__import__("subprocess").DEVNULL,
            text=True, encoding="utf-8", errors="replace")
        return [f for f in out.splitlines() if f.strip()]
    except __import__("subprocess").CalledProcessError as ex:
        print(f"error: git diff failed ({ex})", file=sys.stderr)
        return None


def cmd_explain(args):
    art, idx = load_artifact(args.repo, args.cache, enrich_ok=not args.no_enrich)
    if args.node:
        n = idx.node(args.node) or next(iter(idx.find(args.node) or []), None)
        if n is None:
            print(f"not found: {args.node}")
            return 2
        d = ex.explain_node(idx, n)
        if args.json:
            print(json.dumps(d, ensure_ascii=False, indent=2))
        else:
            print(ex.render_explain_node(d))
        return 0
    files = list(args.files or [])
    if args.git:
        git_files = _git_changed(args.repo, args.git)
        if git_files is None:
            return 1
        files += git_files
    if not files:
        print("error: provide --node ID or a list of changed FILES (or --git BASE)",
              file=sys.stderr)
        return 2
    d = ex.explain_changed(art, files, index=idx)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(ex.render_explain_changed(d))
    return 0


def cmd_verify(args):
    narration = args.explanation or ""
    if args.explanation_file:
        try:
            with open(args.explanation_file, encoding="utf-8") as f:
                narration = f.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    if not narration.strip():
        narration = sys.stdin.read()
    files = list(args.files or [])
    if args.git:
        git_files = _git_changed(args.repo, args.git)
        if git_files is None:
            return 1
        files += git_files
    if not files:
        print("error: provide changed FILES (or --git BASE)", file=sys.stderr)
        return 2
    if not narration.strip():
        print("error: provide --explanation TEXT, --explanation-file PATH, or narrate on stdin",
              file=sys.stderr)
        return 2
    art, idx = load_artifact(args.repo, args.cache, enrich_ok=not args.no_enrich)
    d = ex.verify_explanation(art, files, narration, index=idx)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(ex.render_verify(d))
    return 0


def cmd_deleted(args):
    art, _ = load_artifact(args.repo, args.cache)
    if args.json:
        print(json.dumps(art["deleted"], ensure_ascii=False, indent=2))
    else:
        print(history.render_deleted(art["deleted"]))
    return 0


def cmd_propose(args):
    from ssrl import llm
    art, idx = load_artifact(args.repo, args.cache, enrich_ok=True)
    provider = llm.make_provider("mock" if args.mock else args.provider,
                                 endpoint=args.endpoint, model=args.model,
                                 api_key=args.api_key, timeout=args.timeout)
    if not provider.probe():
        ep = getattr(provider, "endpoint", "-")
        print(f"error: provider '{args.provider}' unreachable at {ep} "
              f"(model '{args.model}'); start the server or pass --mock",
              file=sys.stderr)
        return 3
    art, stats = llm.run(idx, art, provider, scope=args.scope)
    print(json.dumps({k: stats[k] for k in sorted(stats)}, indent=2))
    proposed = sorted((n for n in art["nodes"]
                       if (n.get("metadata") or {}).get("origin") == "llm"),
                      key=lambda n: n["id"])
    if proposed:
        print()
        print("LLM-PROPOSED INTENTS (hypotheses, never facts):")
        for n in proposed:
            print(f"  {n['id']}: '{n['name']}' conf={n['confidence']} "
                  f"rationale={n['metadata'].get('rationale', '')}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(json.dumps(art, ensure_ascii=False, indent=1))
        print(f"wrote {args.out}")
    return 0


def cmd_watch(args):
    cache_dir = None if args.no_cache else _cache_dir_for(args.repo)
    w = watchmod.Watch(args.repo, cache_dir=cache_dir, enrich_ok=args.enrich,
                       interval=args.interval, events=args.events)
    print(f"watching {os.path.abspath(args.repo)} "
          f"(interval={args.interval}s enrich={args.enrich} cache={not args.no_cache})")
    try:
        w.run(max_iterations=args.max, on_event=lambda ev: print(watchmod.render(ev)))
    except KeyboardInterrupt:
        print("\nwatch stopped")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="ssrl", description="SSRL — semantic software representation layer (MVP)")
    sub = p.add_subparsers(dest="cmd")

    b = sub.add_parser("build"); b.add_argument("repo"); b.add_argument("--cache", action="store_true"); b.set_defaults(fn=cmd_build)
    e = sub.add_parser("enrich"); e.add_argument("repo"); e.add_argument("--cache", action="store_true"); e.set_defaults(fn=cmd_enrich)
    a = sub.add_parser("ask"); a.add_argument("repo"); a.add_argument("question"); a.add_argument("--cache", action="store_true"); a.set_defaults(fn=cmd_ask)
    w = sub.add_parser("why"); w.add_argument("repo"); w.add_argument("node"); w.add_argument("--cache", action="store_true"); w.set_defaults(fn=cmd_why)
    n = sub.add_parser("narrative"); n.add_argument("repo"); n.add_argument("--cache", action="store_true"); n.set_defaults(fn=cmd_narrative)
    au = sub.add_parser("audit"); au.add_argument("repo"); au.add_argument("--cache", action="store_true"); au.set_defaults(fn=cmd_audit)
    st = sub.add_parser("stats"); st.add_argument("repo"); st.add_argument("--cache", action="store_true"); st.set_defaults(fn=cmd_stats)
    j = sub.add_parser("json"); j.add_argument("repo"); j.add_argument("--out"); j.add_argument("--cache", action="store_true"); j.add_argument("--enrich", action="store_true"); j.set_defaults(fn=cmd_json)
    wt = sub.add_parser("watch"); wt.add_argument("repo"); wt.add_argument("--interval", type=float, default=2.0); wt.add_argument("--enrich", action="store_true"); wt.add_argument("--events"); wt.add_argument("--max", type=int); wt.add_argument("--no-cache", action="store_true"); wt.set_defaults(fn=cmd_watch)
    imp = sub.add_parser("impact"); imp.add_argument("repo"); imp.add_argument("files", nargs="*"); imp.add_argument("--git"); imp.add_argument("--json", action="store_true"); imp.add_argument("--no-enrich", action="store_true"); imp.add_argument("--cache", action="store_true"); imp.set_defaults(fn=cmd_impact)
    exx = sub.add_parser("explain"); exx.add_argument("repo"); exx.add_argument("--node"); exx.add_argument("files", nargs="*"); exx.add_argument("--git"); exx.add_argument("--json", action="store_true"); exx.add_argument("--no-enrich", action="store_true"); exx.add_argument("--cache", action="store_true"); exx.set_defaults(fn=cmd_explain)
    vf = sub.add_parser("verify"); vf.add_argument("repo"); vf.add_argument("files", nargs="*"); vf.add_argument("--explanation"); vf.add_argument("--explanation-file"); vf.add_argument("--git"); vf.add_argument("--json", action="store_true"); vf.add_argument("--no-enrich", action="store_true"); vf.add_argument("--cache", action="store_true"); vf.set_defaults(fn=cmd_verify)
    mc = sub.add_parser("mcp"); mc.add_argument("repo"); mc.add_argument("--enrich", action="store_true"); mc.add_argument("--no-cache", action="store_true"); mc.set_defaults(fn=cmd_mcp)
    de = sub.add_parser("deleted"); de.add_argument("repo"); de.add_argument("--json", action="store_true"); de.add_argument("--cache", action="store_true"); de.set_defaults(fn=cmd_deleted)
    pp = sub.add_parser("propose"); pp.add_argument("repo"); pp.add_argument("--provider", default="ollama", choices=["ollama", "openai", "mock"]); pp.add_argument("--endpoint"); pp.add_argument("--model", default="qwen3:0.6b"); pp.add_argument("--api-key"); pp.add_argument("--timeout", type=float, default=30.0); pp.add_argument("--scope", default="flows", choices=["flows", "units", "all"]); pp.add_argument("--mock", action="store_true", help="force deterministic mock provider"); pp.add_argument("--out"); pp.add_argument("--cache", action="store_true"); pp.set_defaults(fn=cmd_propose)

    args = p.parse_args(argv)
    if not getattr(args, "fn", None):
        p.print_help()
        return 2
    try:
        return args.fn(args) or 0
    except FileNotFoundError as ex:
        print(f"error: {ex}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())