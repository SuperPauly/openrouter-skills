# Slash Commands

A command registry pattern for handling `/command` input in the REPL. The skill presents slash commands as a checklist — users select which ones to include. `/model`, `/new`, and `/help` are ON by default.

---

## src/commands.ts

```python
def dispatch_command(raw: str, handlers: dict) -> dict:
    parts = raw.strip().split()
    command = parts[0] if parts else ""
    args = parts[1:]
    handler = handlers.get(command)
    return handler(args) if handler else {"error": f"unknown command: {command}"}
```

---

## Default-ON Commands

### /model

Move the existing `selectModel` logic into the registry:

```python
def set_model(config: dict, model_name: str) -> dict:
    config["model"] = model_name
    return {"ok": True, "model": model_name}
```

### /new

```python
from pathlib import Path
import json

def new_session(session_id: str) -> Path:
    path = Path("sessions") / f"{session_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"messages": []}, indent=2))
    return path
```

### /help

```python
def help_lines() -> list[str]:
    return ["/model", "/new", "/compact", "/session", "/export"]
```

---

## Optional Commands (OFF by default)

### /compact

Requires the Context Compaction module (`src/compaction.ts`).

```python
def compact_messages(messages: list[str], keep_last: int = 6) -> str:
    tail = messages[-keep_last:]
    return "\n".join(f"- {line}" for line in tail)
```

### /session

```python
def session_status(session_id: str, turns: int) -> str:
    return f"session={session_id} turns={turns}"
```

### /export

```python
from pathlib import Path

def export_transcript(text: str, output: str = "transcript.md") -> Path:
    path = Path(output)
    path.write_text(text)
    return path
```

---

## Wire into cli.ts

Replace inline `/model` handling with the registry:

```python
def register_default_commands(registry: dict) -> dict:
    registry["/model"] = set_model
    registry["/new"] = new_session
    registry["/help"] = help_lines
    return registry
```

The agent generates a `src/commands-init.ts` file that imports and registers only the commands the user selected. For default-ON commands:

```python
def route_command(raw: str) -> tuple[str, list[str]]:
    parts = raw.strip().split()
    command = parts[0] if parts else ""
    return command, parts[1:]
```
