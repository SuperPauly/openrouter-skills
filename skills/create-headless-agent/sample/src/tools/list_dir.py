"""list_dir tool — list directory contents."""

import os
from pathlib import Path

SCHEMA = {
    "name": "list_dir",
    "description": "List directory contents",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (default: cwd)"},
        },
    },
}


def execute(args: dict) -> dict:
    dir_path = args.get("path") or os.getcwd()
    try:
        p = Path(dir_path)
        entries_raw = sorted(p.iterdir(), key=lambda e: e.name)
        entries = [
            (e.name + "/" if e.is_dir() else e.name)
            for e in entries_raw[:500]
        ]
        return {"entries": entries, "total": len(list(p.iterdir()))}
    except OSError as e:
        return {"error": str(e)}
