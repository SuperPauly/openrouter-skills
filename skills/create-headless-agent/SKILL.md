---
name: create-headless-agent
description: Scaffolds a headless agent in Python using the OpenRouter Responses API — for CLI tools, API servers, queue workers, and pipelines. No terminal UI. Use when building a headless agent, programmatic agent, CLI tool that uses AI, batch agent, pipeline agent, API agent, agent without a UI, or agent service.
---

# Create Headless Agent

Scaffolds a headless agent in Python targeting OpenRouter. The generated project uses the OpenRouter Responses API for the inner loop (model calls, tool execution, stop conditions) and provides a clean programmatic shell: configuration, session management, tool definitions, and one or more entry points (CLI, HTTP server, or library import). No terminal UI, no readline, no ANSI — just input in, result out.

## Prerequisites

- Python 3.11+
- `OPENROUTER_API_KEY` from [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
- For API reference, see the `openrouter-python-sdk` skill

---

## Decision Tree

| User wants to... | Action |
|---|---|
| Build a new headless agent | Present checklist below, follow Generation Workflow |
| Add tools to an existing agent | Read [references/tools.md](references/tools.md), present tool checklist only |
| Add a module | Read [references/modules.md](references/modules.md), generate the module |
| Add an entry point | Read [references/entry-points.md](references/entry-points.md), generate it |

---

## Interactive Feature Checklist

Present this as a multi-select checklist. Items marked **ON** are pre-selected defaults.

### Entry Points (pick one or more)

| Entry Point | Default | Description |
|-------------|---------|-------------|
| CLI | ON | args/stdin to agent to stdout, `--output json` for NDJSON |
| Library module | ON | `from src.agent import run_agent` |
| HTTP server | OFF | `http.server.HTTPServer` with SSE streaming |
| MCP server | OFF | Expose as MCP tool via stdio |

### OpenRouter Server Tools (server-side, zero implementation)

| Tool | Type string | Default |
|------|------------|---------|
| Web Search | `openrouter:web_search` | ON |
| Web Fetch | `openrouter:web_fetch` | ON |
| Datetime | `openrouter:datetime` | ON |
| Image Generation | `openrouter:image_generation` | OFF |

Server tools go in the `tools` array alongside user-defined tools. No client code needed — OpenRouter executes them. Docs: [openrouter.ai/docs/guides/features/server-tools](https://openrouter.ai/docs/guides/features/server-tools/overview).

### User-Defined Tools (client-side, generated into src/tools/)

| Tool | Default | Description |
|------|---------|-------------|
| File Read | ON | Read files with offset/limit |
| File Write | ON | Write/create files, auto-create directories |
| File Edit | ON | Search-and-replace with diff validation |
| Glob/Find | ON | File discovery by glob pattern |
| Grep/Search | ON | Content search by regex |
| Directory List | ON | List directory contents |
| Shell/Bash | ON | Execute commands with timeout and output capture |
| Custom Tool Template | ON | Empty skeleton for domain-specific tools |
| Python REPL | OFF | Persistent Python environment |
| Sub-agent Spawn | OFF | Delegate tasks to child agents |
| View Image | OFF | Read local images as base64 |

### Agent Modules (architectural components)

| Module | Default | Description |
|--------|---------|-------------|
| Session Persistence | ON | JSONL conversation log, `--no-session` to disable |
| Retry with Backoff | ON | Built into agent.py |
| Context Compaction | OFF | Summarize when context is long |
| Tool Result Offload | OFF | Persist oversized tool outputs to disk, keep preview in context |
| System Prompt Composition | OFF | Dynamic instructions from context files |
| Tool Approval Flow | OFF | Programmatic approve/reject |
| Structured Event Logging | OFF | JSON events to stderr |
| Output Schema Validation | OFF | JSON Schema constraining response |
| Webhook Notifications | OFF | POST on completion |

### CLI Output Mode (single-select, if CLI entry point is ON)

| Mode | Default | Description |
|------|---------|-------------|
| Text | ON | Final response text to stdout |
| JSON | OFF | NDJSON event stream |
| Quiet | OFF | Exit code only |

---

## Generation Workflow

Before generating, **ask the user what to name their agent**. This name is used as:
- the `"name"` field in `pyproject.toml`
- the `[project.scripts]` entry (so `pip install -e .` makes it a globally-invokable CLI)
- the project directory name (if creating a new directory)

Suggested question: *"What would you like to call your agent? (short snake_case or kebab-case, e.g. `research-bot` or `docs-helper`)"*. Default to `my-agent` if the user has no preference. Use the chosen name everywhere the workflow below shows `<agent-name>`.

After getting the name and checklist selections, follow this workflow:

```
- [ ] Generate pyproject.toml with name=<agent-name> and scripts entry
- [ ] Generate requirements.txt (requests, jsonschema, pytest)
- [ ] Generate src/__init__.py
- [ ] Generate src/config.py
- [ ] Generate src/tools/__init__.py wiring selected tools
- [ ] Generate selected tool files in src/tools/ (specs in references/tools.md)
- [ ] Generate src/agent.py (core runner via Responses API)
- [ ] If Session Persistence ON: generate src/session.py (spec in references/modules.md)
- [ ] Generate selected modules (specs in references/modules.md)
- [ ] Generate src/cli.py entry point (spec in references/entry-points.md)
- [ ] If HTTP server selected: generate src/server.py (spec in references/entry-points.md)
- [ ] Generate .env.example
- [ ] Generate test/test_retry.py and test/test_output_schema.py
- [ ] Run `pip install -e .` to install in development mode
- [ ] Verify: run `python -m py_compile src/cli.py`
- [ ] Tell the user they can now invoke their agent with `python src/cli.py "<prompt>"`
- [ ] Or install globally with `pip install -e .` and run `<agent-name> "<prompt>"`
```

After generation, the user can run their agent:

```bash
python src/cli.py "What's in this repo?"
echo "Summarize README.md" | python src/cli.py
python src/cli.py --output json "List all TODOs" | python -m json.tool
```

To later rename the agent, update the `name` and `[project.scripts]` entries in `pyproject.toml`, then re-run `pip install -e .`.

---

## Tool Pattern

All user-defined tools follow this pattern. Here is one complete example — all other tools in [references/tools.md](references/tools.md) follow the same shape:

```python
DEFAULT_LINE_LIMIT = 2000
MAX_LINE_CHARS = 2000

SCHEMA = {
    "name": "file_read",
    "description": (
        "Read the contents of a file. Output is capped at 2000 lines by default "
        "(use offset/limit to paginate) and any line longer than 2000 characters is truncated. "
        "When the response is truncated, the hint field tells you how to continue."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "offset": {"type": "number", "description": "Start reading from this line (1-indexed)"},
            "limit": {"type": "number", "description": f"Maximum lines to return (default {DEFAULT_LINE_LIMIT})"},
        },
        "required": ["path"],
    },
}


def execute(args: dict) -> dict:
    path = args.get("path", "")
    offset = int(args.get("offset") or 1)
    limit = int(args.get("limit") or DEFAULT_LINE_LIMIT)
    from pathlib import Path
    p = Path(path)
    if not p.exists():
        return {"error": f"File not found: {path}"}
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except OSError as e:
        return {"error": str(e)}
    lines = text.splitlines()
    total = len(lines)
    start = offset - 1
    end = start + limit
    sliced = lines[start:end]
    long_lines = 0
    processed = []
    for line in sliced:
        if len(line) > MAX_LINE_CHARS:
            dropped = len(line) - MAX_LINE_CHARS
            processed.append(line[:MAX_LINE_CHARS] + f"… [line truncated, {dropped} chars dropped]")
            long_lines += 1
        else:
            processed.append(line)
    tail_truncated = end < total
    truncated = tail_truncated or long_lines > 0
    result = {"content": "\n".join(processed), "totalLines": total}
    if truncated:
        result["truncated"] = True
        hint_parts = [f"Showing lines {start + 1}-{start + len(sliced)} of {total}."]
        if tail_truncated:
            hint_parts.append(f"Use offset={start + len(sliced) + 1} to continue.")
            result["nextOffset"] = start + len(sliced) + 1
        if long_lines > 0:
            hint_parts.append(
                f"{long_lines} line(s) exceeded {MAX_LINE_CHARS} chars and were per-line truncated; "
                "use grep to fetch content from those lines."
            )
        result["hint"] = " ".join(hint_parts)
    return result
```

For specs of all other tools, see [references/tools.md](references/tools.md).

---

## Core Files

These files are always generated. The agent adapts them based on checklist selections.

### pyproject.toml

Initialize the project. Replace `<agent-name>` with the name the user chose:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "<agent-name>"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests>=2.31", "jsonschema>=4.0"]

[project.scripts]
<agent-name> = "src.cli:main"

[tool.pytest.ini_options]
testpaths = ["test"]
```

### requirements.txt

```
requests>=2.31
jsonschema>=4.0
pytest>=8.0
```

### src/config.py

```python
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal


def _positive_number(name: str, raw: str) -> float:
    n = float(raw)
    if n <= 0:
        raise ValueError(f"{name} must be a positive number, got: {raw!r}")
    return n


@dataclass
class AgentConfig:
    api_key: str = ""
    model: str = "anthropic/claude-sonnet-4.6"
    name: str = "My Agent"
    system_prompt: str = "\n".join([
        "You are a coding assistant with access to tools for reading, writing, editing, and searching files, and running shell commands.",
        "",
        "Current working directory: {cwd}",
        "",
        "Guidelines:",
        "- Use your tools proactively. Explore the codebase to find answers instead of asking the user.",
        "- Keep working until the task is fully resolved before responding.",
        "- Do not guess or make up information — use your tools to verify.",
        "- Be concise and direct.",
        "- Show file paths clearly when working with files.",
        "- Prefer grep and glob tools over shell commands for file search.",
        "- When editing code, make minimal targeted changes consistent with the existing style.",
    ])
    max_steps: int = 20
    max_cost: float = 1.0
    session_dir: str = ".sessions"
    session_enabled: bool = True
    output_mode: Literal["text", "json", "quiet"] = "text"


def load_config(overrides: dict | None = None, skip_api_key: bool = False) -> AgentConfig:
    config = AgentConfig()
    config_path = Path("agent.config.json")
    if config_path.exists():
        file = json.loads(config_path.read_text())
        for k, v in file.items():
            if hasattr(config, k):
                setattr(config, k, v)
    if os.environ.get("OPENROUTER_API_KEY"):
        config.api_key = os.environ["OPENROUTER_API_KEY"]
    if os.environ.get("AGENT_MODEL"):
        config.model = os.environ["AGENT_MODEL"]
    if os.environ.get("AGENT_MAX_STEPS"):
        config.max_steps = int(_positive_number("AGENT_MAX_STEPS", os.environ["AGENT_MAX_STEPS"]))
    if os.environ.get("AGENT_MAX_COST"):
        config.max_cost = _positive_number("AGENT_MAX_COST", os.environ["AGENT_MAX_COST"])
    for k, v in (overrides or {}).items():
        if hasattr(config, k):
            setattr(config, k, v)
    if not config.api_key and not skip_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required.")
    return config
```

### src/tools/__init__.py

Adapt imports based on checklist selections. This example includes all default-ON tools:

```python
from src.tools import file_read, file_write, file_edit, glob_find, grep_search, list_dir, shell, custom

# Server tools — executed by OpenRouter, no client implementation needed
SERVER_TOOLS = [
    {"type": "openrouter:web_search"},
    {"type": "openrouter:web_fetch"},
    {"type": "openrouter:datetime", "parameters": {"timezone": "UTC"}},
]

# User-defined tools — executed client-side
CLIENT_TOOLS = {
    "file_read": file_read,
    "file_write": file_write,
    "file_edit": file_edit,
    "glob": glob_find,
    "grep": grep_search,
    "list_dir": list_dir,
    "shell": shell,
    "custom": custom,
}

TOOL_SCHEMAS = [mod.SCHEMA for mod in CLIENT_TOOLS.values()]
ALL_TOOLS = TOOL_SCHEMAS + SERVER_TOOLS


def execute_tool(name: str, args: dict) -> dict:
    mod = CLIENT_TOOLS.get(name)
    if mod is None:
        return {"error": f"Unknown tool: {name}"}
    return mod.execute(args)
```

### src/agent.py

```python
import json
import time
import os
import requests
from typing import Callable, Iterator
from src.config import AgentConfig
from src.tools import ALL_TOOLS, execute_tool

BASE_URL = "https://openrouter.ai/api/v1"


def run_agent(
    config: AgentConfig,
    prompt: str,
    on_event: Callable[[dict], None] | None = None,
) -> dict:
    started_at = time.time()
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    system_prompt = config.system_prompt.replace("{cwd}", os.getcwd())
    input_items = [{"type": "message", "role": "user", "content": prompt}]
    previous_response_id = None
    accumulated_text = ""
    usage = None

    for step in range(config.max_steps):
        payload: dict = {
            "model": config.model,
            "instructions": system_prompt,
            "tools": ALL_TOOLS,
        }
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id
            payload["input"] = input_items
        else:
            payload["input"] = input_items

        resp = requests.post(f"{BASE_URL}/responses", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()

        previous_response_id = data.get("id")
        usage = data.get("usage")
        output = data.get("output", [])

        tool_calls = []
        for item in output:
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        delta = part.get("text", "")
                        accumulated_text += delta
                        if on_event:
                            on_event({"type": "text", "delta": delta})
            elif item.get("type") == "function_call":
                tool_calls.append(item)
                if on_event:
                    args = json.loads(item.get("arguments", "{}"))
                    on_event({"type": "tool_call", "name": item["name"], "call_id": item["call_id"], "args": args})

        if not tool_calls:
            break

        input_items = []
        for tc in tool_calls:
            args = json.loads(tc.get("arguments", "{}"))
            result = execute_tool(tc["name"], args)
            output_str = json.dumps(result) if not isinstance(result, str) else result
            if on_event:
                on_event({"type": "tool_result", "name": tc["name"], "call_id": tc["call_id"],
                          "output": output_str[:200] + "..." if len(output_str) > 200 else output_str})
            input_items.append({
                "type": "function_call_output",
                "call_id": tc["call_id"],
                "output": output_str,
            })

    duration_ms = int((time.time() - started_at) * 1000)
    if on_event:
        on_event({"type": "done", "usage": usage, "duration_ms": duration_ms})
    return {"text": accumulated_text, "usage": usage, "duration_ms": duration_ms}


def run_agent_with_retry(
    config: AgentConfig,
    prompt: str,
    on_event: Callable[[dict], None] | None = None,
    max_retries: int = 3,
) -> dict:
    """Retry on 429/5xx — but ONLY if no tool calls have been executed yet."""
    for attempt in range(max_retries + 1):
        tool_calls_made = 0

        def wrapped_on_event(event: dict) -> None:
            nonlocal tool_calls_made
            if event.get("type") == "tool_call":
                tool_calls_made += 1
            if on_event:
                on_event(event)

        try:
            return run_agent(config, prompt, wrapped_on_event)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            retryable = status == 429 or (500 <= status < 600)
            if not retryable or attempt == max_retries or tool_calls_made > 0:
                raise
            time.sleep(min(1.0 * (2 ** attempt), 30.0))
    raise RuntimeError("Unreachable")
```

### src/cli.py

Headless CLI entry point — parses args, reads stdin, dispatches to the agent, and exits. See [references/entry-points.md](references/entry-points.md) for the complete implementation.

```python
import argparse
import sys
from src.config import load_config
from src.agent import run_agent_with_retry


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the agent")
    parser.add_argument("prompt", nargs="?", help="Prompt text")
    parser.add_argument("-p", "--prompt-flag", dest="prompt_flag")
    parser.add_argument("-o", "--output", choices=["text", "json", "quiet"], default="text")
    parser.add_argument("--no-session", action="store_true")
    parser.add_argument("-m", "--model")
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--max-cost", type=float)
    args = parser.parse_args()

    prompt = args.prompt or args.prompt_flag
    if not prompt and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()
    if not prompt:
        parser.print_help()
        sys.exit(1)

    overrides = {}
    if args.model:
        overrides["model"] = args.model
    if args.max_steps:
        overrides["max_steps"] = args.max_steps
    if args.max_cost:
        overrides["max_cost"] = args.max_cost
    if args.no_session:
        overrides["session_enabled"] = False

    config = load_config(overrides)

    try:
        result = run_agent_with_retry(config, prompt)
        if args.output != "quiet":
            print(result["text"])
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

See [references/entry-points.md](references/entry-points.md) for the complete `src/cli.py` and `src/server.py` implementations.

---

## Reference Files

For content beyond the core files:

- **[references/tools.md](references/tools.md)** -- Specs for all user-defined tools: file-read, file-write, file-edit, glob, grep, list-dir, shell, web-fetch, python-repl, sub-agent, view-image, custom template
- **[references/modules.md](references/modules.md)** -- Agent modules: session persistence, context compaction, system prompt composition, tool approval, structured logging, output schema validation, webhook notifications
- **[references/entry-points.md](references/entry-points.md)** -- Entry point specs: CLI (full implementation), HTTP server with SSE
