"""glob tool — find files by glob pattern."""

import os
import fnmatch
from pathlib import Path

SCHEMA = {
    "name": "glob",
    "description": "Find files matching a glob pattern",
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": 'Glob pattern, e.g. "src/**/*.py"'},
            "path": {"type": "string", "description": "Directory to search in (default: cwd)"},
        },
        "required": ["pattern"],
    },
}


def execute(args: dict) -> dict:
    pattern = args.get("pattern", "**/*")
    search_dir = args.get("path") or os.getcwd()

    try:
        base = Path(search_dir)
        matches: list[str] = []
        for p in base.rglob(pattern.lstrip("/")):
            rel = str(p.relative_to(base))
            if "node_modules" in rel or ".git" in rel.split(os.sep):
                continue
            matches.append(rel)
            if len(matches) >= 1000:
                break

        truncated = len(matches) >= 1000
        result: dict = {"files": sorted(matches), "total": len(matches)}
        if truncated:
            result["truncated"] = True
        return result
    except OSError as e:
        return {"error": str(e)}
