"""Phase 10 lab — Explainable AI battery (ADR-009).

Validates the explanation auditor (`ssrl/explain.py`) with narrations drafted by
an opencode subagent (model opencode/big-pickle) acting as a *synthetic external
coding AI* — standing in for Claude/Codex self-explaining a real change set.

Runs the deterministic auditor over the seed (lab/p10_eai_seed.json) and writes
aggregate results to lab/p10_eai_results.{json,md}. Same discipline as the
p9_probe/p9_study harness: stdlib only, deterministic for a given seed.

Ceiling check (Phase 9 technique): the "faithful" narrations are the ground truth
written by the AI author with only real symbols and real relations — they MUST
reach groundedness 1.0 and zero invented citations. The "adversarial" narration
introduces one fabricated reference — the auditor MUST flag it (REVIEW).
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ssrl import explain, extract, index as indexmod, semantics

LAB_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(LAB_DIR)
SEED_PATH = os.path.join(LAB_DIR, "p10_eai_seed.json")
OUT_JSON = os.path.join(LAB_DIR, "p10_eai_results.json")
OUT_MD = os.path.join(LAB_DIR, "p10_eai_results.md")


def main():
    with open(SEED_PATH, encoding="utf-8") as f:
        seed = json.load(f)
    art = semantics.enrich(extract.build(REPO_ROOT, cache_dir=None))
    idx = indexmod.Index(art)

    rows = []
    for sc in seed["scenarios"]:
        files = sc["files"]
        narration = sc["narration"]
        d = explain.verify_explanation(art, files, narration, index=idx)
        s = seed["scenarios"].index(sc)
        rows.append({
            "scenario": sc["name"],
            "kind": sc["kind"],
            "files": files,
            "verdict": d["verdict"],
            "groundedness": d["groundedness"],
            "citations": d["citations"],
            "claims": d["claims"],
            "change_scope": d["change_scope"],
            "narration": narration,
        })
        status = "ok" if ((sc["kind"] == "faithful" and d["verdict"] == "PASS")
                          or (sc["kind"] == "adversarial" and d["verdict"] == "REVIEW"
                              and d["citations"]["invented"] > 0)) else "MISMATCH"
        print(f"[{status}] {sc['name']:<26} kind={sc['kind']:<10} "
              f"verdict={d['verdict']:<6} groundedness={d['groundedness']} "
              f"invented={d['citations']['invented']}")

    faithful = [r for r in rows if r["kind"] == "faithful"]
    adversarial = [r for r in rows if r["kind"] == "adversarial"]
    agg = {
        "total": len(rows),
        "faithful_pass": sum(1 for r in faithful if r["verdict"] == "PASS"),
        "faithful_total": len(faithful),
        "adversarial_review": sum(1 for r in adversarial if r["verdict"] == "REVIEW"),
        "adversarial_total": len(adversarial),
        "mean_groundedness_faithful": round(sum(r["groundedness"] for r in faithful)
                                            / len(faithful), 3) if faithful else None,
        "ceiling_ok": all(r["citations"]["invented"] == 0 and r["groundedness"] == 1.0
                          for r in faithful),
    }
    agg["threshold"] = _threshold_analysis(rows)

    out = {"author": seed["author"], "aggregate": agg, "scenarios": rows}
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    L = [f"# P10 — Explainable AI battery (ADR-009)",
         "",
         f"Narrations drafted by: **{seed['author']}** acting as a synthetic",
         "external coding AI. Auditor: `ssrl/explain.py` (deterministic).",
         "",
         "## Aggregate",
         f"- faithful ground-truth ceiling: **{agg['ceiling_ok']}** "
         f"({agg['faithful_pass']}/{agg['faithful_total']} PASS, "
         f"mean groundedness {agg['mean_groundedness_faithful']})",
         f"- adversarial REFERENCE caught: **{agg['adversarial_review']}/{agg['adversarial_total']}** "
         "REVIEW with invented > 0",
         "",
         "## Threshold sensitivity",
         f"- rule: **{agg['threshold']['rule']}**",
         f"- observed separation: faithful groundedness "
         f"min={agg['threshold']['observations']['min_groundedness_faithful']}; "
         f"adversarial groundedness "
         f"max={agg['threshold']['observations']['max_groundedness_adversarial']}",
         f"- safe band (zero-misclassification thresholds): "
         f"({agg['threshold']['safe_band']['lo']}, {agg['threshold']['safe_band']['hi']}]",
         f"- default `pass_groundedness={agg['threshold']['default']}` inside the "
         f"band: **{agg['threshold']['current_in_band']}**",
         f"- fully-accurate thresholds: "
         f"{', '.join(str(t) for t in agg['threshold']['fully_accurate_thresholds'])}",
         "",
         "| threshold | accuracy (all N scenarios) |",
         "|-----------|----------------------------|"]
    for s in agg["threshold"]["sweep"]:
        L.append(f"| {s['threshold']:<9} | {s['accuracy']} "
                 f"({s['correct']}/{s['total']}) |")
    L += ["", "## Per scenario", ""]
    for r in rows:
        L.append(f"### {r['scenario']} ({r['kind']}) — {r['verdict']}")
        L.append(f"- files: {', '.join(r['files'])}")
        L.append(f"- groundedness = {r['groundedness']}; "
                 f"present={r['citations']['present']} invented={r['citations']['invented']} "
                 f"external={r['citations']['external']} in_scope={r['citations']['in_scope']} "
                 f"unquoted_hits={r['citations']['unquoted_hits']} "
                 f"unresolved={r['citations']['unresolved_tokens']}")
        if r["citations"]["invented_details"]:
            L.append(f"- invented details: {', '.join(r['citations']['invented_details'])}")
        if r["claims"]["unsupported"]:
            L.append(f"- unsupported claims ({len(r['claims']['unsupported'])}): "
                     + " | ".join(r["claims"]["unsupported"]))
        if r["claims"]["consistency_failures"]:
            for cf in r["claims"]["consistency_failures"]:
                L.append(f"- consistency failure: {cf['claim']} ({cf['reason']})")
        L.append(f"- narration: {r['narration']}")
        L.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    ok = agg["ceiling_ok"] and agg["adversarial_review"] == agg["adversarial_total"]
    print(f"\naggregate: ceiling_ok={agg['ceiling_ok']} "
          f"adversarial_caught={agg['adversarial_review']}/{agg['adversarial_total']}")
    t = agg["threshold"]
    print(f"threshold: default={t['default']} safe_band=({t['safe_band']['lo']}, "
          f"{t['safe_band']['hi']}] current_in_band={t['current_in_band']}")
    print(f"wrote {OUT_JSON}")
    return 0 if ok else 2


def _expected(verdict, kind):
    return "PASS" if kind == "faithful" else "REVIEW"


def _classify(groundedness, invented, t):
    return "PASS" if groundedness >= t and invented == 0 else "REVIEW"


def _threshold_analysis(rows):
    """Data-driven check of the verdict threshold (ADR-009 §5).

    Sweeps pass_groundedness over [0.0, 1.0] and reports which thresholds keep
    the battery perfectly separated (faithful -> PASS, adversarial -> REVIEW).
    The resulting safe band (max adversarial groundedness, min faithful
    groundedness] brackets every threshold with zero misclassification; the
    default 0.8 is confirmed to sit inside it for the current seed. Honest
    limits: one battery is too small to *move* the default — tuning needs the
    larger Phase 9/10 data set.
    """
    truths = [("PASS" if r["kind"] == "faithful" else "REVIEW", r) for r in rows]
    sweep = []
    for i in range(21):
        t = round(i * 0.05, 2)
        correct = sum(1 for want, r in truths
                      if _classify(r["groundedness"], r["citations"]["invented"], t) == want)
        sweep.append({"threshold": t, "correct": correct, "total": len(truths),
                      "accuracy": round(correct / len(truths), 3)})
    faithful_g = [r["groundedness"] for r in rows if r["kind"] == "faithful"]
    advers_g = [r["groundedness"] for r in rows if r["kind"] == "adversarial"]
    lo = max(advers_g) if advers_g else 1.0
    hi = min(faithful_g) if faithful_g else 1.0
    accurate = [s["threshold"] for s in sweep if s["accuracy"] == 1.0]
    return {
        "default": 0.8,
        "rule": "PASS iff groundedness >= t AND invented == 0",
        "observations": {
            "min_groundedness_faithful": hi,
            "max_groundedness_adversarial": lo,
        },
        "safe_band": {"lo": lo, "hi": hi,
                      "lower_open": True, "upper_closed": True},
        "current_in_band": lo < 0.8 <= hi,
        "fully_accurate_thresholds": accurate,
        "sweep": sweep,
    }


if __name__ == "__main__":
    sys.exit(main())