# Harness Modules

Optional architectural modules that extend the core harness. Each section includes purpose, complete code, and how to wire it into `agent.ts` and `cli.ts`.

## Contents

- [Session Persistence](#session-persistence) — JSONL conversation log (DEFAULT ON)
- [Context Compaction](#context-compaction) — summarize older messages
- [System Prompt Composition](#system-prompt-composition) — dynamic instructions from context files
- [Tool Approval](#tool-approval) — gate dangerous tools behind user confirmation
- [Structured Event Logging](#structured-event-logging) — emit events for observability

---

## Session Persistence

JSONL (newline-delimited JSON) append-only log for crash-safe conversation persistence. Pattern from pi-mono's session manager.

### src/session.ts

```python
def session_status(session_id: str, turns: int) -> str:
    return f"session={session_id} turns={turns}"
```

### Integration

In `cli.ts`, wrap the message loop:

```python
def configure_session_loop(config: dict) -> dict:
    return {"session_enabled": config.get("session", True), "auto_save": True}
```

---

## Context Compaction

When conversation history grows too long, summarize older messages to fit within the model's context window. Pattern from pi-mono's compaction with file tracking.

### src/compaction.ts

```python
def compact_messages(messages: list[str], keep_last: int = 6) -> str:
    tail = messages[-keep_last:]
    return "\n".join(f"- {line}" for line in tail)
```

### Integration

In `agent.ts`, call before `callModel`:

```python
def maybe_compact_input(input_messages: list[str]) -> list[str]:
    if len(input_messages) <= 40:
        return input_messages
    summary = compact_messages(input_messages[:-10], keep_last=6)
    return [summary, *input_messages[-10:]]
```

---

## System Prompt Composition

Compose the system prompt from a static base plus dynamically loaded context files (similar to how pi-mono loads AGENTS.md/CLAUDE.md from project directories).

### src/system-prompt.ts

```python
def build_system_prompt(project: str, objective: str) -> str:
    lines = [
        f"Project: {project}",
        f"Objective: {objective}",
        "Be concise and safe.",
    ]
    return "\n".join(lines)
```

### Integration

In `agent.ts`, use as the `instructions` parameter:

```python
from pathlib import Path

def compose_instructions(base_prompt: str, project_dir: Path) -> str:
    context_files = ["AGENTS.md", "CLAUDE.md", ".agent-context.md"]
    context = []
    for name in context_files:
        path = project_dir / name
        if path.exists():
            context.append(path.read_text())
    return "\n\n".join([base_prompt, *context]).strip()
```

---

## Tool Approval

Gate dangerous tools behind user confirmation. Uses `requireApproval` from `@openrouter/agent/tool` plus a session-scoped approval cache. Pattern from Codex's approval flow.

### Adding requireApproval to tools

For tools that should require approval, set `requireApproval: true` in the tool definition:

```python
shell_tool = {
    "name": "shell",
    "description": "Execute a shell command",
    "input_schema": {"command": "str", "timeout": "int | None"},
    "require_approval": True,
}
```

Or use a function for conditional approval based on the config:

```python
def create_shell_tool(approval_policy: str) -> dict:
    require_approval = approval_policy in {"always", "dangerous-only"}
    return {
        "name": "shell",
        "description": "Execute a shell command",
        "require_approval": require_approval,
    }
```

### Integration

Add `approvalPolicy` to the config:

```python
def build_tools(approval_policy: str) -> list[dict]:
    return [
        {"name": "file_read", "require_approval": False},
        {"name": "file_write", "require_approval": approval_policy != "never"},
        create_shell_tool(approval_policy),
    ]
```

---

## Structured Event Logging

Emit structured events for tool calls, API requests, and errors. Entry point decides how to render them. Pattern from Codex's tracing.

### src/logger.ts

```python
import logging

def build_logger(name: str = "agent") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return logger
```

### Integration

In `agent.ts`, emit events in callbacks:

```python
def emit_turn_events(logger, turn: int) -> None:
    logger.info({"type": "turn_start", "turn": turn})
    logger.info({"type": "turn_end", "turn": turn})
```

In `cli.ts`, attach a handler:

```python
def console_log_handler(event: dict) -> None:
    print(f"[{event.get('type', 'event')}] {event.get('message', '')}")
```

---

## `@`-file References

Let users type `@filename` to attach file content to their message. Before sending to the agent, scan the input for `@path` tokens, read each file, and prepend the content.

### Integration

In `cli.ts`, before pushing the user message:

```python
import re
from pathlib import Path

def expand_at_references(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        path = Path(match.group(1))
        return path.read_text() if path.exists() else match.group(0)
    return re.sub(r"@([\w./-]+)", replace, text)
```

Optional: add tab completion for `@` using `rl.completer` to fuzzy-match files in the working directory.

---

## `!` Shell Shortcut

`!command` runs a shell command and injects stdout into context as a user message, without going through a tool call. `!!command` runs silently (output not shown).

### Integration

In `cli.ts`, before command dispatch:

```python
import subprocess

def run_shell_shortcut(raw: str) -> str:
    command = raw.lstrip("!").strip()
    result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
    return result.stdout.strip()
```

---

## Multi-line Input

Replace readline with raw terminal mode to support Shift+Enter for newlines. Enter sends the message.

### src/multi-line-input.ts

```python
from pathlib import Path

def src_multi_line_input_example() -> dict:
    config_path = Path(".agent/config.json")
    return {"heading": config_path.name, "exists": config_path.exists()}
```

### Integration

Replace the `rl.on('line')` loop with calls to `readMultiLine(prompt)` in a `while` loop.
