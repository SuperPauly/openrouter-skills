"""file_edit tool — apply search-and-replace edits to a file."""

from pathlib import Path


SCHEMA = {
    "name": "file_edit",
    "description": "Apply search-and-replace edits to a file. Each edit must match exactly once.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "edits": {
                "type": "array",
                "description": "List of search-and-replace operations",
                "items": {
                    "type": "object",
                    "properties": {
                        "old_text": {"type": "string", "description": "Text to find (must match exactly once)"},
                        "new_text": {"type": "string", "description": "Replacement text"},
                    },
                    "required": ["old_text", "new_text"],
                },
            },
        },
        "required": ["path", "edits"],
    },
}


def _make_diff(original: str, modified: str, path: str) -> str:
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    import difflib
    diff = difflib.unified_diff(orig_lines, mod_lines, fromfile=f"a/{path}", tofile=f"b/{path}")
    return "".join(diff)


def execute(args: dict) -> dict:
    path = args.get("path", "")
    edits: list = args.get("edits") or []

    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}

    try:
        original = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"error": str(e)}

    text = original
    for i, edit in enumerate(edits):
        old = edit.get("old_text", "")
        new = edit.get("new_text", "")
        count = text.count(old)
        if count == 0:
            return {"error": f"Edit {i + 1}: old_text not found in file"}
        if count > 1:
            return {"error": f"Edit {i + 1}: old_text matches {count} times — must match exactly once"}
        text = text.replace(old, new, 1)

    try:
        p.write_text(text, encoding="utf-8")
    except OSError as e:
        return {"error": str(e)}

    diff = _make_diff(original, text, path)
    return {"edited": True, "path": str(p.resolve()), "diff": diff}
