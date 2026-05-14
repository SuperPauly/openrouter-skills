"""
Shared utilities for OpenRouter model scripts.
Python equivalent of lib.ts
"""

import os
import sys
import json
from typing import Optional, Any

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


def require_api_key() -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print(
            "Error: OPENROUTER_API_KEY environment variable is not set.\n"
            "Get your API key at https://openrouter.ai/keys",
            file=sys.stderr,
        )
        sys.exit(1)
    return api_key


def optional_api_key() -> Optional[str]:
    return os.environ.get("OPENROUTER_API_KEY")


def fetch_api(path: str, api_key: Optional[str] = None) -> Any:
    url = f"https://openrouter.ai/api/v1{path}"
    headers: dict[str, str] = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = requests.get(url, headers=headers)
    if not resp.ok:
        body = resp.text
        if resp.status_code == 401:
            print("Error 401: Invalid API key. Check your OPENROUTER_API_KEY.", file=sys.stderr)
        elif resp.status_code == 404:
            print(f"Error 404: Not found — {url}", file=sys.stderr)
            print("Use list_models.py to see available model IDs.", file=sys.stderr)
        elif resp.status_code == 429:
            print("Error 429: Rate limited. Wait a moment and try again.", file=sys.stderr)
        else:
            print(f"Error {resp.status_code}: {body or resp.reason}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def format_model(m: dict) -> dict:
    result: dict = {
        "id": m.get("id"),
        "name": m.get("name"),
        "description": m.get("description"),
        "created": m.get("created"),
        "context_length": m.get("context_length"),
        "pricing": m.get("pricing"),
        "architecture": m.get("architecture"),
        "top_provider": m.get("top_provider"),
        "per_request_limits": m.get("per_request_limits"),
        "supported_parameters": m.get("supported_parameters"),
    }
    if m.get("expiration_date"):
        result["expiration_date"] = m["expiration_date"]
    return result


def parse_args(argv: list[str]) -> dict[str, Any]:
    """
    Parse CLI args in the same style as the TypeScript parseArgs:
    --flag value  -> {"flag": "value"}
    --flag        -> {"flag": True}
    positional    -> {"_0": val, "_1": val, ...}
    also sets "_count" = number of positional args
    """
    result: dict[str, Any] = {}
    positional: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                result[key] = argv[i + 1]
                i += 2
            else:
                result[key] = True
                i += 1
        else:
            positional.append(argv[i])
            i += 1
    for idx, val in enumerate(positional):
        result[f"_{idx}"] = val
    result["_count"] = str(len(positional))
    return result
