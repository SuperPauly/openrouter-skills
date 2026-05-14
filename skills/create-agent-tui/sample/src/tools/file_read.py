"""file_read tool — read file contents with optional offset/limit."""

import base64
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
LINE_CAP = 2000
CHAR_CAP = 2000

SCHEMA = {
    "name": "file_read",
    "description": "Read the contents of a file. For images, returns base64 data. "
                   "Text files support offset/limit for pagination.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "offset": {"type": "number", "description": "Start reading from this line number (1-indexed)"},
            "limit": {"type": "number", "description": "Maximum number of lines to return (default 2000)"},
        },
        "required": ["path"],
    },
}


def execute(args: dict) -> dict:
    path = args.get("path", "")
    offset = int(args.get("offset") or 1)
    limit = int(args.get("limit") or LINE_CAP)

    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}

    if p.suffix.lower() in IMAGE_EXTS:
        data = p.read_bytes()
        b64 = base64.b64encode(data).decode("ascii")
        mime = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp",
        }.get(p.suffix.lower(), "image/png")
        return {"type": "image", "data": b64, "mimeType": mime}

    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"error": str(e)}

    lines = text.splitlines()
    total = len(lines)
    start = max(0, offset - 1)
    end = start + limit
    sliced = lines[start:end]

    # Per-line truncation
    truncated_lines = 0
    processed = []
    for line in sliced:
        if len(line) > CHAR_CAP:
            dropped = len(line) - CHAR_CAP
            processed.append(line[:CHAR_CAP] + f"… [line truncated, {dropped} chars dropped]")
            truncated_lines += 1
        else:
            processed.append(line)

    tail_truncated = end < total
    any_truncated = tail_truncated or truncated_lines > 0

    result: dict = {
        "content": "\n".join(processed),
        "totalLines": total,
        "truncated": any_truncated,
    }

    if any_truncated:
        hint_parts = []
        if tail_truncated:
            hint_parts.append(f"Showing lines {start + 1}-{start + len(sliced)} of {total}. Use offset={start + len(sliced) + 1} to continue.")
            result["nextOffset"] = start + len(sliced) + 1
        if truncated_lines > 0:
            hint_parts.append(f"{truncated_lines} line(s) exceeded {CHAR_CAP} chars and were per-line truncated; use grep to fetch content from those lines.")
        result["hint"] = " ".join(hint_parts)

    return result
