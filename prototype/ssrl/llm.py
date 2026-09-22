"""SSRL micro-LLM hypothesis proponent (Phase 9, ADR-008).

The ONLY stage that may call a language model. Everything else in SSRL stays
deterministic and dependency-free. The model *proposes*; structure disposes:

  - Context = "evidence bundles" (facts only, hard caps, ~<=700 tokens).
  - Tasks (closed, tiny): flow-intent naming + unit-role labeling.
  - Outputs are always Intent *hypotheses* with evidence type `LLMProposal`,
    ceiling-capped at 0.5 (confidence.SOURCE_CEILING) and re-scored by the
    calibration engine; deterministic evidence is never overwritten.
  - Providers (stdlib `urllib` only): Ollama /api/chat, OpenAI-compatible
    /v1/chat/completions (llama.cpp, vLLM, LM Studio), and a deterministic
    MockProvider for tests and offline runs.

Target model: Qwen3-0.6B (Instruct) class — see research/decisions/ADR-008.
"""

import json
import re
import time
import urllib.error
import urllib.request

from . import confidence, index as indexmod, model

ROLE_TAXONOMY = ("persistence", "model", "service", "config", "infra", "entrypoint",
                 "controller", "ui", "util", "unknown")

FLOW_PROMPT_SYSTEM = (
    "You are a code-comprehension assistant for a deterministic tool. The facts below "
    "come from an AST caller graph — trust them exactly; do not invent function or file "
    "names. Name the behavior of this function chain in at most 6 English words. "
    "Return ONLY a JSON object: {\"label\": str, \"confidence\": float 0..1, "
    "\"rationale\": str <= 80 chars}. No reasoning text, no explanation."
)

UNIT_PROMPT_SYSTEM = (
    "You are a code-comprehension assistant for a deterministic tool. The facts below "
    "come from an AST index — trust them exactly; do not invent names. Classify the role "
    "of this unit. Choose exactly ONE role from: {taxa}. "
    "Return ONLY a JSON object: {\"role\": str, \"confidence\": float 0..1, "
    "\"rationale\": str <= 80 chars}. No reasoning text, no explanation."
)

MAX_FLOW_CHARS = 2600
MAX_UNIT_CHARS = 2200
MAX_STEP_LINES = 24


class _HttpUnreachable(Exception):
    pass


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

class Provider:
    """Base: complete(messages, max_tokens) -> dict|None with text + token stats."""

    name = "base"
    reachable = False

    def probe(self):
        raise NotImplementedError

    def complete(self, system, user, max_tokens=220):
        raise NotImplementedError


class OllamaProvider(Provider):
    """Local Ollama (default model: qwen3:0.6b). /api/chat, format=json, temp 0."""

    name = "ollama"

    def __init__(self, endpoint="http://localhost:11434", model="qwen3:0.6b", timeout=30.0):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.timeout = timeout

    def probe(self):
        try:
            with urllib.request.urlopen(f"{self.endpoint}/api/tags", timeout=min(self.timeout, 5)) as r:
                body = json.loads(r.read().decode("utf-8", "replace"))
            self.reachable = self.model in {m["name"] for m in body.get("models", [])}
        except (urllib.error.URLError, OSError, ValueError):
            self.reachable = False
        return self.reachable

    def complete(self, system, user, max_tokens=220):
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "stream": False,
            "format": "json",
            "think": False,
            "options": {"temperature": 0.0, "num_predict": max_tokens},
        }
        req = urllib.request.Request(
            f"{self.endpoint}/api/chat", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        text = (data.get("message") or {}).get("content", "")
        return {"text": text, "tokens_prompt": data.get("prompt_eval_count", 0),
                "tokens_eval": data.get("eval_count", 0)}


class OpenAICompatProvider(Provider):
    """OpenAI-compatible chat endpoint (llama.cpp server / vLLM / LM Studio)."""

    name = "openai"

    def __init__(self, endpoint, model, api_key=None, timeout=30.0):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def probe(self):
        try:
            req = urllib.request.Request(f"{self.endpoint}/v1/models", headers=self._headers())
            with urllib.request.urlopen(req, timeout=min(self.timeout, 5)) as r:
                body = json.loads(r.read().decode("utf-8", "replace"))
            ids = [m.get("id") for m in body.get("data", [])]
            self.reachable = not ids or self.model in ids
        except (urllib.error.URLError, OSError, ValueError):
            self.reachable = False
        return self.reachable

    def complete(self, system, user, max_tokens=220):
        payload = {"model": self.model, "temperature": 0.0, "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]}
        req = urllib.request.Request(
            f"{self.endpoint}/v1/chat/completions", data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(), method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        text = (((data.get("choices") or [{}])[0].get("message") or {}).get("content", ""))
        usage = data.get("usage", {})
        return {"text": text, "tokens_prompt": usage.get("prompt_tokens", 0),
                "tokens_eval": usage.get("completion_tokens", 0)}


class MockProvider(Provider):
    """Deterministic canned proposer (tests / offline runs). label derives from facts."""

    name = "mock"
    reachable = True

    def __init__(self):
        self.calls = 0

    def probe(self):
        return True

    def complete(self, system, user, max_tokens=220):
        self.calls += 1
        # stable fabrications from the facts in the prompt: first symbol ids + modules
        ids = re.findall(r"`([A-Za-z0-9_:#.]+)`", user)
        head = [token for token in ids if token.lower() != "repo"][:3]
        stem = (head[0].split("::")[-1].split(".")[-1] if head else "behavior")
        role = "persistence" if "db" in user.lower() else "service"
        text = json.dumps({"label": f"handle {stem}", "role": role, "confidence": 0.55,
                           "rationale": f"mock proposal for {head[0] if head else 'unknown'}"})
        return {"text": text, "tokens_prompt": len(user) // 4,
                "tokens_eval": len(text) // 4}


# ---------------------------------------------------------------------------
# Evidence bundles (context design, ADR-008 §4)
# ---------------------------------------------------------------------------

def _loc(node):
    return node["evidence"][0]["source"] if node.get("evidence") else "-"


def _line(node, limit=80):
    doc = (node.get("metadata") or {}).get("doc") or ""
    doc1 = doc.splitlines()[0][:limit] if doc else ""
    return f"  - `{node['id']}` [{_loc(node)}] {doc1}".rstrip()


def flow_bundle(index, flow_node):
    """Build the flow-intent evidence bundle (facts only, capped)."""
    steps = sorted((flow_node.get("metadata") or {}).get("steps") or [],
                   key=lambda s: s.replace("::", "/"))
    lines = [f"repo: {index.artifact['stats'].get('files')} files / flow id: `{flow_node['id']}`"]
    entry = (flow_node.get("metadata") or {}).get("entry")
    if entry and index.node(entry):
        lines.append(_line(index.node(entry)))
    for sid in steps[:MAX_STEP_LINES]:
        n = index.node(sid)
        if n:
            lines.append(_line(n))
    return {"kind": "flow", "text": "\n".join(lines), "chars": sum(len(l) + 1 for l in lines),
            "steps": len(steps)}


def unit_bundle(index, node):
    """Build the unit-role evidence bundle (module/class facts only, capped)."""
    doc = (node.get("metadata") or {}).get("doc") or ""
    imports = [n["name"].split("::")[-1] for n in index.imports_of(node["id"], include_external=True)
               if n.get("type") == "Import"][:8]
    kids = [n for e in index.children(node["id"], "CONTAINS")
            for n in [index.by_id.get(e["target"])] if n]
    names = [n["name"] for n in kids][:12]
    called = set()
    callee_names = []
    for n in kids:
        for c in index.callees_of(n["id"]):
            if c["id"] not in called:
                called.add(c["id"])
                callee_names.append(c["name"])
                if len(callee_names) >= 8:
                    break
    caller_ids = {c["id"] for n in kids for c in index.callers_of(n["id"])}
    lines = [f"repo: {index.artifact['stats'].get('files')} files / unit `{node['id']}` [{_loc(node)}]",
             f"doc: {doc.splitlines()[0][:180] if doc else '(none)'}",
             f"imports: {', '.join(imports) or '(none external)'}",
             f"contained: {', '.join(names) or '(none)'}",
             f"callers: {len(caller_ids)} | callees: {', '.join(callee_names) or '(none)'}"]
    return {"kind": "unit", "text": "\n".join(lines), "chars": sum(len(l) + 1 for l in lines),
            "symbols": len(kids)}


# ---------------------------------------------------------------------------
# Prompting + parsing + validation
# ---------------------------------------------------------------------------

def _extract_json(text):
    if not text:
        return None
    text = text.strip().strip("`").strip()
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except ValueError:
            pass
    m = re.search(r'"((?:label)|(?:role))\s*[:=]\s*"([^"]+)"', text)
    return {"label": m.group(2)} if m else None


def _clean_value(obj, key, fallback=""):
    if not isinstance(obj, dict):
        return fallback
    v = obj.get(key)
    return v if isinstance(v, str) else fallback


def _clean_conf(obj):
    if not isinstance(obj, dict):
        return 0.5
    try:
        c = float(obj.get("confidence", 0.5))
    except (TypeError, ValueError):
        return 0.5
    return 0.5 if not (0.0 <= c <= 1.0) else round(c, 3)


def parse_flow_decision(text, bundle=None):
    obj = _extract_json(text)
    if obj is None:
        return None
    label = _clean_value(obj, "label").strip()
    if not label or len(label.split()) > 6:
        return None
    return {"kind": "flow", "label": _clean_value(obj, "label"),
            "confidence": _clean_conf(obj), "rationale": _clean_value(obj, "rationale")[:160]}


def parse_unit_decision(text, bundle=None):
    obj = _extract_json(text)
    if obj is None:
        return None
    role = _clean_value(obj, "role").strip().lower()
    if role not in ROLE_TAXONOMY:
        return None
    return {"kind": "unit", "role": role, "confidence": _clean_conf(obj),
            "rationale": _clean_value(obj, "rationale")[:160]}


# ---------------------------------------------------------------------------
# Proposal runner + materialization
# ---------------------------------------------------------------------------

def _slug(label):
    s = re.sub(r"[^a-z0-9]+", "-", (label or "").lower()).strip("-")
    return s[:40] or "unnamed"


def propose_flows(index, artifact, runner, bundle_fn=flow_bundle):
    """Run Task A over every Flow. Returns (decisions, stats)."""
    flows = sorted((n for n in artifact["nodes"] if n["type"] == "Flow"),
                   key=lambda n: n["id"])
    decisions, stats = [], _new_stats()
    for fn in flows:
        bundle = bundle_fn(index, fn)
        if bundle["chars"] > MAX_FLOW_CHARS:
            stats["skipped"] += 1
            continue
        try:
            out = runner.complete(FLOW_PROMPT_SYSTEM, bundle["text"])
        except (urllib.error.URLError, OSError, TimeoutError):
            stats["errors"] += 1
            continue
        stats["requests"] += 1
        if out is None:
            stats["errors"] += 1
            continue
        stats["tokens_prompt"] += out.get("tokens_prompt", 0)
        stats["tokens_eval"] += out.get("tokens_eval", 0)
        dec = parse_flow_decision(out.get("text"), bundle)
        if dec is None:
            stats["rejected"] += 1
            continue
        dec["target"] = fn["id"]
        decisions.append(dec)
        stats["accepted"] += 1
    return decisions, stats


def propose_units(index, artifact, runner, bundle_fn=unit_bundle, include_init=True):
    """Run Task B over Module (and Class) nodes. Returns (decisions, stats)."""
    nodes = [n for n in artifact["nodes"] if n["type"] in ("Module", "Class")]
    if not include_init:
        nodes = [n for n in nodes if not (n["id"].endswith(".__init__") or n["name"] == "__init__.py")]
    decisions, stats = [], _new_stats()
    for node in sorted(nodes, key=lambda n: n["id"]):
        bundle = bundle_fn(index, node)
        if bundle["chars"] > MAX_UNIT_CHARS:
            stats["skipped"] += 1
            continue
        try:
            out = runner.complete(UNIT_PROMPT_SYSTEM.replace("{taxa}", ", ".join(ROLE_TAXONOMY)),
                                  bundle["text"])
        except (urllib.error.URLError, OSError, TimeoutError):
            stats["errors"] += 1
            continue
        stats["requests"] += 1
        if out is None:
            stats["errors"] += 1
            continue
        stats["tokens_prompt"] += out.get("tokens_prompt", 0)
        stats["tokens_eval"] += out.get("tokens_eval", 0)
        dec = parse_unit_decision(out.get("text"), bundle)
        if dec is None:
            stats["rejected"] += 1
            continue
        dec["target"] = node["id"]
        dec["label"] = dec.pop("role")
        decisions.append(dec)
        stats["accepted"] += 1
    return decisions, stats


def _new_stats():
    return {"requests": 0, "accepted": 0, "rejected": 0, "skipped": 0, "errors": 0,
            "covered": 0, "tokens_prompt": 0, "tokens_eval": 0, "elapsed_s": 0.0}


def apply_proposals(artifact, decisions, index=None):
    """Materialize proposals as Intent hypotheses (ADR-008 §6). Returns (stats, added)."""
    index = index or indexmod.Index(artifact)
    existing = {n["id"] for n in artifact["nodes"] if n["type"] == "Intent"}
    stats = _new_stats()
    added = []
    for dec in decisions:
        iid = f"intent::{dec['target']}:{_slug(dec['label'])}"
        if iid in existing:
            stats["covered"] += 1
            continue
        weight = round(min(dec["confidence"], confidence.SOURCE_CEILING["LLMProposal"]), 3)
        node = {
            "id": iid, "type": "Intent", "name": dec["label"], "confidence": weight,
            "evidence": [{"type": "LLMProposal", "source": dec["target"], "weight": weight}],
            "metadata": {"target": dec["target"], "hypothesis": True, "origin": "llm",
                         "rationale": dec.get("rationale", ""), "llm_conf": dec["confidence"]},
        }
        edge = model.make_edge(dec["target"], iid, "SUPPORTS_INTENT",
                               [{"type": "LLMProposal", "source": dec["target"], "weight": weight}],
                               {"hypothesis": True})
        artifact["nodes"].append(node)
        artifact["edges"].append(edge)
        existing.add(iid)
        added.append(node)
        stats["accepted"] += 1
    artifact["stats"]["llm_proposed"] = {"requests": stats["requests"], "added": len(added),
                                         "covered": stats["covered"]}
    return stats, added


def _accum(dst, src):
    for k in ("requests", "accepted", "rejected", "skipped", "errors",
              "tokens_prompt", "tokens_eval"):
        dst[k] += src.get(k, 0)


def run(index, artifact, runner, scope="flows"):
    """Full propose run for a scope. Returns (artifact, stats)."""
    start = time.time()
    decisions = []
    stats = _new_stats()
    if scope in ("flows", "all"):
        d, s = propose_flows(index, artifact, runner)
        decisions += d
        _accum(stats, s)
    if scope in ("units", "all"):
        d, s = propose_units(index, artifact, runner)
        decisions += d
        _accum(stats, s)
    apply_stats, added = apply_proposals(artifact, decisions, index=index)
    stats["accepted"] = len(added)
    stats["covered"] = apply_stats["covered"]
    stats["elapsed_s"] = round(time.time() - start, 3)
    return artifact, stats


def make_provider(provider_name="ollama", endpoint=None, model="qwen3:0.6b",
                  api_key=None, timeout=30.0):
    """Provider factory for the CLI (ADR-008 §5)."""
    if provider_name == "mock":
        return MockProvider()
    if provider_name == "ollama":
        return OllamaProvider(endpoint or "http://localhost:11434", model, timeout)
    if provider_name == "openai":
        return OpenAICompatProvider(endpoint, model, api_key, timeout)
    raise ValueError(f"unknown provider: {provider_name}")