#!/usr/bin/env python3
"""
List all models available on OpenRouter.

Usage: python list_models.py [--category <cat>] [--sort newest|price|context|throughput]

Examples:
  python list_models.py
  python list_models.py --sort newest
  python list_models.py --category programming --sort price
"""
import sys
import json
from lib import optional_api_key, fetch_api, format_model, parse_args

api_key = optional_api_key()
args = parse_args(sys.argv[1:])

category = args.get("category")
sort = args.get("sort")

path = f"/models?category={__import__('urllib.parse', fromlist=['quote']).quote(str(category))}" if category else "/models"

data = fetch_api(path, api_key)
models = [format_model(m) for m in (data.get("data") or [])]

# Warn about expiring models
expiring = [m for m in models if m.get("expiration_date")]
if expiring:
    print(f"Warning: {len(expiring)} model(s) have upcoming expiration dates.\n", file=sys.stderr)

if sort == "newest":
    models.sort(key=lambda m: m.get("created") or 0, reverse=True)
elif sort == "price":
    models.sort(key=lambda m: float((m.get("pricing") or {}).get("prompt") or "0"))
elif sort == "context":
    models.sort(key=lambda m: m.get("context_length") or 0, reverse=True)
elif sort in ("throughput", "speed"):
    models.sort(
        key=lambda m: (m.get("top_provider") or {}).get("max_completion_tokens") or 0,
        reverse=True,
    )

print(json.dumps(models, indent=2))
