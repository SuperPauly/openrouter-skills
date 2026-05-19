# Python Optional Modules

These modules extend the generated harness without changing the core agent loop. Add only the modules the user asks for.

## Session Persistence

`src/session.py` stores messages as JSON lines.

```python
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import uuid

Message = dict[str, object]

def init_session_dir(directory: str) -> Path:
    path = Path(directory).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path

def new_session_path(directory: str) -> Path:
    session_dir = init_session_dir(directory)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return session_dir / f"{stamp}-{uuid.uuid4().hex[:8]}.jsonl"

def save_message(session_path: Path, message: Message) -> None:
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "message": message}
    with session_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")

def load_session(session_path: Path) -> list[Message]:
    messages = []
    if not session_path.exists():
        return messages
    for line in session_path.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        message = entry.get("message")
        if isinstance(message, dict):
            messages.append(message)
    return messages
```

## Context Compaction

```python
import requests


def compact_messages(messages: list[dict], config: dict) -> list[dict]:
    keep_recent = int(config.get("keep_recent", 8))
    if len(messages) <= keep_recent + 4:
        return messages

    older = messages[:-keep_recent]
    recent = messages[-keep_recent:]
    summary_prompt = "Summarize this conversation for future turns:\n" + repr(older)
    response = requests.post(
        "https://openrouter.ai/api/v1/responses",
        headers=config["headers"],
        json={"model": config["summary_model"], "input": summary_prompt},
        timeout=60,
    )
    response.raise_for_status()
    summary = response.json()["output"][0]["content"][0]["text"]
    return [{"role": "system", "content": "Conversation summary: " + summary}, *recent]
```

## System Prompt Composition

```python
from pathlib import Path


def compose_system_prompt(base: str, project_dir: str, context_files: list[str]) -> str:
    parts = [base]
    root = Path(project_dir)
    for name in context_files:
        file_path = root / name
        if file_path.exists() and file_path.is_file():
            parts.append(f"\n# {name}\n{file_path.read_text(encoding='utf-8', errors='replace')}")
    return "\n".join(parts)
```

## Approval Flow

```python
from collections.abc import Callable

ApprovalCallback = Callable[[str, dict], bool]


def should_require_approval(tool_name: str, args: dict) -> bool:
    if tool_name in {"file_write", "file_edit"}:
        return True
    if tool_name == "shell":
        command = str(args.get("command", ""))
        risky_words = ("rm ", "sudo ", "chmod ", "chown ", "mkfs")
        return any(word in command for word in risky_words)
    return False


def execute_with_approval(tool_name: str, args: dict, approve: ApprovalCallback, execute) -> dict:
    if should_require_approval(tool_name, args) and not approve(tool_name, args):
        return {"approved": False, "error": "tool call rejected"}
    result = execute(tool_name, args)
    result["approved"] = True
    return result
```

## Structured Logging

```python
from datetime import datetime, timezone
from pathlib import Path
import json
import sys


def make_event(event_type: str, **data) -> dict:
    return {"type": event_type, "time": datetime.now(timezone.utc).isoformat(), **data}


def stderr_json_handler(event: dict) -> None:
    print(json.dumps(event, default=str), file=sys.stderr, flush=True)


def file_log_handler(path: str):
    log_path = Path(path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def handle(event: dict) -> None:
        with log_path.open("a", encoding="utf-8") as handle_file:
            handle_file.write(json.dumps(event, default=str) + "\n")

    return handle
```

## Output Schema Validation

```python
import json
from pathlib import Path
from jsonschema import Draft202012Validator


def load_schema(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_output(text: str, schema: dict) -> tuple[bool, str | None]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, str(exc)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda err: err.path)
    if errors:
        return False, errors[0].message
    return True, None
```

## Webhook Notifications

```python
import requests


def notify_webhook(url: str, payload: dict) -> None:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
```
