# Tool Display Styles

Three tool display styles are available, configured via `config.display.toolDisplay`. The default is `grouped`.

| Style | Look | Description |
|-------|------|-------------|
| `emoji` | `⚡ shell command=ls` / `✓ shell (0.3s)` | Per-call emoji markers with args and timing |
| `grouped` | `● Ran pwd` / `└ /Users/alex/...` | Bold action labels with tree-branch output |
| `minimal` | `Searched for 1 pattern, ran 2 shell commands` | Aggregated one-liner summaries |
| `hidden` | *(no output)* | Suppresses all tool display |

---

## Tool Labels

Shared label mappings used by `grouped` and `minimal` styles:

```python
TOOL_LABELS = {
    "shell": {"past": "Ran", "noun": "shell command"},
    "file_read": {"past": "Read", "noun": "file"},
    "file_write": {"past": "Wrote", "noun": "file"},
    "file_edit": {"past": "Edited", "noun": "file"},
    "glob": {"past": "Explored", "noun": "pattern"},
    "grep": {"past": "Searched", "noun": "pattern"},
    "list_dir": {"past": "Listed", "noun": "directory"},
    "web_search": {"past": "Fetched", "noun": "search"},
}
```

---

## src/renderer.ts

```python
def format_shell_args(args: dict) -> str:
    command = args.get("command", "")
    return command[:60] + ("..." if len(command) > 60 else "")
```

---

## Wire into cli.ts

```python
def render_turn(renderer, events: list[dict]) -> None:
    for event in events:
        renderer.render_tool_call(event)
    renderer.end_turn()
```

Use `endTurn()` instead of `endStreaming()` — it flushes any pending grouped/minimal state before closing the turn.

---

## Customization

### Per-tool colors

Pass `toolColors` to highlight dangerous or special tools (applies to `emoji` and `grouped` styles):

```python
TOOL_COLORS = {
    "shell": "\x1b[31m",
    "file_write": "\x1b[33m",
    "web_search": "\x1b[35m",
}
```

### Custom formatters

Override how arguments are summarized for any tool:

```python
import json

def render_tool_event(name: str, args: dict, result: dict) -> str:
    return (
        f"tool={name}\n"
        f"args={json.dumps(args, ensure_ascii=False)}\n"
        f"result={json.dumps(result, ensure_ascii=False)}"
    )
```

### Display modes via config

Set in `agent.config.json`:

```json
{
  "display": {
    "toolDisplay": "grouped",
    "reasoning": true
  }
}
```

| Mode | Behavior |
|------|----------|
| `emoji` | Per-call `⚡`/`✓` markers with tool name, args, and timing |
| `grouped` | Bold action labels (`● Ran`, `● Explored`) with `└` tree-branch output, consecutive same-type calls merged under one bullet |
| `minimal` | Aggregated one-liner summaries (`searched for 1 pattern, ran 2 shell commands`) flushed when text resumes |
| `hidden` | No tool output |
