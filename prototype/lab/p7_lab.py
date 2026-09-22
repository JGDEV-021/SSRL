"""SSRL Phase 7 lab — freshness measurement on a real, evolving project.

Copies a real corpus (read-only by contract, NFR-5) into a temp working copy,
then drives the watcher (ssrl.watch) through a scripted evolution sequence and
records one regeneration event per change. Every regeneration is incremental
(only changed files re-parsed; the sha256 cache replays the rest).

Usage:
    python lab/p7_lab.py [corpus] [--noregen]

Events are written to a JSON-lines log and a measurements summary printed.
"""

import json
import os
import shutil
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ssrl import extract, model, semantics, watch as watchmod

DEFAULT_CORPUS = os.path.abspath(os.path.join(
    os.path.expanduser("~"), "Downloads", "JG-CODE", "doc_rag"))


def write_rel(root, rel, content):
    p = os.path.join(root, rel.replace("/", os.sep))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    corpus = argv[0] if argv else DEFAULT_CORPUS
    if not os.path.isdir(corpus):
        print(f"no such corpus: {corpus}", file=sys.stderr)
        return 1

    tmp = tempfile.mkdtemp(prefix="ssrl-p7-lab-")
    root = os.path.join(tmp, "work")
    shutil.copytree(corpus, root)
    cache_dir = os.path.join(tmp, "cache")
    events_path = os.path.join(tmp, "events.jsonl")

    retriever_rel = "retriever.py"
    retriever = open(os.path.join(root, retriever_rel), encoding="utf-8").read()

    w = watchmod.Watch(root, cache_dir=cache_dir, enrich_ok=True, interval=0.0, events=events_path)
    try:
        events = [w.initial_sync()]

        write_rel(root, retriever_rel, retriever + "\n\ndef ping():\n    return True\n")
        events.append(w.step())

        write_rel(root, "quality_extra.py",
                  '"""Extra quality probe added in the lab."""\n\ndef quick_probe():\n    return 1\n')
        events.append(w.step())

        os.remove(os.path.join(root, "quality_extra.py"))
        events.append(w.step())

        write_rel(root, retriever_rel, retriever + "\n\ndef ping():\n    return \"pong\"\n")
        events.append(w.step())

        write_rel(root, retriever_rel, retriever)
        events.append(w.step())

        w.step()  # static cycle after revert -> None
    finally:
        w.close()

    print(f"corpus copy  : {root}")
    print(f"events log   : {events_path}")
    print()
    hdr = ("# | event     | files | reparsed | from_cache | nodes | edges | "
           "d_nodes | d_edges | enrich(fl/i/s)  | elapsed_s")
    print(hdr)
    print("-" * len(hdr))
    for i, ev in enumerate(events, 1):
        d = ev.get("delta") or {}
        h = ev.get("hypotheses") or {}
        hs = (f"{h.get('flows', '-')}/{h.get('intents', '-')}/"
              f"{h.get('services_domain', '-')}" if h else "-")
        print(f"{i:<4} | {ev['type']:<9} | {ev['files']:<5} | {ev['reparsed']:<8} | "
              f"{ev['from_cache']:<10} | {ev['nodes']:<5} | {ev['edges']:<5} | "
              f"{d.get('nodes', '-'):<7} | {d.get('edges', '-'):<7} | "
              f"{hs:<15} | {ev['elapsed_s']}")

    reparsed = sum(ev["reparsed"] for ev in events)
    cached = sum(ev["from_cache"] for ev in events)
    files = events[0]["files"]
    cycl = len(events)
    print()
    print(f"summary: {cycl} regenerations over a {files}-file corpus; "
          f"total reparsed={reparsed} total from_cache={cached}")
    print(f"incremental ratio: {reparsed}/{files} expected per touched change, "
          f"cache covered {cached}/{files * cycl} module-cycles")
    print(f"final artifact: nodes={events[-1]['nodes']} edges={events[-1]['edges']} "
          f"(should equal initial {events[0]['nodes']}/{events[0]['edges']} after revert)")
    return 0


if __name__ == "__main__":
    sys.exit(main())