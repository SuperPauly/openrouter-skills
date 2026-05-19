# Python TUI Tools Reference

Local tools are plain Python callables with JSON-compatible inputs and outputs. Hosted OpenRouter tools are declared in the request payload and execute on OpenRouter's side.

## Tool Declaration Pattern

```python
from collections.abc import Callable
from typing import Any

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]

TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": "read_file",
        "description": "Read a text file with optional line range.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "offset": {"type": "integer", "minimum": 0},
                "limit": {"type": "integer", "minimum": 1, "maximum": 500},
            },
            "required": ["path"],
        },
    }
]

HANDLERS: dict[str, ToolHandler] = {}

def register_tool(name: str, handler: ToolHandler) -> None:
    HANDLERS[name] = handler

def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"error": f"unknown tool: {name}"}
    return handler(arguments)
```

## File Read

```python
from pathlib import Path

def read_file(args: dict) -> dict:
    path = Path(args["path"]).expanduser().resolve()
    offset = int(args.get("offset", 0))
    limit = int(args.get("limit", 200))
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    selected = lines[offset:offset + limit]
    return {
        "path": str(path),
        "content": "\n".join(selected),
        "total_lines": len(lines),
        "truncated": offset + limit < len(lines),
    }
```

## File Write

```python
from pathlib import Path

def write_file(args: dict) -> dict:
    path = Path(args["path"]).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(args["content"], encoding="utf-8")
    return {"written": True, "path": str(path)}
```

## File Edit

```python
from pathlib import Path
import difflib

def edit_file(args: dict) -> dict:
    path = Path(args["path"]).expanduser().resolve()
    original = path.read_text(encoding="utf-8")
    old = args["old"]
    new = args["new"]
    if old not in original:
        return {"edited": False, "error": "old text not found"}
    updated = original.replace(old, new, 1)
    path.write_text(updated, encoding="utf-8")
    diff = "\n".join(difflib.unified_diff(
        original.splitlines(), updated.splitlines(),
        fromfile=str(path), tofile=str(path), lineterm="",
    ))
    return {"edited": True, "path": str(path), "diff": diff}
```

## Glob

```python
from pathlib import Path

def glob_files(args: dict) -> dict:
    base = Path(args.get("path", ".")).expanduser().resolve()
    pattern = args.get("pattern", "**/*")
    results = []
    for item in base.rglob(pattern):
        rel = item.relative_to(base).as_posix()
        if ".git" in rel.split("/") or "__pycache__" in rel.split("/"):
            continue
        results.append(rel)
        if len(results) >= 1000:
            break
    return {"matches": results, "truncated": len(results) >= 1000}
```

## Grep

```python
import re
import subprocess
from pathlib import Path

def grep(args: dict) -> dict:
    pattern = args["pattern"]
    base = Path(args.get("path", ".")).resolve()
    try:
        proc = subprocess.run(
            ["rg", "--line-number", pattern, str(base)],
            text=True, capture_output=True, timeout=20, check=False,
        )
        matches = proc.stdout.splitlines()[:100]
        return {"matches": matches, "truncated": len(matches) == 100}
    except FileNotFoundError:
        rx = re.compile(pattern)
        matches = []
        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue
            for line_no, line in enumerate(file_path.read_text(errors="ignore").splitlines(), 1):
                if rx.search(line):
                    matches.append(f"{file_path}:{line_no}:{line}")
                    if len(matches) >= 100:
                        return {"matches": matches, "truncated": True}
        return {"matches": matches, "truncated": False}
```

## Shell

```python
import subprocess

def run_shell(args: dict) -> dict:
    proc = subprocess.run(
        args["command"],
        shell=True,
        text=True,
        capture_output=True,
        timeout=int(args.get("timeout", 30)),
        check=False,
    )
    return {"stdout": proc.stdout, "stderr": proc.stderr, "exit_code": proc.returncode}
```

## Custom Tool

```python
def custom_tool(args: dict) -> dict:
    value = args.get("value", "")
    return {"message": f"received {value}"}
```
