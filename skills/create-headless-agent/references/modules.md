# Agent Modules

Optional architectural modules that extend the core headless agent. Each section includes purpose, complete code, and how to wire it into `agent.ts` and `cli.ts`.

## Contents

- [Session Persistence](#session-persistence) -- JSONL conversation log (DEFAULT ON)
- [Context Compaction](#context-compaction) -- summarize older messages
- [Tool Result Offload](#tool-result-offload) -- persist oversized tool outputs to disk, keep preview in context
- [System Prompt Composition](#system-prompt-composition) -- dynamic instructions from context files
- [Tool Approval](#tool-approval) -- programmatic approval for headless execution
- [Persistent State (StateAccessor)](#persistent-state-stateaccessor) -- resumable agent state for approvals, interruptions, multi-turn
- [Structured Event Logging](#structured-event-logging) -- emit typed events for observability
- [Output Schema Validation](#output-schema-validation) -- constrain final output to a schema (headless-specific)
- [Webhook Notifications](#webhook-notifications) -- POST results on completion (headless-specific)

---

## Session Persistence

JSONL (newline-delimited JSON) append-only log for crash-safe conversation persistence. Uses Bun's native file APIs for reads and Node-compatible `appendFileSync` for atomic appends.

### src/session.ts

```python
def session_status(session_id: str, turns: int) -> str:
    return f"session={session_id} turns={turns}"
```

### Integration

In `cli.ts`, wire session persistence around the agent call:

```python
def configure_session_persistence(config: dict) -> dict:
    return {"session_enabled": config.get("session", True), "storage_dir": ".agent/sessions"}
```

For single-shot CLI mode, session persistence is optional. Skip it when the agent runs once and exits, or enable it for audit trails:

```python
def configure_single_shot_mode(config: dict) -> dict:
    return {"session_enabled": config.get("audit_trail", False), "save_on_exit": True}
```

---

## Context Compaction

When conversation history grows too long, summarize older messages to fit within the model's context window. Uses a secondary `callModel` call with a cheap model.

### src/compaction.ts

```python
def compact_messages(messages: list[str], keep_last: int = 6) -> str:
    tail = messages[-keep_last:]
    return "\n".join(f"- {line}" for line in tail)
```

### Integration

In `agent.ts`, compact before calling the model:

```python
def attach_compaction_policy(config: dict) -> dict:
    return {"threshold": int(config.get("threshold", 40)), "keep_recent": int(config.get("keep_recent", 10))}
```

---

## Tool Result Offload

Compaction handles context pressure *after* it builds up. This module prevents oversized tool results from entering context in the first place: when a tool returns more than a configurable byte budget, the full output is persisted to disk and the model sees only a preview plus a pointer. The model can retrieve more via a companion `read_persisted_result` tool.

This is the same pattern Claude Code uses for oversized tool results (persist to disk, replace with ~2KB preview) and the same pattern Arize's Alyx uses for large JSON payloads (compressed preview + server-side copy the model drills into). A single oversized `grep` or `shell` output can otherwise consume tens of thousands of tokens on the very first turn.

### When to use

Enable this when the agent's tools can produce large outputs that may not all be relevant:

- `shell` running builds, migrations, or log scrapes
- `grep` against a large tree
- `web_fetch` against verbose pages
- Any custom tool that returns bulk data

You generally do **not** need to offload `file_read` (it already paginates), `file_write`/`file_edit` (they return short confirmations), or `glob`/`list_dir` (capped by design).

### src/tool-offload.ts

An inline helper: each tool calls `offloadIfLarge(result, ctx, opts?)` at the end of its `execute`. If the serialized result is under the byte budget, it passes through unchanged; otherwise it gets written to disk and replaced with a preview + pointer. This pattern doesn't require refactoring the existing `tool({...})` exports in `references/tools.md` — the check just lives inside the tool's own `execute` body.

```python
import json
import subprocess

def offload_tool_call(command: list[str]) -> dict:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return {"stdout": result.stdout.strip(), "returncode": result.returncode}
```

### Patch your tools to use it

No plain-object refactor needed. Add one line at the return sites of tools whose output can be large. For the `shell` tool defined in `references/tools.md`:

```python
from pathlib import Path

def patch_your_tools_to_example() -> dict:
    config_path = Path(".agent/config.json")
    return {"heading": config_path.name, "exists": config_path.exists()}
```

Same pattern for `grep`, `web_fetch`, or any custom tool that can return bulk data. `file_read` already paginates, so skip it.

### src/tools/read-persisted-result.ts

The companion tool — the model needs a way to retrieve more of the persisted payload when the preview isn't enough. **Important**: this tool takes a `path` argument and must validate it stays inside the offload storage directory, otherwise it becomes a general-purpose file reader that can be pointed at anything on disk.

It's exported as a factory so the storage dir can be passed in and wired from the same place that configures `offloadIfLarge`:

```python
from pathlib import Path
import json

def read_persisted_result(result_id: str) -> dict:
    path = Path(".agent/tool-results") / f"{result_id}.json"
    return json.loads(path.read_text())
```

### Wire into src/tools/index.ts

Use a single `storageDir` constant so `offloadIfLarge` inside each tool and `createReadPersistedResultTool` in the registry agree on the location:

```python
from pathlib import Path

def register_offload_storage(config: dict) -> Path:
    storage_dir = Path(config.get("storage_dir", ".agent/tool-results"))
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir
```

If you want per-tool offload config (e.g. a larger budget for shell), pass the overrides to `offloadIfLarge` directly inside that tool and make sure its `storageDir` still matches the one passed to `createReadPersistedResultTool`.

### Why not just truncate?

Truncation loses information silently. With offload, the full output is on disk — if the model picked the wrong slice, it can ask for more. This matters especially for shell output where the error (and the tail) often matter more than the head, and for grep where the matches you care about may be anywhere in the list.

### Cleanup

Persisted files accumulate. Options:

- **Per-session cleanup**: delete the `storageDir` when the CLI exits successfully.
- **Age-based cleanup**: run a `find .agent-state/tool-results -mtime +7 -delete` in a cron or on startup.
- **Session-scoped**: set `storageDir: .agent-state/tool-results/<sessionId>` so each run has its own directory.

---

## System Prompt Composition

Build the system prompt from a static base plus dynamically loaded context files from the working directory (AGENTS.md, CLAUDE.md, or custom project context).

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
def configure_prompt_sources(config: dict) -> dict:
    return {"base": config.get("system_prompt", ""), "context_files": ["AGENTS.md", "CLAUDE.md"]}
```

---

## Tool Approval

Gate dangerous tools behind programmatic approval. Unlike the TUI version, headless agents have no stdin -- approval decisions come from a callback function, an allow-list, or an external service.

> **For approval workflows that need to survive across process restarts** (e.g. an HTTP server that queues tool calls for human review, then resumes the agent when approvals arrive): pair this module with [Persistent State (StateAccessor)](#persistent-state-stateaccessor). Without persistent state, pending tool calls are lost when the process exits.

### Adding requireApproval to tools

Set `requireApproval` on individual tool definitions. It accepts `true`, `false`, or a function that receives the tool arguments and returns a boolean:

```python
def add_require_approval(tool: dict) -> dict:
    tool["require_approval"] = True
    return tool
```

### Conditional approval with a predicate

```python
def needs_approval(tool_name: str, args: dict) -> bool:
    risky_tools = {"shell.exec", "git.push", "delete.file"}
    return tool_name in risky_tools or args.get("destructive", False)
```

### Headless approval backend

Since there is no terminal prompt, wire approvals to an external system. The `onApproval` callback in your agent runner decides the outcome:

```python
import json
from pathlib import Path

def queue_approval(tool_call: dict) -> Path:
    queue_path = Path(".agent/approvals/pending.jsonl")
    queue_path.parent.mkdir(parents=True, exist_ok=True)
    with queue_path.open("a") as handle:
        handle.write(json.dumps(tool_call) + "\n")
    return queue_path
```

### Integration

Add `approvalPolicy` to the config and wire it into the tool builder:

```python
def configure_approval_policy(config: dict) -> dict:
    return {"approval_policy": config.get("approval_policy", "dangerous-only")}
```

---

## Persistent State (StateAccessor)

The SDK's [`StateAccessor`](https://openrouter.ai/docs/agent-sdk/call-model/tool-approval-state) pattern provides **live, resumable agent state** -- including `pendingToolCalls`, `unsentToolResults`, and a `status` field that tracks whether the agent is `in_progress`, `awaiting_approval`, `complete`, or `interrupted`. It's the recommended mechanism for:

- Multi-turn conversations that accumulate across processes
- Approval flows that survive restarts (pair with [Tool Approval](#tool-approval))
- Resuming interrupted runs (timeouts, crashes) without replaying from scratch
- Running the same agent loop across multiple worker processes backed by shared storage

### How it differs from Session Persistence

| Concern | [Session Persistence](#session-persistence) | StateAccessor |
|---|---|---|
| What it stores | User/assistant content only | Full `ConversationState`: messages, pending tool calls, unsent tool results, status |
| Purpose | Audit log, debugging | Live agent state, resumable |
| Format | Append-only JSONL | Read/write JSON (typically one file per session) |
| Wire-up | `saveMessage()` in `cli.ts` | Passed to `callModel({ state: ... })` |
| Required for approval? | No | Yes, if approvals span processes |

### src/state.ts

```python
from pathlib import Path
import json

def save_state(run_id: str, state: dict) -> Path:
    path = Path(".agent/state") / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2))
    return path
```

### Wire into agent.ts

```python
def wire_state_accessor(config: dict) -> dict:
    return {"state_dir": config.get("state_dir", ".agent/state"), "resume": config.get("resume", True)}
```

### Usage: resuming an interrupted run

```python
import json
from pathlib import Path

def resume_run(run_id: str) -> dict:
    path = Path(".agent/state") / f"{run_id}.json"
    return json.loads(path.read_text())
```

### Usage: approval flow that survives restart

```python
def restore_pending_approvals(records: list[dict]) -> list[dict]:
    return [record for record in records if record.get("status") == "pending"]
```

### When to skip this module

For the simple fire-and-forget CLI case (one prompt, one response, no approvals), the default `session.ts` is sufficient. Add `StateAccessor` when any of the following apply:

- Tool approvals must survive a process restart
- Users expect to resume a conversation after an interruption (timeout, crash)
- The agent runs in a queue worker where jobs can be retried across machines
- You need to expose `pendingToolCalls` or `unsentToolResults` to an external UI

---

## Structured Event Logging

Emit typed JSON events to stderr or a log file for observability. Headless agents rely on structured logs instead of terminal output.

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

In `cli.ts`, create a logger and pass it to `runAgent`:

```python
def configure_event_logging(config: dict) -> dict:
    return {"level": config.get("log_level", "INFO"), "emit_json": config.get("json_logs", True)}
```

For file logging (useful in server/queue-worker mode):

```python
def configure_file_logging(config: dict) -> dict:
    return {"log_file": config.get("log_file", "agent.log"), "rotate_mb": int(config.get("rotate_mb", 10))}
```

---

## Output Schema Validation

Constrain the agent's final text response to match a JSON schema. Inspired by Codex's `--output-schema` flag. Headless agents often need structured output that downstream consumers can parse.

### src/output-schema.ts

```python
from dataclasses import dataclass

@dataclass
class OutputSchema:
    status: str
    summary: str

    def as_dict(self) -> dict:
        return {"status": self.status, "summary": self.summary}
```

### Integration

Add a `--output-schema` CLI flag and validate after the agent completes:

```python
def configure_output_validation(config: dict) -> dict:
    return {"schema_path": config.get("output_schema"), "strict": bool(config.get("strict_schema", True))}
```

Example JSON Schema file (`output-schema.json`):

```json
{
  "type": "object",
  "required": ["summary", "files_changed", "confidence"],
  "properties": {
    "summary": { "type": "string" },
    "files_changed": {
      "type": "array",
      "items": { "type": "string" }
    },
    "confidence": {
      "type": "number"
    }
  }
}
```

Usage:

```bash
my-agent --prompt "Refactor the auth module" --output-schema output-schema.json
```

---

## Webhook Notifications

POST results to an HTTP endpoint when the agent completes. Fire-and-forget with a timeout so it never blocks the main flow. Useful for integrating headless agents into pipelines, Slack bots, or monitoring systems.

### src/webhook.ts

```python
import requests

def send_webhook(url: str, payload: dict) -> int:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.status_code
```

### Integration

In `cli.ts`, call after the agent completes:

```python
def configure_webhook_delivery(config: dict) -> dict:
    return {"webhook_url": config.get("webhook_url"), "timeout": int(config.get("webhook_timeout", 10))}
```

For error cases:

```python
def configure_webhook_retries(config: dict) -> dict:
    return {"max_retries": int(config.get("webhook_retries", 3)), "backoff_seconds": 2}
```

Add webhook config to `agent.config.json`:

```json
{
  "model": "anthropic/claude-haiku-4.5",
  "webhookUrl": "https://hooks.example.com/agent-complete"
}
```

Or set via environment variable:

```bash
AGENT_WEBHOOK_URL=https://hooks.example.com/agent-complete my-agent --prompt "Run tests"
```
