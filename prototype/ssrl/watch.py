"""SSRL watch (Phase 7) - continuous regeneration, zero manual sync (NFR-3).

A dependency-free (ADR-002) polling watcher: a cheap stat baseline (mtime_ns +
size) detects corpus change; `extract.build`'s sha256 cache (D-8) then replays
unchanged modules, so every regeneration parses only the delta while the
artifact stays deterministic (NFR-4).

Watch never writes to the corpus. It touches only the caller-provided cache dir
and (optionally) the JSON-lines events log.
"""

import json
import os
import time

from . import extract, semantics

__all__ = ["scan", "diff", "Watch", "render"]


def scan(root):
    """Indexed .py files -> {repo-relative path: (mtime_ns, size)}."""
    sig = {}
    for p in extract.index_corpus(root):
        rel = os.path.relpath(p, root).replace("\\", "/")
        st = os.stat(p)
        sig[rel] = (st.st_mtime_ns, st.st_size)
    return sig


def diff(baseline, current):
    """(added, modified, removed) relative paths between two stat snapshots."""
    added, modified = [], []
    for rel, sig in current.items():
        if rel not in baseline:
            added.append(rel)
        elif sig != baseline[rel]:
            modified.append(rel)
    removed = [rel for rel in baseline if rel not in current]
    return sorted(added), sorted(modified), sorted(removed)


class Watch:
    def __init__(self, root, cache_dir=None, enrich_ok=False, interval=2.0, events=None):
        self.root = os.path.abspath(root)
        self.cache_dir = cache_dir
        self.enrich_ok = enrich_ok
        self.interval = interval
        self._log_fh = None
        if events:
            path = os.path.abspath(events)
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            self._log_fh = open(path, "a", encoding="utf-8")
        self._baseline = None
        self._last_stats = None
        self._seq = 0

    def close(self):
        if self._log_fh:
            self._log_fh.close()
            self._log_fh = None

    def _emit(self, event):
        if self._log_fh:
            self._log_fh.write(json.dumps(event, ensure_ascii=False) + "\n")
            self._log_fh.flush()

    def _regen(self, kind, added, modified, removed):
        started = time.time()
        self._seq += 1
        art = extract.build(self.root, cache_dir=self.cache_dir)
        hypotheses = None
        if self.enrich_ok:
            art = semantics.enrich(art)
            hypotheses = art["stats"].get("hypotheses")
        s = art["stats"]
        delta = None
        if self._last_stats is not None:
            delta = {
                "files": s["files"] - self._last_stats["files"],
                "nodes": s["nodes"] - self._last_stats["nodes"],
                "edges": s["edges"] - self._last_stats["edges"],
            }
        event = {
            "ts": round(time.time(), 3),
            "seq": self._seq,
            "type": kind,
            "added": added,
            "modified": modified,
            "removed": removed,
            "files": s["files"],
            "reparsed": s["parsed"],
            "from_cache": s["from_cache"],
            "errors": s["parse_errors"],
            "nodes": s["nodes"],
            "edges": s["edges"],
            "elapsed_s": round(time.time() - started, 4),
        }
        if hypotheses:
            event["hypotheses"] = hypotheses
        if delta:
            event["delta"] = delta
        self._emit(event)
        self._last_stats = s
        return event

    def initial_sync(self):
        self._baseline = scan(self.root)
        return self._regen("initial", [], [], [])

    def step(self):
        """One poll cycle. Returns a regeneration event, or None if static."""
        current = scan(self.root)
        added, modified, removed = diff(self._baseline, current)
        self._baseline = current
        if not (added or modified or removed):
            return None
        return self._regen("change", added, modified, removed)

    def run(self, max_iterations=None, on_event=None):
        """Initial sync, then poll forever (or max_iterations cycles)."""
        try:
            first = self.initial_sync()
            if on_event:
                on_event(first)
            i = 0
            while max_iterations is None or i < max_iterations:
                time.sleep(self.interval)
                i += 1
                ev = self.step()
                if ev is not None and on_event:
                    on_event(ev)
            return i
        finally:
            self.close()


def render(event):
    """One-line human-readable summary of a regeneration event."""
    kind = event["type"]
    changes = ""
    if kind == "change":
        parts = []
        if event.get("added"):
            parts.append(f"+{len(event['added'])}")
        if event.get("modified"):
            parts.append(f"~{len(event['modified'])}")
        if event.get("removed"):
            parts.append(f"-{len(event['removed'])}")
        changes = " ".join(parts) + " "
    hyp = event.get("hypotheses")
    enrich_s = ""
    if hyp:
        enrich_s = (f" flows={hyp['flows']} intents={hyp['intents']} "
                    f"svc_domain={hyp['services_domain']}")
    return (
        f"[#{event['seq']} {kind}] {changes}files={event['files']} "
        f"reparsed={event['reparsed']} from_cache={event['from_cache']} "
        f"errors={event['errors']} nodes={event['nodes']} edges={event['edges']}"
        f"{enrich_s} elapsed={event['elapsed_s']}s")