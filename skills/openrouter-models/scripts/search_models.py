#!/usr/bin/env python3
"""
Search models by name/ID or filter by modality.

Usage: python search_models.py <query> [--modality <modality>]

Examples:
  python search_models.py "claude"
  python search_models.py --modality image
  python search_models.py "gpt" --modality text
"""
import sys
import json
from lib import optional_api_key, fetch_api, format_model, parse_args

api_key = optional_api_key()
args = parse_args(sys.argv[1:])

query = args.get("_0")
modality = args.get("modality")

if not query and not modality:
    print(
        'Usage: python search_models.py <query> [--modality <modality>]\n\n'
        'Examples:\n'
        '  python search_models.py "claude"\n'
        '  python search_models.py --modality image\n'
        '  python search_models.py "gpt" --modality text',
        file=sys.stderr,
    )
    sys.exit(1)

data = fetch_api("/models", api_key)
models = data.get("data") or []

if query:
    lower = query.lower()
    models = [
        m for m in models
        if lower in (m.get("id") or "").lower() or lower in (m.get("name") or "").lower()
    ]

if modality:
    lower_mod = modality.lower()
    def has_modality(m: dict) -> bool:
        arch = m.get("architecture") or {}
        inp: list = arch.get("input_modalities") or []
        out: list = arch.get("output_modalities") or []
        return lower_mod in [x.lower() for x in inp + out]
    models = [m for m in models if has_modality(m)]

print(json.dumps([format_model(m) for m in models], indent=2))
