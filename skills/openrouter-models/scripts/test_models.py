"""Parity tests for openrouter-models Python scripts. No network required."""

import sys, os, json, unittest
from unittest.mock import patch
from io import StringIO

sys.path.insert(0, os.path.dirname(__file__))
import lib

MODEL_A = {"id": "openai/gpt-4o", "name": "OpenAI: GPT-4o", "description": "Flagship", "created": 1720000000, "context_length": 128000, "pricing": {"prompt": "0.0000025", "completion": "0.00001", "input_cache_read": "0.00000125"}, "architecture": {"input_modalities": ["text", "image"], "output_modalities": ["text"]}, "top_provider": {"max_completion_tokens": 16384, "is_moderated": True}, "per_request_limits": None, "supported_parameters": ["tools", "temperature"]}
MODEL_B = {"id": "anthropic/claude-haiku-4.5", "name": "Anthropic: Claude Haiku 4.5", "description": "Fast", "created": 1730000000, "context_length": 200000, "pricing": {"prompt": "0.0000008", "completion": "0.000004"}, "architecture": {"input_modalities": ["text", "image"], "output_modalities": ["text"]}, "top_provider": {"max_completion_tokens": 8096, "is_moderated": False}, "per_request_limits": None, "supported_parameters": ["tools"]}
MODEL_C = {"id": "google/gemini-2.5-flash", "name": "Google: Gemini 2.5 Flash", "description": "Multi", "created": 1710000000, "context_length": 32768, "pricing": {"prompt": "0.000000075", "completion": "0.0000003"}, "architecture": {"input_modalities": ["text", "image", "audio"], "output_modalities": ["text"]}, "top_provider": {"max_completion_tokens": 8192, "is_moderated": False}, "per_request_limits": None, "supported_parameters": ["tools"]}
MODELS_LIST = {"data": [MODEL_A, MODEL_B, MODEL_C]}

ENDPOINTS_RESP = {"data": {"id": "openai/gpt-4o", "name": "OpenAI: GPT-4o", "endpoints": [
    {"provider_name": "OpenAI", "tag": "openai", "status": 0, "uptime_last_30m": 99.5, "latency_last_30m": {"p50": 800, "p75": 1200, "p90": 2000, "p99": 5000}, "throughput_last_30m": {"p50": 45, "p75": 55, "p90": 65, "p99": 90}, "context_length": 128000, "max_completion_tokens": 16384, "max_prompt_tokens": None, "pricing": {"prompt": "0.0000025", "completion": "0.00001"}, "quantization": "unknown", "supports_implicit_caching": True, "supported_parameters": ["tools"]},
    {"provider_name": "Azure", "tag": "azure", "status": 0, "uptime_last_30m": 98.0, "latency_last_30m": {"p50": 1200, "p75": 1800, "p90": 3000, "p99": 8000}, "throughput_last_30m": {"p50": 30, "p75": 40, "p90": 55, "p99": 75}, "context_length": 128000, "max_completion_tokens": 16384, "max_prompt_tokens": None, "pricing": {"prompt": "0.0000030", "completion": "0.000012"}, "quantization": None, "supports_implicit_caching": False, "supported_parameters": ["tools"]},
]}}

def _fake_fetch(path, api_key=None):
    if path == "/models": return MODELS_LIST
    if "/endpoints" in path: return ENDPOINTS_RESP
    return {}

def _run(mod_name, argv, *, api_key=None, fake_fetch=_fake_fetch):
    sys.modules.pop(mod_name, None)
    buf = StringIO()
    env = {"OPENROUTER_API_KEY": api_key} if api_key else {}
    with patch.object(lib, "fetch_api", side_effect=fake_fetch), \
         patch("sys.argv", [f"{mod_name}.py"] + argv), \
         patch("sys.stdout", buf), \
         patch.dict(os.environ, env):
        __import__(mod_name)
    return json.loads(buf.getvalue())

def _run_exits(mod_name, argv, *, api_key=None):
    sys.modules.pop(mod_name, None)
    env = {"OPENROUTER_API_KEY": api_key} if api_key else {}
    with patch.object(lib, "fetch_api", side_effect=_fake_fetch), \
         patch("sys.argv", [f"{mod_name}.py"] + argv), \
         patch.dict(os.environ, env, clear=(api_key is None)):
        if api_key is None:
            os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            __import__(mod_name)
        except SystemExit as e:
            return e.code
    return None


class TestLib(unittest.TestCase):
    def test_format_model_fields(self):
        r = lib.format_model(MODEL_A)
        for f in ("id", "name", "context_length", "pricing", "architecture"):
            self.assertIn(f, r)
    def test_format_model_no_expiration_when_absent(self):
        self.assertNotIn("expiration_date", lib.format_model(MODEL_A))
    def test_format_model_expiration_when_present(self):
        self.assertEqual(lib.format_model({**MODEL_A, "expiration_date": "2026-12-31"})["expiration_date"], "2026-12-31")
    def test_parse_args_positional(self):
        r = lib.parse_args(["claude", "--sort", "newest"])
        self.assertEqual(r["_0"], "claude"); self.assertEqual(r["sort"], "newest")
    def test_parse_args_count(self):
        self.assertEqual(lib.parse_args(["--sort", "price"])["_count"], "0")
    def test_optional_api_key_none(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_API_KEY", None)
            self.assertIsNone(lib.optional_api_key())
    def test_optional_api_key_returns_value(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-test"}):
            self.assertEqual(lib.optional_api_key(), "sk-test")
    def test_require_api_key_exits_when_absent(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("OPENROUTER_API_KEY", None)
            with self.assertRaises(SystemExit) as ctx: lib.require_api_key()
        self.assertEqual(ctx.exception.code, 1)


class TestListModels(unittest.TestCase):
    def test_returns_all_models(self):
        self.assertEqual(len(_run("list_models", [])), 3)
    def test_sort_newest(self):
        r = _run("list_models", ["--sort", "newest"])
        d = [m["created"] for m in r]
        self.assertEqual(d, sorted(d, reverse=True))
    def test_sort_price(self):
        r = _run("list_models", ["--sort", "price"])
        p = [float((m["pricing"] or {}).get("prompt", "0")) for m in r]
        self.assertEqual(p, sorted(p))
    def test_sort_context(self):
        r = _run("list_models", ["--sort", "context"])
        l = [m["context_length"] for m in r]
        self.assertEqual(l, sorted(l, reverse=True))
    def test_output_shape(self):
        for m in _run("list_models", []):
            for f in ("id", "name", "context_length", "pricing"):
                self.assertIn(f, m)


class TestSearchModels(unittest.TestCase):
    def test_query_filters_name(self):
        r = _run("search_models", ["gpt"])
        self.assertTrue(all("gpt" in m["id"].lower() or "gpt" in m["name"].lower() for m in r))
    def test_modality_audio_filter(self):
        r = _run("search_models", ["--modality", "audio"])
        self.assertEqual(len(r), 1); self.assertEqual(r[0]["id"], "google/gemini-2.5-flash")
    def test_no_results_empty(self):
        self.assertEqual(_run("search_models", ["zzz_no_match"]), [])
    def test_missing_args_exits_1(self):
        self.assertEqual(_run_exits("search_models", []), 1)


class TestCompareModels(unittest.TestCase):
    def test_compare_two(self):
        self.assertEqual(len(_run("compare_models", ["openai/gpt-4o", "anthropic/claude-haiku-4.5"])), 2)
    def test_output_shape(self):
        for m in _run("compare_models", ["openai/gpt-4o", "anthropic/claude-haiku-4.5"]):
            p = m["pricing_per_million_tokens"]
            self.assertTrue(p["prompt"].startswith("$")); self.assertTrue(p["completion"].startswith("$"))
    def test_sort_price_cheapest_first(self):
        r = _run("compare_models", ["openai/gpt-4o", "anthropic/claude-haiku-4.5", "--sort", "price"])
        self.assertEqual(r[0]["id"], "anthropic/claude-haiku-4.5")
    def test_cached_input_included(self):
        r = _run("compare_models", ["openai/gpt-4o", "anthropic/claude-haiku-4.5"])
        gpt = next(m for m in r if m["id"] == "openai/gpt-4o")
        self.assertIn("cached_input", gpt["pricing_per_million_tokens"])
    def test_too_few_models_exits_1(self):
        self.assertEqual(_run_exits("compare_models", ["openai/gpt-4o"]), 1)


class TestGetEndpoints(unittest.TestCase):
    def test_output_shape(self):
        r = _run("get_endpoints", ["openai/gpt-4o"], api_key="sk-test")
        for f in ("model_id", "model_name", "total_providers", "endpoints"):
            self.assertIn(f, r)
    def test_sort_throughput(self):
        r = _run("get_endpoints", ["openai/gpt-4o", "--sort", "throughput"], api_key="sk-test")
        tp = [(e.get("throughput_30m_tokens_per_sec") or {}).get("p50", 0) for e in r["endpoints"]]
        self.assertEqual(tp, sorted(tp, reverse=True))
    def test_sort_latency(self):
        r = _run("get_endpoints", ["openai/gpt-4o", "--sort", "latency"], api_key="sk-test")
        lat = [(e.get("latency_30m_ms") or {}).get("p50", float("inf")) for e in r["endpoints"]]
        self.assertEqual(lat, sorted(lat))
    def test_status_formatted(self):
        r = _run("get_endpoints", ["openai/gpt-4o"], api_key="sk-test")
        for ep in r["endpoints"]: self.assertIn(ep["status"], ["operational", "degraded"])
    def test_missing_model_exits_1(self):
        self.assertEqual(_run_exits("get_endpoints", [], api_key="sk-test"), 1)
    def test_missing_key_exits_1(self):
        self.assertEqual(_run_exits("get_endpoints", ["openai/gpt-4o"]), 1)


class TestResolveModel(unittest.TestCase):
    def test_exact_match_high_confidence(self):
        r = _run("resolve_model", ["openai/gpt-4o"])
        self.assertEqual(len(r), 1); self.assertEqual(r[0]["confidence"], "high"); self.assertEqual(r[0]["score"], 1.0)
    def test_fuzzy_gpt4o(self):
        r = _run("resolve_model", ["gpt 4o"])
        self.assertTrue(len(r) >= 1); self.assertEqual(r[0]["id"], "openai/gpt-4o")
    def test_no_match_empty(self):
        self.assertEqual(_run("resolve_model", ["zzz_no_match_xyzxyz"]), [])
    def test_sorted_by_score_desc(self):
        r = _run("resolve_model", ["gpt 4o"])
        scores = [x["score"] for x in r]
        self.assertEqual(scores, sorted(scores, reverse=True))
    def test_output_has_confidence_score(self):
        r = _run("resolve_model", ["gpt 4o"])
        for x in r:
            self.assertIn(x["confidence"], ["high", "medium", "low"])
            self.assertGreaterEqual(x["score"], 0.0); self.assertLessEqual(x["score"], 1.0)
    def test_empty_query_exits_1(self):
        self.assertEqual(_run_exits("resolve_model", []), 1)


if __name__ == "__main__":
    unittest.main()
