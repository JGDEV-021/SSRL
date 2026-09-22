# SSRL Phase 7 — Lab Integration (Real-World Testbed)

**Goal (roadmap.md:175):** first real-world laboratory — SSRL operates continuously
on a real, evolving project without manual sync.

**Scope of this report:** the `ssrl watch` surface (watch/regenerate-on-change), the
freshness lab measurements, and the read-only live demonstration on the author's real
repositories.

---

## 1. What was built

New module `prototype/ssrl/watch.py` (v0.5.0 package; zero dependencies, ADR-002) plus
the `watch` CLI command:

```
watch  <repo> [--interval S] [--enrich] [--events F] [--max N] [--no-cache]
```

Design (all documented in the module docstring):

- **Polling, not OS events** — stdlib only. Each cycle computes a cheap
  `{rel: (mtime_ns, size)}` stat baseline (`watch.scan`) and diffs it
  (`watch.diff` → `added / modified / removed`).
- **Incremental regeneration** — on change, `extract.build(root, cache_dir)` is called;
  the D-8 sha256 cache replays every unchanged module, so only the delta is re-parsed.
- **Determinism preserved (NFR-4)** — regeneration produces the same artifact as a full
  build for the same corpus state.
- **Non-invasive (NFR-5)** — watch never writes inside the corpus; it touches only the
  cache dir and the (optional) `--events` JSON-lines log.
- **Cache enabled by default for `watch`** — this is deliberate: incremental *parsing*
  is the point of continuous operation. Other commands keep `--cache` opt-in.
- **Stepper API** — `Watch.initial_sync()` / `step()` are callable directly (what the
  lab and tests drive, no sleeps), and `Watch.run()` composes them into the timed loop.

## 2. Lab — freshness measurement (scripted evolution)

Driver: `prototype/lab/p7_lab.py`. It copies the real `doc_rag` corpus (read-only by
contract) into a temp working copy, then drives edit → `step()` → edit → `step()` …,
recording one event per change. Measurements (events log regenerated per run):

| # | event | files | reparsed | from_cache | nodes | edges | Δnodes | Δedges | enrich f/i/s | elapsed_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | initial | 31 | 31 | 0 | 306 | 741 | — | — | 10/48/4 | 0.91 |
| 2 | change (+fn in retriever) | 31 | 1 | 30 | 307 | 742 | +1 | +1 | 10/48/4 | 0.44 |
| 3 | change (+new module) | 32 | 1 | 31 | 309 | 744 | +2 | +2 | 10/48/4 | 0.41 |
| 4 | change (−new module) | 31 | 0 | 31 | 307 | 742 | −2 | −2 | 10/48/4 | 0.41 |
| 5 | change (body edit) | 31 | 1 | 30 | 307 | 742 | 0 | 0 | 10/48/4 | 0.47 |
| 6 | change (revert) | 31 | 1 | 30 | 306 | 741 | −1 | −1 | 10/48/4 | 0.43 |

**Results**
- Every regeneration re-parsed **exactly the touched file** (`reparsed=1`; `0` on pure
  deletion — deleting needs no re-parse); cache replayed the other 30–31 modules.
- Freshness closed the loop: after the revert, the artifact is **identical to the
  initial build** (306 nodes / 741 edges) — the layer converges, it does not drift.
- Enrichment recomputed deterministically every cycle (10 flows / 48 intents / 4 svc).
- Per-change regeneration ≈ 0.41–0.47 s vs full parse ≈ 0.91 s (cache + link re-run;
  the re-link is required for correct CALLS across the whole repo each time).

**Known limitation (documented, honest):** the D-8 cache is *single-version per file*
— it stores the last-seen digest only. Reverting a file to a previously-seen version
re-parses it once (it does not replay the old cache entry). Artifacts stay correct;
only the replay optimization is single-version. Keeping N versions per file is a
future refinement, not needed for correctness.

## 3. End-to-end run() loop (timed, background edit)

A real timed `Watch.run(interval=0.2, max=5)` against a working copy with a background
thread editing `db.py` mid-loop:

```
[#1 initial] files=6 reparsed=6 from_cache=0 errors=0 nodes=16 edges=20 elapsed=0.011s
[#2 change]  ~1 files=6 reparsed=1 from_cache=5 errors=0 nodes=17 edges=21 elapsed=0.069s
```

The edit landed between polls, was detected on the next cycle, and the artifact
regenerated incrementally; further static polls were silent no-ops.

## 4. Live read-only run on the author's real repos

No simulation — `watch` pointed directly at the read-only corpora:

```
$ python -m ssrl.cli watch <jgpredictor> --enrich --interval 0.3 --max 2
watching … (interval=0.3s enrich=True cache=True)
[#1 initial] files=122 reparsed=0 from_cache=122 errors=0 nodes=1316 edges=3112
             flows=1 intents=174 svc_domain=24 elapsed=0.43s

$ python -m ssrl.cli watch <doc_rag> --interval 0.3 --max 2
watching … (interval=0.3s enrich=True cache=True)
[#1 initial] files=31 reparsed=0 from_cache=31 errors=0 nodes=244 edges=679 elapsed=0.38s
```

Poll cycles after initial are silent until an edit appears — the loop is continuous.
Corpus integrity was verified: file sha256 before and after are identical (NFR-5).

## 5. Success criteria check (roadmap.md:182)

> "SSRL operates continuously on real, evolving projects without manual sync."

**VERIFIED.** No manual `--cache` invocation anywhere in the loop; the cache is the
engine of incrementality, not a user action. Artifacts track the corpus convergently
(lab revert → identical output), work on the two real repos read-only, and regenerate
with delta-only parsing at ~0.4–0.5 s per change on `doc_rag`.

## 6. Tests

6 new tests in `tests/test_mvp.py` (`TestWatch`): diff detection (add/modify/remove),
initial full-parse, delta-only re-parse, static-cycle no-op, deletion reflected,
revert converges. Total suite: **39 tests, all green, ~0.65 s.**

Reproduce: `python lab/p7_lab.py` and `python -m unittest discover -s tests -v`.