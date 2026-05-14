---
name: create-agent-tui
description: Scaffolds a complete agent TUI in Python using the OpenRouter Responses API — like create-react-app for terminal agents. Generates a customizable terminal interface with three input styles, four tool display modes, ASCII banners, streaming output, session persistence, and configurable tools. Use when building an agent, creating a TUI, scaffolding an agent project, or building a coding assistant.
---

# Create Agent TUI

Scaffolds a complete agent TUI in Python targeting OpenRouter. The generated project uses `requests` for the inner loop (model calls, tool execution, stop conditions) and provides the outer shell: a customizable terminal interface, configuration, session management, tool definitions, and an entry point.

Architecture draws from three production agent systems:
- **pi-mono/coding-agent** — three-layer separation, JSONL sessions, pluggable tool operations
- **Claude Code** — tool metadata (read-only, destructive, approval), system prompt composition
- **Codex CLI** — layered config, approval flow with session caching, structured logging

## Prerequisites

- Python 3.11+
- `OPENROUTER_API_KEY` from [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
- For full SDK reference, see the `openrouter-python-sdk` skill

---

## Decision Tree

| User wants to... | Action |
|---|---|
| Build a new agent from scratch | Present checklist below → follow Generation Workflow |
| Add tools to an existing harness | Read [references/tools.md](references/tools.md), present tool checklist only |
| Add a harness module | Read [references/modules.md](references/modules.md), generate the module |
| Add an API server entry point | Read [references/server-entry-points.md](references/server-entry-points.md) |

---

## Interactive Tool Checklist

Present this as a multi-select checklist. Items marked **ON** are pre-selected defaults.

### OpenRouter Server Tools (server-side, zero implementation)

| Tool | Type string | Default | Config |
|------|------------|---------|--------|
| Web Search | `openrouter:web_search` | ON | engine, max_results, domain filtering |
| Datetime | `openrouter:datetime` | ON | timezone |
| Image Generation | `openrouter:image_generation` | OFF | model, quality, size, format |

Server tools go in the `tools` array alongside user-defined tools. No client code needed — OpenRouter executes them.

### User-Defined Tools (client-side, generated into src/tools/)

| Tool | Default | Description |
|------|---------|-------------|
| File Read | ON | Read files with offset/limit, detect images |
| File Write | ON | Write/create files, auto-create directories |
| File Edit | ON | Search-and-replace with diff validation |
| Glob/Find | ON | File discovery by glob pattern |
| Grep/Search | ON | Content search by regex |
| Directory List | ON | List directory contents |
| Shell/Bash | ON | Execute commands with timeout and output capture |
| Python REPL | OFF | Persistent Python environment |
| Sub-agent Spawn | OFF | Delegate tasks to child agents |
| Plan/Todo | OFF | Track multi-step task progress |
| Request User Input | OFF | Structured multiple-choice questions |
| Web Fetch | OFF | Fetch and extract text from web pages |
| View Image | OFF | Read local images as base64 |
| Custom Tool Template | ON | Empty skeleton for domain-specific tools |

### Harness Modules (architectural components)

| Module | Default | Description |
|--------|---------|-------------|
| Session Persistence | ON | JSONL append-only conversation log |
| ASCII Logo Banner | OFF | Custom ASCII art banner on startup — ask for project name |
| Context Compaction | OFF | Summarize older messages when context is long |
| System Prompt Composition | OFF | Assemble instructions from static + dynamic context |
| Tool Permissions / Approval | OFF | Gate dangerous tools behind user confirmation |
| Structured Event Logging | OFF | Emit events for tool calls, API requests, errors |
| `@`-file References | OFF | `@filename` to attach file content to next message |
| `!` Shell Shortcut | OFF | `!command` to run shell and inject output into context |
| Multi-line Input | OFF | Shift+Enter for multi-line (requires raw terminal mode) |

### Slash Commands (user-facing REPL commands)

| Command | Default | Description |
|---------|---------|-------------|
| `/model` | ON | Switch model via OpenRouter API |
| `/new` | ON | Start a fresh conversation |
| `/help` | ON | List available commands |
| `/compact` | OFF | Manually trigger context compaction |
| `/session` | OFF | Show session metadata and token usage |
| `/export` | OFF | Save conversation as Markdown |

When slash commands are enabled, generate `src/commands.py` with a command registry. See [references/slash-commands.md](references/slash-commands.md) for specs.

### Visual Customization (present as single-select for each)

**Input style** — how the prompt looks. See [references/input-styles.md](references/input-styles.md):

| Style | Default | Description |
|-------|---------|-------------|
| `block` | ON | Full-width background box with `›` prompt, adapts to terminal theme |
| `bordered` | | Horizontal `─` lines above and below input |
| `plain` | | Simple `> ` readline prompt, no escape sequences |
| Other | | User describes what they want — implement a custom input style |

**Tool display** — how tool calls appear during execution. See [references/tool-display.md](references/tool-display.md):

| Style | Default | Description |
|-------|---------|-------------|
| `grouped` | ON | Bold action labels with tree-branch output |
| `emoji` | | Per-call `⚡`/`✓` markers with args and timing |
| `minimal` | | Aggregated one-liner summaries |
| `hidden` | | No tool output |
| Other | | User describes what they want — implement a custom display |

**Loader animation** — shown while waiting for model response. See [references/loader.md](references/loader.md):

| Style | Default | Description |
|-------|---------|-------------|
| `spinner` | ON | Braille dot spinner (⠋⠙⠹…) to the left of the text |
| `gradient` | | Scrolling color shimmer over the loader text |
| `minimal` | | Trailing dots (`Working···`) |
| Other | | User describes what they want — implement a custom animation |

Also ask for the **loader text** (default: `"Working"`).

---

## Generation Workflow

After getting checklist selections, follow this workflow:

```
- [ ] Generate pyproject.toml with dependencies
- [ ] Generate src/config.py (add show_banner field if ASCII Logo Banner is ON)
- [ ] Generate src/tools/__init__.py wiring selected tools + server tools
- [ ] Generate selected tool files in src/tools/ (see Tool Pattern below, specs in references/tools.md)
- [ ] Generate src/agent.py (core runner)
- [ ] Generate selected harness modules (specs in references/modules.md)
- [ ] Generate src/terminal_bg.py (adaptive input background — see references/tui.md)
- [ ] Generate input style functions in src/cli.py (block/bordered/plain — see references/input-styles.md)
- [ ] Generate src/renderer.py (tool display — see references/tool-display.md)
- [ ] Generate src/loader.py (loader animation — see references/loader.md)
- [ ] If slash commands selected: generate src/commands.py (see references/slash-commands.md)
- [ ] If ASCII Logo Banner is ON: generate src/banner.py (see ASCII Logo Banner section below)
- [ ] Generate src/cli.py entry point (or src/server.py — see references/server-entry-points.md)
- [ ] Generate .env.example with OPENROUTER_API_KEY=
- [ ] Verify: run python -m py_compile src/*.py to check syntax
```

---

## Tool Pattern

All user-defined tools follow this pattern. Here is one complete example — all other tools in [references/tools.md](references/tools.md) follow the same shape:

```python
import os

DEFAULT_LINE_LIMIT = 2000
MAX_LINE_CHARS = 2000

SCHEMA = {
    "type": "function",
    "name": "file_read",
    "description": "Read the contents of a file. Output is capped at 2000 lines by default (use offset/limit to paginate) and any line longer than 2000 characters is truncated. When the response is truncated, the hint field tells you how to continue.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "offset": {"type": "integer", "description": "Start reading from this line (1-indexed)"},
            "limit": {"type": "integer", "description": f"Maximum lines to return (default {DEFAULT_LINE_LIMIT})"},
        },
        "required": ["path"],
    },
}


def execute(args: dict) -> dict:
    path = args["path"]
    offset = args.get("offset")
    limit = args.get("limit", DEFAULT_LINE_LIMIT)
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().split("\n")
        start = (offset - 1) if offset else 0
        end = min(start + limit, len(lines))
        long_lines = 0
        slice_ = []
        for line in lines[start:end]:
            if len(line) <= MAX_LINE_CHARS:
                slice_.append(line)
            else:
                long_lines += 1
                slice_.append(line[:MAX_LINE_CHARS] + f"… [line truncated, {len(line) - MAX_LINE_CHARS} chars dropped]")
        tail_truncated = end < len(lines)
        truncated = tail_truncated or long_lines > 0
        result: dict = {"content": "\n".join(slice_), "total_lines": len(lines)}
        if truncated:
            hint_parts = [f"Showing lines {start + 1}-{end} of {len(lines)}."]
            if tail_truncated:
                hint_parts.append(f"Use offset={end + 1} to continue.")
            if long_lines:
                hint_parts.append(f"{long_lines} line(s) exceeded {MAX_LINE_CHARS} chars and were per-line truncated; use grep to fetch content from those lines.")
            result["truncated"] = True
            if tail_truncated:
                result["next_offset"] = end + 1
            result["hint"] = " ".join(hint_parts)
        return result
    except FileNotFoundError:
        return {"error": f"File not found: {path}"}
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": str(e)}
```

For specs of all other tools, see [references/tools.md](references/tools.md).

---

## Core Files

These files are always generated. The agent adapts them based on checklist selections.

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "<agent-name>"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["requests>=2.31"]

[project.scripts]
<agent-name> = "src.cli:main"

[tool.pytest.ini_options]
testpaths = ["test"]
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### src/config.py

```python
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DisplayConfig:
    tool_display: Literal["emoji", "grouped", "minimal", "hidden"] = "grouped"
    reasoning: bool = False
    input_style: Literal["block", "bordered", "plain"] = "block"


@dataclass
class AgentConfig:
    api_key: str = ""
    model: str = "anthropic/claude-opus-4.7"
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
    show_banner: bool = False
    display: DisplayConfig = field(default_factory=DisplayConfig)
    slash_commands: bool = True


def load_config(overrides: dict | None = None) -> AgentConfig:
    config = AgentConfig()
    config_path = Path("agent.config.pyon")
    if config_path.exists():
        file = json.loads(config_path.read_text())
        if "display" in file:
            display_data = file.pop("display")
            for k, v in display_data.items():
                if hasattr(config.display, k):
                    setattr(config.display, k, v)
        for k, v in file.items():
            if hasattr(config, k):
                setattr(config, k, v)
    if os.environ.get("OPENROUTER_API_KEY"):
        config.api_key = os.environ["OPENROUTER_API_KEY"]
    if os.environ.get("AGENT_MODEL"):
        config.model = os.environ["AGENT_MODEL"]
    if os.environ.get("AGENT_MAX_STEPS"):
        config.max_steps = int(os.environ["AGENT_MAX_STEPS"])
    if os.environ.get("AGENT_MAX_COST"):
        config.max_cost = float(os.environ["AGENT_MAX_COST"])
    for k, v in (overrides or {}).items():
        if hasattr(config, k):
            setattr(config, k, v)
    if not config.api_key:
        raise RuntimeError("OPENROUTER_API_KEY is required.")
    return config
```

### src/tools/__init__.py

Adapt imports based on checklist selections. This example includes all default-ON tools:
```python
from src.tools import file_read, file_write, file_edit, glob_find, grep_search, list_dir, shell

SERVER_TOOLS = [
    {"type": "openrouter:web_search"},
    {"type": "openrouter:datetime", "parameters": {"timezone": "UTC"}},
]

CLIENT_TOOLS = {
    "file_read": file_read,
    "file_write": file_write,
    "file_edit": file_edit,
    "glob": glob_find,
    "grep": grep_search,
    "list_dir": list_dir,
    "shell": shell,
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
from typing import Callable
from src.config import AgentConfig
from src.tools import ALL_TOOLS, execute_tool

BASE_URL = "https://openrouter.ai/api/v1"


def run_agent(
    config: AgentConfig,
    prompt: str,
    on_event: Callable[[dict], None] | None = None,
) -> dict:
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }
    system_prompt = config.system_prompt.replace("{cwd}", os.getcwd())
    input_items = [{"type": "message", "role": "user", "content": prompt}]
    previous_response_id = None
    accumulated_text = ""
    usage = None

    for _ in range(config.max_steps):
        payload: dict = {
            "model": config.model,
            "instructions": system_prompt,
            "tools": ALL_TOOLS,
            "input": input_items,
        }
        if previous_response_id:
            payload["previous_response_id"] = previous_response_id

        resp = requests.post(f"{BASE_URL}/responses", headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.pyon()

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

    return {"text": accumulated_text, "usage": usage}


def run_agent_with_retry(
    config: AgentConfig,
    prompt: str,
    on_event: Callable[[dict], None] | None = None,
    max_retries: int = 3,
) -> dict:
    for attempt in range(max_retries + 1):
        try:
            return run_agent(config, prompt, on_event)
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            retryable = status == 429 or (500 <= status < 600)
            if not retryable or attempt == max_retries:
                raise
            time.sleep(min(1.0 * (2 ** attempt), 30.0))
    raise RuntimeError("Unreachable")
```

### src/cli.py

Three input styles are supported: `block` (background box), `bordered` (horizontal lines), and `plain` (simple caret). See [references/input-styles.md](references/input-styles.md) for full implementations.

```python
import sys
import os
from src.config import load_config
from src.agent import run_agent_with_retry

DIM = "\x1b[2m"
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
CYAN = "\x1b[36m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
GRAY = "\x1b[90m"


def format_tokens(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def summarize_args(name: str, args: dict) -> str:
    key_map = {
        "shell": "command", "file_read": "path", "file_write": "path",
        "file_edit": "path", "glob": "pattern", "grep": "pattern", "web_search": "query",
    }
    key = key_map.get(name) or (list(args.keys())[0] if args else None)
    if not key or key not in args:
        return ""
    val = str(args[key])
    return f"{key}={val[:40] + '…' if len(val) > 40 else val}"


def main() -> None:
    config = load_config()
    width = min(os.get_terminal_size().columns if hasattr(os, "get_terminal_size") else 60, 60)
    line = GRAY + "─" * width + RESET
    print(f"\n{line}")
    print(f"  {BOLD}My Agent{RESET}  {DIM}v0.1.0{RESET}")
    print(f"  {DIM}model{RESET}  {CYAN}{config.model}{RESET}")
    print(f"{line}\n")

    try:
        while True:
            try:
                user_input = input(f"{GREEN}>{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input:
                continue
            if user_input.lower() == "exit":
                break

            print()
            streaming = [False]
            started = [False]

            def handle_event(event: dict) -> None:
                if not started[0]:
                    started[0] = True
                    print("\r\x1b[K", end="", flush=True)
                if event["type"] == "text":
                    streaming[0] = True
                    print(event["delta"], end="", flush=True)
                elif event["type"] == "tool_call":
                    if streaming[0]:
                        print()
                        streaming[0] = False
                    args_str = summarize_args(event["name"], event["args"])
                    print(f"  {YELLOW}⚡{RESET} {DIM}{event['name']}{' ' + args_str if args_str else ''}{RESET}")
                elif event["type"] == "tool_result":
                    print(f"  {GREEN}✓{RESET} {DIM}{event['name']}{RESET}")
                    started[0] = False

            try:
                result = run_agent_with_retry(config, user_input, handle_event)
                if streaming[0]:
                    print(RESET, end="")
                in_t = (result.get("usage") or {}).get("input_tokens", 0)
                out_t = (result.get("usage") or {}).get("output_tokens", 0)
                print(f"\n{GRAY}  {format_tokens(in_t)} in · {format_tokens(out_t)} out{RESET}\n")
            except Exception as e:
                if streaming[0]:
                    print(RESET, end="")
                print(f"\n{YELLOW}  Error: {e}{RESET}\n")
    except Exception as e:
        print(f"Fatal: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## ASCII Logo Banner

When `ASCII Logo Banner` is selected, ask the user for their project name, then generate `src/banner.py` with ASCII art of that name. Use a block-letter style with the `█` character for the art. The banner should fit in a 60-column terminal.

### src/banner.py

Generate ASCII art for the user's project name. Example for a project called "ACME":

```python
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
CYAN = "\x1b[36m"

LOGO = """
   █████╗  ██████╗███╗   ███╗███████╗
  ██╔══██╗██╔════╝████╗ ████║██╔════╝
  ███████║██║     ██╔████╔██║█████╗
  ██╔══██║██║     ██║╚██╔╝██║██╔══╝
  ██║  ██║╚██████╗██║ ╚═╝ ██║███████╗
  ╚═╝  ╚═╝ ╚═════╝╚═╝     ╚═╝╚══════╝"""


def print_banner(model: str) -> None:
    print(CYAN + BOLD + LOGO + RESET)
    print(f"  {DIM}model  {RESET}{model}\n")
```

Adapt the ASCII art to the user's actual project name. Keep it to one or two short words that fit in 60 columns.

### Wire into src/cli.py

Add at the top of `main()`, before the text banner, when `show_banner` is selected:

```python
from src.banner import print_banner

# In main(), when show_banner is True:
if config.show_banner:
    print_banner(config.model)
```

Add `show_banner: bool` to `AgentConfig` (default `False`). Enable via `agent.config.json` or `load_config({"show_banner": True})`.

---

## Reference Files

For content beyond the core files:

- **[references/tools.md](references/tools.md)** — Specs for all user-defined tools: file-read, file-write, file-edit, glob, grep, list-dir, shell, js-repl, sub-agent, plan, request-input, web-fetch, view-image, custom template
- **[references/modules.md](references/modules.md)** — Harness modules: session persistence, context compaction, system prompt composition, tool approval, structured logging
- **[references/tui.md](references/tui.md)** — Terminal background detection, adaptive input background
- **[references/tool-display.md](references/tool-display.md)** — Tool display styles: emoji, grouped, minimal; TuiRenderer class, per-tool colors, formatters
- **[references/input-styles.md](references/input-styles.md)** — Input styles: block (background box), bordered (horizontal lines), plain (simple caret)
- **[references/loader.md](references/loader.md)** — Loader animations: gradient (scrolling shimmer), spinner (braille dots), minimal (trailing dots)
- **[references/slash-commands.md](references/slash-commands.md)** — Slash command registry: /model, /new, /help, /compact, /session, /export
- **[references/system-prompt.md](references/system-prompt.md)** — Default system prompt, buildSystemPrompt(), customization guide
- **[references/server-entry-points.md](references/server-entry-points.md)** — Flask API server entry point with SSE streaming, plus extension points (MCP, WebSocket, dynamic models)
