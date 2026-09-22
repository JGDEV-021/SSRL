import os
import sys
import unittest

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "pkgapp")
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC)

from ssrl import confidence, extract, index as indexmod, model, narrative as narr, qa, semantics


def build_artifact(enrich=False):
    art = extract.build(FIXTURES, cache_dir=None)
    if enrich:
        art = semantics.enrich(art)
    return art


class TestExtract(unittest.TestCase):
    def test_parse_ok(self):
        a = build_artifact()
        self.assertEqual(a["stats"]["parse_errors"], 0)
        self.assertEqual(a["stats"]["files"], 6)

    def test_node_types_present(self):
        a = build_artifact()
        types = {n["type"] for n in a["nodes"]}
        self.assertTrue({"Module", "Class", "Function", "Method", "Repository"} <= types)

    def test_class_and_method(self):
        a = build_artifact()
        by_id = {n["id"]: n for n in a["nodes"]}
        item = by_id.get("class::models::Item")
        self.assertIsNotNone(item)
        # method contained by class
        contains = [e for e in a["edges"] if e["relationship"] == "CONTAINS" and e["source"] == item["id"]]
        self.assertTrue(any(e["target"] == "func::models::validate" for e in contains))

    def test_imports_local_resolved(self):
        a = build_artifact()
        db = next(n for n in a["nodes"] if n["id"] == "module::db")
        imps = [e for e in a["edges"] if e["relationship"] == "IMPORTS" and e["source"] == db["id"]]
        self.assertTrue(any(e["target"] == "module::models" for e in imps))

    def test_calls_cross_module(self):
        a = build_artifact()
        edges = [e for e in a["edges"] if e["relationship"] == "CALLS"]
        self.assertTrue(any(e["metadata"].get("resolution") == "cross-module" for e in edges))
        self.assertTrue(any(e["source"] == "func::db::save"
                            and e["target"] == "func::models::validate" for e in edges))

    def test_facts_confidence_one(self):
        for kind in ("Module", "Class", "Function", "Method", "Repository"):
            a = build_artifact()
            for n in a["nodes"]:
                if n["type"] == kind:
                    self.assertEqual(n["confidence"], 1.0)

    def test_evidence_present(self):
        a = build_artifact()
        for n in a["nodes"]:
            if n["type"] in ("Module", "Class", "Function", "Method"):
                self.assertTrue(n.get("evidence"), f"{n['id']} has evidence")
                self.assertIn("parser", n["evidence"][0]["type"])

    def test_determinism(self):
        a1 = build_artifact()
        a2 = build_artifact()
        self.assertEqual(
            sorted((n["id"], n["type"]) for n in a1["nodes"]),
            sorted((n["id"], n["type"]) for n in a2["nodes"]))
        self.assertEqual(
            sorted((e["source"], e["target"], e["relationship"]) for e in a1["edges"]),
            sorted((e["source"], e["target"], e["relationship"]) for e in a2["edges"]))

    def test_repo_contains_each_module_once(self):
        a = build_artifact()
        repo = next(n["id"] for n in a["nodes"] if n["type"] == "Repository")
        per_module = [
            e for e in a["edges"]
            if e["relationship"] == "CONTAINS" and e["source"] == repo and e["target"].startswith("module::")]
        self.assertEqual(len(per_module), 6)


class TestIncrementalCache(unittest.TestCase):
    def test_cache_reused(self):
        import tempfile, shutil
        d = tempfile.mkdtemp()
        try:
            a1 = extract.build(FIXTURES, cache_dir=d)
            self.assertEqual(a1["stats"]["from_cache"], 0)
            self.assertEqual(a1["stats"]["parsed"], 6)
            a2 = extract.build(FIXTURES, cache_dir=d)
            self.assertEqual(a2["stats"]["from_cache"], 6)
            self.assertEqual(a2["stats"]["parsed"], 0)
            # identical content despite cache
            self.assertEqual(
                sorted((n["id"], n["type"]) for n in a1["nodes"]),
                sorted((n["id"], n["type"]) for n in a2["nodes"]))
        finally:
            shutil.rmtree(d)


class TestSemantics(unittest.TestCase):
    def test_intents_generated(self):
        a = build_artifact(enrich=True)
        intents = [n for n in a["nodes"] if n["type"] == "Intent"]
        names = {n["name"] for n in intents}
        self.assertTrue(names)  # non-empty; naming heuristics over fixture
        for n in intents:
            self.assertGreater(n["confidence"], 0)
            self.assertLess(n["confidence"], 1)

    def test_flows_generated(self):
        a = build_artifact(enrich=True)
        flows = [n for n in a["nodes"] if n["type"] == "Flow"]
        self.assertGreaterEqual(len(flows), 1)  # store validation flow
        by_id = {n["id"]: n for n in a["nodes"]}
        # flow for store() should include db.save -> models.validate
        model = None
        for f in flows:
            if f["metadata"].get("entry") == "func::services.store::store":
                model = f
        self.assertIsNotNone(model)
        steps = model["metadata"]["steps"]
        self.assertTrue(any("func::db::save" in s for s in steps))
        self.assertTrue(any("func::models::validate" in s for s in steps))

    def test_confidences_bounded(self):
        a = build_artifact(enrich=True)
        hyps = [n for n in a["nodes"] if n["type"] in ("Intent", "Flow", "Service")]
        for h in hyps:
            self.assertGreaterEqual(h["confidence"], 0.0)
            self.assertLess(h["confidence"], 1.0)

    def test_facts_untouched_by_enrich(self):
        def structural_ids(art):
            return sorted(n["id"] for n in art["nodes"] if n["type"] in model.STRUCTURAL_NODES)
        a = build_artifact(enrich=False)
        ae = build_artifact(enrich=True)
        self.assertEqual(structural_ids(a), structural_ids(ae))


class TestConfidence(unittest.TestCase):
    def test_fact_calibrates_to_1(self):
        n = {"id": "x", "type": "Function", "confidence": 1.0, "evidence": []}
        self.assertEqual(confidence.calibrate(n)[0], 1.0)

    def test_hypothesis_without_evidence_demoted(self):
        n = {"id": "h1", "type": "Intent", "confidence": 0.8, "evidence": []}
        self.assertEqual(confidence.calibrate(n)[0], 0.5)

    def test_hypothesis_capped_by_source(self):
        n = {"id": "h2", "type": "Intent", "confidence": 0.9,
             "evidence": [{"type": "NamingPattern", "weight": 0.7}]}
        c, _ = confidence.calibrate(n)
        self.assertLessEqual(c, 0.7)

    def test_aggregate_noisy_or(self):
        ev = [{"type": "NamingPattern", "weight": 0.6}, {"type": "CallGraph", "weight": 0.5}]
        c = confidence.aggregate(ev)
        self.assertEqual(c, 0.6)  # combined capped at strongest single source


class TestIndex(unittest.TestCase):
    def test_find_module(self):
        idx = indexmod.Index(build_artifact())
        hits = idx.find("db")
        self.assertTrue(any(n["id"] == "module::db" for n in hits))

    def test_callers(self):
        idx = indexmod.Index(build_artifact())
        val = idx.node("func::models::validate")
        callers = idx.callers_of(val["id"])
        self.assertTrue(any(n["name"] == "save" for n in callers))

    def test_entry_points(self):
        idx = indexmod.Index(build_artifact())
        eps = idx.entry_points()
        self.assertTrue(any(n["name"] == "main" for n in eps))


class TestQA(unittest.TestCase):
    def setUp(self):
        import json as _json
        globals()["json"] = _json
        self.idx = indexmod.Index(build_artifact(enrich=True))

    def test_where(self):
        a = qa.answer(self.idx, "where is save")
        self.assertEqual(a["intent"], "where")
        self.assertIn("db.py", json.dumps(a))
        self.assertTrue(all(f["label"] for f in a["facts"]))

    def test_callees(self):
        a = qa.answer(self.idx, "what does store call")
        self.assertEqual(a["intent"], "callees")
        self.assertTrue(a["facts"])

    def test_summary_module_docstring(self):
        a = qa.answer(self.idx, "what does db do")
        self.assertIn("persistence", a["answer_text"])

    def test_entry(self):
        a = qa.answer(self.idx, "entry points")
        self.assertEqual(a["intent"], "entry")
        self.assertIn("main", a["answer_text"])

    def test_flows_browse(self):
        a = qa.answer(self.idx, "flows")
        self.assertEqual(a["intent"], "flows")
        self.assertTrue(a["hypotheses"])

    def test_notfound(self):
        a = qa.answer(self.idx, "what does zzzzzz do")
        self.assertIn("couldn't find", a["answer_text"])


class TestNarrative(unittest.TestCase):
    def test_generates_sectioned(self):
        idx = indexmod.Index(build_artifact(enrich=True))
        text = narr.narrative(idx)
        for section in ("Living Narrative", "Overview", "Entry points", "Module map", "Key flows"):
            self.assertIn(section, text)

    def test_mentions_parse_health(self):
        idx = indexmod.Index(build_artifact(enrich=True))
        self.assertIn("Parse health", narr.narrative(idx))


class TestImportDesugar(unittest.TestCase):
    def test_relative_import_to_module_edge(self):
        a = build_artifact()
        db = next(n for n in a["nodes"] if n["id"] == "module::db")
        imps = [e["target"] for e in a["edges"] if e["relationship"] == "IMPORTS" and e["source"] == db["id"]]
        self.assertIn("module::models", imps)

    def test_from_dotdot_service(self):
        a = build_artifact()
        store = next(n for n in a["nodes"] if n["id"] == "module::services.store")
        imps = [e["target"] for e in a["edges"] if e["relationship"] == "IMPORTS" and e["source"] == store["id"]]
        self.assertIn("module::db", imps)


class TestWhyCli(unittest.TestCase):
    def test_why_accepts_node_id(self):
        import argparse, contextlib, io
        from ssrl import cli
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.cmd_why(argparse.Namespace(repo=FIXTURES, cache=False, node="func::db::save"))
        out = buf.getvalue()
        self.assertNotIn("not found", out)
        self.assertIn("func::db::save", out)

    def test_why_accepts_name_fallback(self):
        import argparse, contextlib, io
        from ssrl import cli
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            cli.cmd_why(argparse.Namespace(repo=FIXTURES, cache=False, node="save"))
        out = buf.getvalue()
        self.assertNotIn("not found", out)
        self.assertIn("func::db::save", out)


if __name__ == "__main__":
    unittest.main()