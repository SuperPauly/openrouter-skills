#!/usr/bin/env python3
"""
Compare two or more models side by side.

Usage: python compare_models.py <model-id-1> <model-id-2> [...] [--sort price|context|speed|throughput]

Examples:
  python compare_models.py "anthropic/claude-sonnet-4" "openai/gpt-4o"
  python compare_models.py "anthropic/claude-sonnet-4" "google/gemini-2.5-pro" --sort price
"""
import sys
import json
from lib import optional_api_key, fetch_api, parse_args

api_key = optional_api_key()
args = parse_args(sys.argv[1:])
sort_by = args.get("sort")

# Collect positional model IDs
model_ids: list[str] = []
i = 0
while True:
    val = args.get(f"_{i}")
    if val is None:
        break
    model_ids.append(str(val))
    i += 1

if len(model_ids) < 2:
    print(
        'Usage: python compare_models.py <model-id-1> <model-id-2> [...] [--sort price|context|speed|throughput]\n\n'
        'Examples:\n'
        '  python compare_models.py "anthropic/claude-sonnet-4" "openai/gpt-4o"\n'
        '  python compare_models.py "anthropic/claude-sonnet-4" "google/gemini-2.5-pro" --sort price\n\n'
        'Sort options:\n'
        '  price      - Sort by prompt cost (cheapest first)\n'
        '  context    - Sort by context length (largest first)\n'
        '  speed      - Sort by max completion tokens (largest first)\n'
        '  throughput - Alias for speed',
        file=sys.stderr,
    )
    sys.exit(1)

data = fetch_api("/models", api_key)
all_models = data.get("data") or []

matched: list[dict] = []
for model_id in model_ids:
    lower_id = model_id.lower()
    exact = next((m for m in all_models if m.get("id", "").lower() == lower_id), None)
    if exact:
        matched.append(exact)
    else:
        partial = [m for m in all_models if lower_id in m.get("id", "").lower()]
        if not partial:
            print(f'Warning: No model found matching "{model_id}". Skipping.', file=sys.stderr)
        elif len(partial) == 1:
            matched.append(partial[0])
        else:
            others = ", ".join(m["id"] for m in partial[1:4])
            suffix = "..." if len(partial) > 4 else ""
            print(
                f'Warning: "{model_id}" matched {len(partial)} models. Using closest match: {partial[0]["id"]}\n'
                f'  Other matches: {others}{suffix}',
                file=sys.stderr,
            )
            matched.append(partial[0])

if len(matched) < 2:
    print("Need at least 2 models to compare. Use list_models.py to find valid IDs.", file=sys.stderr)
    sys.exit(1)

if sort_by == "price":
    matched.sort(key=lambda m: float((m.get("pricing") or {}).get("prompt") or "0"))
elif sort_by == "context":
    matched.sort(key=lambda m: m.get("context_length") or 0, reverse=True)
elif sort_by in ("speed", "throughput"):
    matched.sort(
        key=lambda m: (m.get("top_provider") or {}).get("max_completion_tokens") or 0,
        reverse=True,
    )

comparison = []
for m in matched:
    pricing = m.get("pricing") or {}
    prompt_cost = float(pricing.get("prompt") or "0") * 1_000_000
    completion_cost = float(pricing.get("completion") or "0") * 1_000_000
    cache_raw = pricing.get("input_cache_read")
    cache_cost = float(cache_raw) * 1_000_000 if cache_raw else None
    arch = m.get("architecture") or {}
    top = m.get("top_provider") or {}
    pricing_out: dict = {
        "prompt": f"${prompt_cost:.2f}",
        "completion": f"${completion_cost:.2f}",
    }
    if cache_cost is not None:
        pricing_out["cached_input"] = f"${cache_cost:.2f}"
    entry: dict = {
        "id": m.get("id"),
        "name": m.get("name"),
        "context_length": m.get("context_length"),
        "max_completion_tokens": top.get("max_completion_tokens"),
        "per_request_limits": m.get("per_request_limits"),
        "pricing_per_million_tokens": pricing_out,
        "modalities": {
            "input": arch.get("input_modalities") or [],
            "output": arch.get("output_modalities") or [],
        },
        "supported_parameters": m.get("supported_parameters") or [],
        "is_moderated": top.get("is_moderated"),
    }
    if m.get("expiration_date"):
        entry["expiration_date"] = m["expiration_date"]
    comparison.append(entry)

print(json.dumps(comparison, indent=2))
