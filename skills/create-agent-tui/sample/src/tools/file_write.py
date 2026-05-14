"""file_write tool — write content to a file."""

from pathlib import Path

SCHEMA = {
    "name": "file_write",
    "description": "Write content to a file, creating it and parent directories if needed",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "content": {"type": "string", "description": "Content to write"},
        },
        "required": ["path", "content"],
    },
}


def execute(args: dict) -> dict:
    path = args.get("path", "")
    content = args.get("content", "")
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"written": True, "path": str(p.resolve())}
    except OSError as e:
        return {"error": str(e)}
