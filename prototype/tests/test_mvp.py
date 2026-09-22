import os
import sys
import unittest

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "pkgapp")
SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, SRC)

from ssrl import confidence, extract, impact as impactmod, index as indexmod, llm, mcp, model, narrative as narr, qa, semantics, watch as watchmod


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


class TestWatch(unittest.TestCase):
    def setUp(self):
        import shutil, tempfile
        self.tmp = tempfile.mkdtemp()
        self.d = os.path.join(self.tmp, "repo")
        shutil.copytree(FIXTURES, self.d)
        self.cache_dir = os.path.join(self.tmp, "cache")
        self.w = watchmod.Watch(self.d, cache_dir=self.cache_dir, interval=0.0)
        self.addCleanup(self.w.close)

    def _write(self, rel, content):
        p = os.path.join(self.d, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)

    def test_diff_detects_add_modify_remove(self):
        base = watchmod.scan(self.d)
        self._write("newmod.py", "def fresh():\n    return 1\n")
        self._write("db.py", "# changed\ndef save():\n    pass\n")
        os.remove(os.path.join(self.d, "main.py"))
        added, modified, removed = watchmod.diff(base, watchmod.scan(self.d))
        self.assertEqual(added, ["newmod.py"])
        self.assertEqual(modified, ["db.py"])
        self.assertEqual(removed, ["main.py"])

    def test_initial_sync_parses_everything(self):
        ev = self.w.initial_sync()
        self.assertEqual(ev["type"], "initial")
        self.assertEqual(ev["reparsed"], 6)
        self.assertEqual(ev["from_cache"], 0)
        self.assertEqual(ev["files"], 6)
        self.assertEqual(ev["errors"], 0)

    def test_change_reparses_only_delta(self):
        start = self.w.initial_sync()
        self._write("db.py", "# evolved\nimport sqlite3\n\ndef connect(path):\n    return None\n\ndef save(row):\n    pass\n\ndef new_feature():\n    return 'x'\n")
        ev = self.w.step()
        self.assertIsNotNone(ev)
        self.assertEqual(ev["type"], "change")
        self.assertEqual(ev["modified"], ["db.py"])
        self.assertEqual(ev["reparsed"], 1)
        self.assertEqual(ev["from_cache"], 5)
        self.assertEqual(ev["delta"]["nodes"], 1)

    def test_static_cycle_returns_none(self):
        self.w.initial_sync()
        self.assertIsNone(self.w.step())

    def test_deletion_is_reflected(self):
        start = self.w.initial_sync()
        os.remove(os.path.join(self.d, "main.py"))
        ev = self.w.step()
        self.assertEqual(ev["removed"], ["main.py"])
        self.assertEqual(ev["files"], 5)
        self.assertLess(ev["nodes"], start["nodes"])

    def test_revert_restores_artifact(self):
        orig = open(os.path.join(self.d, "db.py"), encoding="utf-8").read()
        start = self.w.initial_sync()
        self._write("db.py", orig + "\ndef extra_new():\n    return 2\n")
        temp = self.w.step()
        self.assertGreater(temp["nodes"], start["nodes"])
        self._write("db.py", orig)
        ev = self.w.step()
        self.assertEqual(ev["nodes"], start["nodes"])
        self.assertEqual(ev["reparsed"], 1)
        self.assertEqual(ev["from_cache"], 5)


class TestImpact(unittest.TestCase):
    def setUp(self):
        art = build_artifact(enrich=True)
        self.idx = indexmod.Index(art)
        self.art = art

    def test_changed_db_module(self):
        r = impactmod.impact_changed(self.art, ["db.py"], index=self.idx)
        self.assertEqual(r["counts"], {"files": 1, "modules": 1, "importers": 1,
                                       "callers": 1, "entries": 1, "flows": 1,
                                       "missing": 0})
        self.assertEqual(set(r["affected_modules"]), {"db"})
        self.assertEqual(r["affected_modules"]["db"]["symbols"],
                         ["func::db::init_db", "func::db::save"])
        self.assertEqual(r["importers"]["db"], ["module::services.store"])
        self.assertEqual(r["callers_of_changed"],
                         {"func::db::save": ["func::services.store::store"]})
        self.assertEqual(r["entry_points_touched"], ["func::db::init_db"])
        self.assertEqual(r["flows_affected"], ["flow::func::services.store::store"])
        self.assertIn("module::services.store", r["reverse_dependent_modules"])

    def test_changed_entry_point_module(self):
        r = impactmod.impact_changed(self.art, ["services/store.py"], index=self.idx)
        self.assertEqual(r["counts"]["modules"], 1)
        self.assertEqual(r["affected_modules"]["services.store"]["symbols"],
                         ["func::services.store::store"])
        self.assertEqual(r["importers"], {})
        self.assertEqual(r["callers_of_changed"], {})
        self.assertEqual(r["entry_points_touched"], ["func::services.store::store"])
        self.assertEqual(r["flows_affected"], ["flow::func::services.store::store"])

    def test_ignores_non_py_and_missing(self):
        r = impactmod.impact_changed(self.art, ["db.py", "README.md", "gone.py"],
                                     index=self.idx)
        self.assertEqual(r["ignored"], ["README.md"])
        self.assertEqual(r["missing_modules"], ["gone.py"])
        self.assertEqual(set(r["affected_modules"]), {"db"})

    def test_deterministic(self):
        a = impactmod.impact_changed(self.art, ["db.py", "services/store.py"], index=self.idx)
        b = impactmod.impact_changed(self.art, ["services/store.py", "db.py"], index=self.idx)
        self.assertEqual(a, b)
        self.assertEqual(a["changed_files"], ["db.py", "services/store.py"])

    def test_render_impact_readable(self):
        r = impactmod.impact_changed(self.art, ["db.py"], index=self.idx)
        text = impactmod.render_impact(r)
        self.assertIn("module::db", text)
        self.assertIn("callers of func::db::save", text)
        self.assertIn("flow affected: flow::func::services.store::store", text)


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.srv = mcp.MCPServer(FIXTURES, enrich=True, cache_dir=None)

    def call(self, rid, method, params=None):
        msg = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            msg["params"] = params
        return self.srv.handle(msg)

    def _tool(self, name, args):
        return self.call(7, "tools/call", {"name": name, "arguments": args})

    def test_initialize_handshake(self):
        r = self.call(1, "initialize", {})
        self.assertEqual(r["id"], 1)
        self.assertEqual(r["result"]["protocolVersion"], mcp.PROTOCOL_VERSION)
        self.assertEqual(r["result"]["serverInfo"]["name"], "ssrl-mcp")
        self.assertIn("tools", r["result"]["capabilities"])

    def test_notification_gives_no_response(self):
        self.assertIsNone(self.srv.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_ping(self):
        r = self.call(2, "ping")
        self.assertEqual(r["result"], {})

    def test_tools_list(self):
        r = self.call(3, "tools/list")
        names = [t["name"] for t in r["result"]["tools"]]
        self.assertEqual(names, ["ask", "why", "narrative", "stats", "audit", "impact",
                                 "explain", "verify_explanation"])
        ask = next(t for t in r["result"]["tools"] if t["name"] == "ask")
        self.assertEqual(ask["inputSchema"]["required"], ["question"])

    def test_tools_call_ask_grounded(self):
        r = self._tool("ask", {"question": "who calls save"})
        self.assertFalse(r["result"].get("isError"))
        text = r["result"]["content"][0]["text"]
        self.assertIn("Callers of `save`", text)
        self.assertIn("Function `store`", text)
        self.assertIn("services/store.py:5", text)
        self.assertIn("FACTS", text)

    def test_tools_call_ask_missing_arg_errors(self):
        r = self._tool("ask", {})
        self.assertTrue(r["result"].get("isError"))
        self.assertIn("question", r["result"]["content"][0]["text"])

    def test_unknown_tool_is_error(self):
        r = self.call(8, "tools/call", {"name": "nope", "arguments": {}})
        self.assertEqual(r["error"]["code"], -32602)

    def test_why_resolves_name(self):
        r = self._tool("why", {"node": "save"})
        self.assertFalse(r["result"].get("isError"))
        self.assertIn("func::db::save", r["result"]["content"][0]["text"])

    def test_stats_tool(self):
        r = self._tool("stats", {})
        self.assertIn("files=6", r["result"]["content"][0]["text"])

    def test_audit_tool(self):
        r = self._tool("audit", {})
        self.assertIn("conf=", r["result"]["content"][0]["text"])

    def test_narrative_tool(self):
        r = self._tool("narrative", {})
        self.assertIn("Living Narrative", r["result"]["content"][0]["text"])

    def test_impact_tool(self):
        r = self._tool("impact", {"changed_files": ["db.py"]})
        text = r["result"]["content"][0]["text"]
        self.assertIn("module::db", text)
        self.assertIn("1 changed file(s)", text)

    def test_resources_empty(self):
        r = self.call(9, "resources/list")
        self.assertEqual(r["result"]["resources"], [])

    def test_unknown_method(self):
        r = self.call(10, "nope")
        self.assertEqual(r["error"]["code"], -32601)

    def test_serve_stdio_round_trip(self):
        import io, json as _json
        stream = (_json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
                  + "\n" + _json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
                  + "\n" + _json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                        "params": {"name": "stats", "arguments": {}}})
                  + "\nnot json\n")
        out = io.StringIO()
        self.srv.serve_stdio(io.StringIO(stream), stdout=out)
        responses = [l for l in out.getvalue().splitlines() if l.strip()]
        self.assertEqual(len(responses), 3)  # initialize, stats, parse error
        parsed = [_json.loads(l) for l in responses]
        self.assertEqual(parsed[0]["id"], 1)
        self.assertEqual(parsed[1]["result"]["content"][0]["text"].split("\n")[0].split(" ")[0],
                         "files=6")
        self.assertEqual(parsed[2]["error"]["code"], -32700)


class TestLLMProposer(unittest.TestCase):
    def setUp(self):
        self.art = build_artifact(enrich=True)
        self.idx = indexmod.Index(self.art)
        self.runner = llm.MockProvider()

    def test_mock_provider_deterministic_and_parses(self):
        d1 = llm.propose_flows(self.idx, self.art, self.runner)[0]
        self.runner = llm.MockProvider()
        d2, _ = llm.propose_flows(self.idx, self.art, self.runner)
        self.assertEqual(d1, d2)
        self.assertGreaterEqual(len(d1), len([n for n in self.art["nodes"] if n["type"] == "Flow"]))
        for dec in d1:
            self.assertEqual(dec["kind"], "flow")
            self.assertLessEqual(len(dec["label"].split()), 6)
            self.assertTrue(dec["target"].startswith("flow::"))

    def test_flow_bundle_facts_only_and_capped(self):
        flows = [n for n in self.art["nodes"] if n["type"] == "Flow"]
        flow = sorted(flows, key=lambda n: n["id"])[0]
        b = llm.flow_bundle(self.idx, flow)
        self.assertLessEqual(b["chars"], llm.MAX_FLOW_CHARS)
        self.assertIn(flow["id"], b["text"])
        for sid in (flow.get("metadata") or {}).get("steps", []):
            self.assertIn(sid, b["text"])

    def test_unit_bundle_and_taxonomy(self):
        mod = self.idx.node("module::db")
        b = llm.unit_bundle(self.idx, mod)
        self.assertLessEqual(b["chars"], llm.MAX_UNIT_CHARS)
        self.assertIn("module::db", b["text"])
        text = llm.UNIT_PROMPT_SYSTEM.replace("{taxa}", ", ".join(llm.ROLE_TAXONOMY))
        for role in llm.ROLE_TAXONOMY:
            self.assertIn(role, text)

    def test_parse_rejects_drift_and_bad_taxonomy(self):
        self.assertIsNone(llm.parse_flow_decision("not json at all"))
        self.assertIsNone(llm.parse_flow_decision("""{"label": "a very long label that exceeds six words allowed limit", "confidence": 0.9}"""))
        d = llm.parse_flow_decision("""{"label": "query db", "confidence": 0.6}""")
        self.assertEqual(d["label"], "query db")
        self.assertEqual(d["confidence"], 0.6)
        self.assertIsNone(llm.parse_unit_decision("""{"role": "made-up-role", "confidence": 0.9}"""))
        u = llm.parse_unit_decision("""{"role": "Persistence", "confidence": 0.7}""")
        self.assertEqual(u["role"], "persistence")

    def test_confidence_clamped(self):
        d = llm.parse_flow_decision("""{"label": "x", "confidence": 4}""")
        self.assertEqual(d["confidence"], 0.5)
        d2 = llm.parse_flow_decision("""{"label": "x", "confidence": null}""")
        self.assertEqual(d2["confidence"], 0.5)

    def test_apply_proposals_llm_ceiling_and_origin(self):
        r = llm.run(self.idx, self.art, self.runner, scope="flows")
        art, stats = r
        self.assertGreaterEqual(stats["accepted"], 1)
        self.assertLessEqual(stats["covered"], 2)
        proposed = [n for n in art["nodes"]
                    if (n.get("metadata") or {}).get("origin") == "llm"]
        self.assertGreaterEqual(len(proposed), stats["accepted"])
        for n in proposed:
            self.assertEqual(n["type"], "Intent")
            self.assertEqual(n["evidence"][0]["type"], "LLMProposal")
            self.assertLessEqual(n["evidence"][0]["weight"], 0.5)
            cal, note = confidence.calibrate(n)
            self.assertLessEqual(cal, 0.5)
        edges = [e for e in art["edges"] if e["relationship"] == "SUPPORTS_INTENT"
                 and e.get("metadata", {}).get("hypothesis")]
        self.assertGreaterEqual(len(edges), 1)

    def test_offline_provider_produces_no_errors_and_artifact_unchanged(self):
        class Offline(llm.MockProvider):
            def probe(self):
                return False
            def complete(self, system, user, max_tokens=220):
                raise TimeoutError("offline")
        base_nodes = [n["id"] for n in self.art["nodes"]]
        art, stats = llm.run(self.idx, self.art, Offline(), scope="all")
        self.assertEqual(stats["accepted"], 0)
        self.assertEqual([n["id"] for n in art["nodes"]], base_nodes)

    def test_scope_units_labels_modules(self):
        art, stats = llm.run(self.idx, self.art, self.runner, scope="units")
        self.assertGreaterEqual(stats["accepted"], 1)
        proposed = {n["id"] for n in art["nodes"]
                    if (n.get("metadata") or {}).get("origin") == "llm"}
        self.assertTrue(any(i.startswith("intent::module::") for i in proposed))
        audit_rows = confidence.audit([n for n in art["nodes"] if n["type"] == "Intent"])
        llm_rows = [r for r in audit_rows if "LLMProposal" in r["evidence_sources"]]
        self.assertGreaterEqual(len(llm_rows), 1)


if __name__ == "__main__":
    unittest.main()