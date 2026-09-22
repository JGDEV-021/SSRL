import os
import sys
import unittest

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "pkgapp")
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC)

from ssrl import explain, extract, index as indexmod, semantics


def build_artifact(enrich=True):
    art = extract.build(FIXTURES, cache_dir=None)
    return semantics.enrich(art) if enrich else art


def a_ctx():
    art = build_artifact()
    return art, indexmod.Index(art)


class TestExplainNode(unittest.TestCase):
    def test_fact_node(self):
        art, idx = a_ctx()
        d = explain.explain_node(idx, idx.node("func::db::save"))
        self.assertEqual(d["what"]["type"], "Function")
        self.assertEqual(d["what"]["name"], "save")
        self.assertEqual(d["what"]["id"], "func::db::save")
        self.assertTrue(d["what"]["loc"])                      # rel:line evidence
        self.assertTrue(d["why"].startswith("[FACT]"))
        self.assertIn("confidence 1.0", d["why"].splitlines()[0])
        self.assertEqual(d["how"]["stages"][0], "build (AST extract, deterministic)")

    def test_fact_relations(self):
        art, idx = a_ctx()
        d = explain.explain_node(idx, idx.node("func::db::save"))
        rels = d["what"]["relations"]
        self.assertIn("func::models::validate", rels["callees"])   # save calls validate
        self.assertEqual(d["what"]["relations"]["callers"][0], "func::services.store::store")

    def test_module_node(self):
        art, idx = a_ctx()
        d = explain.explain_node(idx, idx.node("module::db"))
        rels = d["what"]["relations"]
        self.assertIn("module::models", rels["imports"])
        self.assertIn("module::services.store", rels["imported_by"])

    def test_hypothesis_how(self):
        art, idx = a_ctx()
        flows = [n for n in art["nodes"] if n["type"] == "Flow"]
        self.assertTrue(flows)
        d = explain.explain_node(idx, flows[0])
        self.assertTrue(all(s.startswith("enrich")
                            for s in d["how"]["stages"]))
        self.assertTrue(d["why"].startswith("[HYPOTHESIS]"))

    def test_deterministic(self):
        art1, idx1 = a_ctx()
        art2, idx2 = a_ctx()
        d1 = explain.explain_node(idx1, idx1.node("func::db::save"))
        d2 = explain.explain_node(idx2, idx2.node("func::db::save"))
        self.assertEqual(d1, d2)


class TestExplainChanged(unittest.TestCase):
    def test_change_bundle(self):
        art, idx = a_ctx()
        d = explain.explain_changed(art, ["db.py"], index=idx)
        self.assertIn("db.py", d["what"]["changed_files"])
        self.assertEqual(d["what"]["affected_modules"]["db"]["path"], "db.py")
        self.assertIn("func::db::save", d["what"]["affected_modules"]["db"]["symbols"])
        self.assertEqual(d["why"]["counts"]["modules"], 1)
        self.assertGreater(d["why"]["counts"]["importers"], 0)   # services.store imports db
        self.assertIn("func::services.store::store", d["why"]["callers_of_changed"]["func::db::save"])
        self.assertTrue(d["how"]["steps"])

    def test_missing_module(self):
        art, idx = a_ctx()
        d = explain.explain_changed(art, ["brand_new.py"], index=idx)
        self.assertIn("brand_new.py", d["what"]["missing_modules"])

    def test_deterministic(self):
        art1, idx1 = a_ctx()
        art2, idx2 = a_ctx()
        self.assertEqual(
            explain.explain_changed(art1, ["db.py"], index=idx1),
            explain.explain_changed(art2, ["db.py"], index=idx2))


class TestVerifyExplanation(unittest.TestCase):
    def test_grounded_pass(self):
        art, idx = a_ctx()
        n = ("I updated `db.py` so that `save` now calls `models.validate` "
             "to keep validation in one place.")
        d = explain.verify_explanation(art, ["db.py"], n, index=idx)
        self.assertEqual(d["verdict"], "PASS")
        self.assertEqual(d["groundedness"], 1.0)
        self.assertEqual(d["citations"]["invented"], 0)
        self.assertGreaterEqual(d["citations"]["present"], 3)
        self.assertGreaterEqual(d["citations"]["in_scope"], 2)

    def test_invented_reference_review(self):
        art, idx = a_ctx()
        n = "I moved the logic into `save_all_items` (should not exist here)."
        d = explain.verify_explanation(art, ["db.py"], n, index=idx)
        self.assertEqual(d["verdict"], "REVIEW")
        self.assertIn("save_all_items", d["citations"]["invented_details"])
        self.assertEqual(d["groundedness"], 0.0)

    def test_external_import_not_invented(self):
        import copy
        art, idx = a_ctx()
        art = copy.deepcopy(art)
        art["edges"].append({
            "source": "module::db", "target": "import::plain:os",
            "relationship": "IMPORTS", "confidence": 1.0,
            "evidence": [{"type": "parser", "source": "db.py"}], "metadata": {"alias": None},
        })
        idx = indexmod.Index(art)
        n = "I added an ``os`` call to ``db.py``; it now touches the filesystem."
        d = explain.verify_explanation(art, ["db.py"], n, index=idx)
        self.assertEqual(d["citations"]["invented"], 0)
        self.assertGreaterEqual(d["citations"]["external"], 1)

    def test_unsupported_claim(self):
        art, idx = a_ctx()
        n = "I refactored the persistence flow to be more robust. It now handles edge cases."
        d = explain.verify_explanation(art, ["db.py"], n, index=idx)
        self.assertTrue(d["claims"]["unsupported"])

    def test_consistency_failure(self):
        art, idx = a_ctx()
        # `init_db` exists but never calls anything -> asserted relation absent
        n = "The change makes `init_db` call `models.validate`."
        d = explain.verify_explanation(art, ["db.py"], n, index=idx)
        self.assertTrue(d["claims"]["consistency_failures"])

    def test_unquoted_resolves_but_never_invents(self):
        art, idx = a_ctx()
        n = "I touched init_db and the save path; init_db is a one-liner."
        d = explain.verify_explanation(art, ["db.py"], n, index=idx)
        # init_db is not quoted -> resolves as an unquoted hit, never counted invented
        self.assertEqual(d["citations"]["invented"], 0)
        self.assertGreaterEqual(d["citations"]["unquoted_hits"], 1)

    def test_empty_narration(self):
        art, idx = a_ctx()
        d = explain.verify_explanation(art, ["db.py"], "", index=idx)
        self.assertEqual(d["verdict"], "REVIEW")

    def test_deterministic(self):
        art1, idx1 = a_ctx()
        art2, idx2 = a_ctx()
        n = "I changed `db.py`: `save` calls `models.validate`."
        self.assertEqual(
            explain.verify_explanation(art1, ["db.py"], n, index=idx1),
            explain.verify_explanation(art2, ["db.py"], n, index=idx2))


class TestExplainMCP(unittest.TestCase):
    """Wiring through the MCP surface (ADR-009): explain + verify_explanation."""

    def setUp(self):
        from ssrl import mcp
        self.srv = mcp.MCPServer(FIXTURES, cache_dir=None)

    def _tool(self, name, args):
        r = self.srv.handle(
            {"jsonrpc": "2.0", "id": 9, "method": "tools/call",
             "params": {"name": name, "arguments": args}})
        self.assertNotIn("error", r, r)
        text = r["result"]["content"][0]["text"]
        return text, r["result"].get("isError")

    def test_explain_node_tool(self):
        text, err = self._tool("explain", {"node": "func::db::save"})
        self.assertIsNone(err)
        self.assertIn("WHAT", text)
        self.assertIn("Function", text)
        self.assertIn("WHY", text)
        self.assertIn("HOW", text)

    def test_explain_change_tool(self):
        text, err = self._tool("explain", {"files": ["db.py"]})
        self.assertIsNone(err)
        self.assertIn("module db", text)

    def test_explain_requires_one_mode(self):
        r = self.srv.handle(
            {"jsonrpc": "2.0", "id": 10, "method": "tools/call",
             "params": {"name": "explain",
                        "arguments": {"node": "x", "files": ["db.py"]}}})
        self.assertTrue(r["result"]["isError"])

    def test_verify_tool_pass(self):
        text, err = self._tool("verify_explanation", {
            "files": ["db.py"],
            "narration": "I changed `db.py`: `save` now calls `models.validate`.",
        })
        self.assertIsNone(err)
        self.assertIn("VERDICT: PASS", text)

    def test_verify_tool_invented(self):
        text, err = self._tool("verify_explanation", {
            "files": ["db.py"],
            "narration": "I extracted parsing into `parse_logs_forever`.",
        })
        self.assertIsNone(err)
        self.assertIn("VERDICT: REVIEW", text)
        self.assertIn("parse_logs_forever", text)


if __name__ == "__main__":
    unittest.main()