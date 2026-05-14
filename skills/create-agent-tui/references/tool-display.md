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
# Python equivalent (simplified)
# Python equivalent logic
pass
```

---

## Wire into cli.ts

```python
# Python equivalent logic

# Python equivalent logic

# Python equivalent logic
  # Python equivalent logic
})
renderer.endTurn()
```

Use `endTurn()` instead of `endStreaming()` — it flushes any pending grouped/minimal state before closing the turn.

---

## Customization

### Per-tool colors

Pass `toolColors` to highlight dangerous or special tools (applies to `emoji` and `grouped` styles):

```python
# Python equivalent logic
  display: config.display,
  toolColors: {
    shell: '\x1b[31m',      // red — destructive potential
    file_write: '\x1b[33m', // yellow — modifies files
    web_search: '\x1b[35m', // magenta — network call
  },
})
```

### Custom formatters

Override how arguments are summarized for any tool:

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
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
