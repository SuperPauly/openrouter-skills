"""
Shared utilities for OpenRouter image scripts.
Python equivalent of lib.ts
"""

import os
import sys
import json
import base64
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

try:
    import requests
except ImportError:
    print("Error: 'requests' package is required. Install with: pip install requests", file=sys.stderr)
    sys.exit(1)

DEFAULT_MODEL = "google/gemini-3.1-flash-image-preview"

MIME_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


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


def parse_args(argv: list[str]) -> dict[str, Any]:
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


def post_chat_completion(api_key: str, body: dict) -> Any:
    url = "https://openrouter.ai/api/v1/chat/completions"
    resp = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=body,
    )
    if not resp.ok:
        text = resp.text
        if resp.status_code == 401:
            print("Error 401: Invalid API key. Check your OPENROUTER_API_KEY.", file=sys.stderr)
        elif resp.status_code == 429:
            print("Error 429: Rate limited. Wait a moment and try again.", file=sys.stderr)
        else:
            print(f"Error {resp.status_code}: {text or resp.reason}", file=sys.stderr)
        sys.exit(1)
    return resp.json()


def read_image_as_data_url(file_path: str) -> str:
    abs_path = Path(file_path).resolve()
    ext = abs_path.suffix.lower()
    mime = MIME_MAP.get(ext)
    if not mime:
        print(
            f'Error: Unsupported image format "{ext}". Use .png, .jpg, .jpeg, .webp, or .gif',
            file=sys.stderr,
        )
        sys.exit(1)
    data = abs_path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def save_image(data_url: str, output_path: str) -> str:
    match = re.match(r"^data:[^;]+;base64,(.+)$", data_url)
    if not match:
        print("Error: Invalid data URL format in response.", file=sys.stderr)
        sys.exit(1)
    abs_path = Path(output_path).resolve()
    abs_path.write_bytes(base64.b64decode(match.group(1)))
    return str(abs_path)


def default_output_path() -> str:
    now = datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    return f"image-{stamp}.png"
