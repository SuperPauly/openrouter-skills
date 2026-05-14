"""grep tool — search file contents by regex pattern."""

import os
import re
import subprocess
from pathlib import Path

SCHEMA = {
    "name": "grep",
    "description": "Search file contents by regex pattern",
    "parameters": {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "path": {"type": "string", "description": "Directory or file to search (default: cwd)"},
            "glob": {"type": "string", "description": 'File filter, e.g. "*.py"'},
            "ignoreCase": {"type": "boolean"},
        },
        "required": ["pattern"],
    },
}


def _rg_search(pattern: str, search_path: str, file_glob: str | None, ignore_case: bool) -> dict:
    args = ["rg", "--no-heading", "--line-number", "--color=never"]
    if ignore_case:
        args.append("-i")
    if file_glob:
        args.extend(["--glob", file_glob])
    args.extend(["--", pattern, search_path])
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode == 1:
        return {"matches": [], "total": 0}
    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        return {"error": stderr or f"rg exited with code {proc.returncode}"}
    all_lines = [l for l in proc.stdout.split("\n") if l]
    truncated = len(all_lines) > 100
    matches = []
    for line in all_lines[:100]:
        m = re.match(r"^(.+?):(\d+):(.*)$", line)
        if m:
            matches.append({"file": m.group(1), "line": int(m.group(2)), "content": m.group(3)})
        else:
            matches.append({"raw": line})
    result: dict = {"matches": matches, "total": len(all_lines)}
    if truncated:
        result["truncated"] = True
    return result


def _fallback_search(pattern: str, search_path: str, file_glob: str | None, ignore_case: bool) -> dict:
    flags = re.IGNORECASE if ignore_case else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return {"error": f"Invalid regex: {e}"}

    p = Path(search_path)
    files: list[Path] = []
    if p.is_file():
        files = [p]
    else:
        for root, dirs, fnames in os.walk(search_path):
            dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__")]
            for fname in fnames:
                if file_glob and not fnmatch.fnmatch(fname, file_glob):
                    continue
                files.append(Path(root) / fname)

    matches = []
    for f in files:
        try:
            for lineno, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                if regex.search(line):
                    matches.append({"file": str(f), "line": lineno, "content": line})
                    if len(matches) >= 100:
                        return {"matches": matches, "total": len(matches), "truncated": True}
        except OSError:
            continue
    return {"matches": matches, "total": len(matches)}


def execute(args: dict) -> dict:
    pattern = args.get("pattern", "")
    search_path = args.get("path") or os.getcwd()
    file_glob = args.get("glob")
    ignore_case = bool(args.get("ignoreCase", False))
    try:
        return _rg_search(pattern, search_path, file_glob, ignore_case)
    except FileNotFoundError:
        return _fallback_search(pattern, search_path, file_glob, ignore_case)
    except Exception as e:
        return {"error": str(e)}
