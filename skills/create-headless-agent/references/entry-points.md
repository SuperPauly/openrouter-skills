# Python Entry Points

The generated headless project can expose a CLI, a library function, an API service, and an MCP service. All entry points call the same `run_agent_with_retry` function so retries, sessions, tools, and output validation stay consistent.

## CLI

The default CLI lives at `src/cli.py` and runs with `python3 -m src.cli`.

```python
from __future__ import annotations

import argparse
import json
import sys

from .agent import run_agent_with_retry
from .config import load_config
from .session import new_session_path, save_message


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="my-agent")
    parser.add_argument("prompt", nargs="*")
    parser.add_argument("--prompt", "-p", dest="prompt_option")
    parser.add_argument("--model", "-m")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-session", action="store_true")
    parser.add_argument("--output-schema")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    prompt = args.prompt_option or " ".join(args.prompt).strip() or sys.stdin.read().strip()
    if not prompt:
        print("Prompt required", file=sys.stderr)
        return 1

    config = load_config(model=args.model)
    session_path = None if args.no_session else new_session_path(config.session_dir)
    if session_path:
        save_message(session_path, {"role": "user", "content": prompt})

    def on_event(event: dict) -> None:
        if args.json:
            print(json.dumps(event, default=str), flush=True)
        elif not args.quiet and event.get("type") == "tool_start":
            print(f"tool: {event['name']}", file=sys.stderr)

    result = run_agent_with_retry(config, prompt, on_event=on_event)
    if session_path:
        save_message(session_path, {"role": "assistant", "content": result.text})

    print(result.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### CLI examples

```bash
OPENROUTER_API_KEY=your-key python3 -m src.cli --prompt "List all Python files"
OPENROUTER_API_KEY=your-key python3 -m src.cli "What is 2 plus 2?"
echo "Summarize this file" | OPENROUTER_API_KEY=your-key python3 -m src.cli
OPENROUTER_API_KEY=your-key python3 -m src.cli --json --prompt "Search for TODO comments"
OPENROUTER_API_KEY=your-key python3 -m src.cli --quiet --prompt "Fix the linting errors"
OPENROUTER_API_KEY=your-key python3 -m src.cli -m anthropic/claude-sonnet-4 -p "Review this code"
OPENROUTER_API_KEY=your-key python3 -m src.cli --output-schema schema.json -p "Extract entities as JSON"
```

## Library Module

```python
from src.agent import run_agent_with_retry
from src.config import load_config

config = load_config()
result = run_agent_with_retry(config, "Summarize README.md")
print(result.text)
```

## API Service

Use FastAPI when the agent needs an HTTP surface.

```python
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from src.agent import run_agent_with_retry, stream_agent_events
from src.config import load_config

app = FastAPI()
config = load_config()

class AgentRequest(BaseModel):
    prompt: str
    model: str | None = None

@app.post("/agent")
def run_agent(request: AgentRequest, authorization: str | None = Header(default=None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    local_config = config.model_copy(update={"model": request.model or config.model})
    result = run_agent_with_retry(local_config, request.prompt)
    return {"text": result.text, "usage": result.usage}

@app.post("/agent/stream")
def stream_agent(request: AgentRequest):
    local_config = config.model_copy(update={"model": request.model or config.model})
    return StreamingResponse(stream_agent_events(local_config, request.prompt), media_type="text/event-stream")
```

Run it with:

```bash
pip install fastapi uvicorn
OPENROUTER_API_KEY=your-key uvicorn src.server:app --host 0.0.0.0 --port 8000
```

## MCP Service

Expose the agent through a Python MCP server when another agent should call it as a tool.

```python
from mcp.server.fastmcp import FastMCP

from src.agent import run_agent_with_retry
from src.config import load_config

mcp = FastMCP("my-agent")
config = load_config()

def ask_agent(prompt: str) -> str:
    """Run the OpenRouter agent on a prompt."""
    return run_agent_with_retry(config, prompt).text

mcp.add_tool(ask_agent)

if __name__ == "__main__":
    mcp.run()
```

MCP client configuration:

```json
{
  "mcpServers": {
    "my-agent": {
      "command": "python3",
      "args": ["-m", "src.mcp_server"]
    }
  }
}
```
