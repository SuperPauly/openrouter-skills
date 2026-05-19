# Python System Prompt Module

Use a dedicated module when the system prompt is assembled from project files, generated context, or user-selected instructions.

```python
from pathlib import Path

DEFAULT_CONTEXT_FILES = ["AGENTS.md", "README.md", ".agent-context.md"]


def build_system_prompt(base: str, project_dir: str = ".", context_files: list[str] | None = None) -> str:
    files = context_files or DEFAULT_CONTEXT_FILES
    root = Path(project_dir)
    parts = [base]
    for name in files:
        file_path = root / name
        if file_path.exists() and file_path.is_file():
            content = file_path.read_text(encoding="utf-8", errors="replace")
            parts.append(f"\n# {name}\n{content}")
    return "\n".join(parts)
```

Use it in `agent.py`:

```python
from .system_prompt import build_system_prompt

instructions = build_system_prompt(config.instructions, config.project_dir, config.context_files)
```

Recommended config:

```json
{
  "instructions": "You are a focused coding assistant.",
  "project_dir": ".",
  "context_files": ["AGENTS.md", "README.md"]
}
```
