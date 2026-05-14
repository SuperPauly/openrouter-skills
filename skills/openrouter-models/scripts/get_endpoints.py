#!/usr/bin/env python3
"""
Show per-provider performance data for a model.

Usage: python get_endpoints.py <model-id> [--sort throughput|latency|uptime|price]

Examples:
  python get_endpoints.py "anthropic/claude-sonnet-4"
  python get_endpoints.py "anthropic/claude-sonnet-4" --sort throughput
  python get_endpoints.py "openai/gpt-4o" --sort latency
"""
import sys
import json
from lib import require_api_key, fetch_api, parse_args

api_key = require_api_key()
args = parse_args(sys.argv[1:])
model_id = args.get("_0")
sort_by = args.get("sort")

if not model_id:
    print(
        'Usage: python get_endpoints.py <model-id> [--sort throughput|latency|uptime|price]\n\n'
        'Shows per-provider performance data for a model:\n'
        '  - Latency percentiles (p50/p75/p90/p99) in ms\n'
        '  - Uptime % over last 30 minutes\n'
        '  - Throughput (tokens/sec) percentiles\n'
        '  - Provider-specific pricing and limits\n\n'
        'Sort options:\n'
        '  throughput - Fastest generation speed first (highest p50 tokens/sec)\n'
        '  latency   - Lowest response latency first (lowest p50 ms)\n'
        '  uptime    - Most reliable first (highest uptime %)\n'
        '  price     - Cheapest first (lowest prompt cost)\n\n'
        'Examples:\n'
        '  python get_endpoints.py "anthropic/claude-sonnet-4"\n'
        '  python get_endpoints.py "anthropic/claude-sonnet-4" --sort throughput\n'
        '  python get_endpoints.py "openai/gpt-4o" --sort latency',
        file=sys.stderr,
    )
    sys.exit(1)

data = fetch_api(f"/models/{model_id}/endpoints", api_key)
payload = data.get("data") or {}

if not payload.get("endpoints"):
    print(f"No provider endpoints found for model: {model_id}", file=sys.stderr)
    sys.exit(1)

endpoints = payload["endpoints"]

if sort_by == "throughput":
    endpoints.sort(key=lambda e: (e.get("throughput_last_30m") or {}).get("p50") or 0, reverse=True)
elif sort_by == "latency":
    endpoints.sort(key=lambda e: (e.get("latency_last_30m") or {}).get("p50") or float("inf"))
elif sort_by == "uptime":
    endpoints.sort(key=lambda e: e.get("uptime_last_30m") or 0, reverse=True)
elif sort_by == "price":
    endpoints.sort(
        key=lambda e: float((e.get("pricing") or {}).get("prompt") or "0")
    )

def fmt_ep(ep: dict) -> dict:
    pricing = ep.get("pricing") or {}
    prompt_m = float(pricing.get("prompt") or "0") * 1_000_000
    comp_m = float(pricing.get("completion") or "0") * 1_000_000
    pricing_out: dict = {
        "prompt": f"${prompt_m:.2f}",
        "completion": f"${comp_m:.2f}",
    }
    if pricing.get("input_cache_read"):
        pricing_out["cached_input"] = f"${float(pricing['input_cache_read']) * 1_000_000:.2f}"
    if pricing.get("discount"):
        pricing_out["discount"] = f"{int(float(pricing['discount']) * 100)}%"
    status_val = ep.get("status")
    status_str = "operational" if status_val == 0 else f"degraded ({status_val})"
    uptime = ep.get("uptime_last_30m")
    quant = ep.get("quantization")
    result: dict = {
        "provider": ep.get("provider_name"),
        "tag": ep.get("tag"),
        "status": status_str,
        "uptime_30m": f"{uptime:.2f}%" if uptime is not None else None,
        "latency_30m_ms": ep.get("latency_last_30m"),
        "throughput_30m_tokens_per_sec": ep.get("throughput_last_30m"),
        "context_length": ep.get("context_length"),
        "max_completion_tokens": ep.get("max_completion_tokens"),
        "max_prompt_tokens": ep.get("max_prompt_tokens"),
        "pricing_per_million_tokens": pricing_out,
        "quantization": quant if quant != "unknown" else None,
        "supports_implicit_caching": ep.get("supports_implicit_caching"),
        "supported_parameters": ep.get("supported_parameters"),
    }
    return result

output = {
    "model_id": payload.get("id"),
    "model_name": payload.get("name"),
    "total_providers": len(endpoints),
    "endpoints": [fmt_ep(ep) for ep in endpoints],
}

print(json.dumps(output, indent=2))
