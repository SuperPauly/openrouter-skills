# Create Headless Agent

A skill for scaffolding a headless Python agent. It provides a CLI, optional API service, session storage, retry handling, structured output validation, and local tools without a terminal UI.

## Quickstart

```bash
gh skill install OpenRouterTeam/skills create-headless-agent
```

Then ask your coding agent to create a headless OpenRouter agent. The generated project is Python-first and uses `requests` for low-level Responses API calls.

## When to use this

Use `create-headless-agent` when:

- You need a CLI tool that accepts a prompt and writes a response.
- You are wrapping an agent in an API service or queue worker.
- You want a library entry point that exposes `run_agent`.
- You need deterministic logging, sessions, retries, or output schema checks.
- You do not need terminal rendering or interactive input styles.

Use [`create-agent-tui`](../create-agent-tui/) when you want a full interactive terminal UI.

## Customizable features

### Entry points

| Entry point | Default | Description |
|---|---|---|
| CLI | on | `python -m src.cli "prompt"` with text, JSON, or quiet output. |
| Library module | on | Import `run_agent` from `src.agent`. |
| API service | off | Add a Python HTTP endpoint with streaming. |
| MCP service | off | Expose the agent as a Python MCP tool. |

### Server tools

| Tool | Default | What it does |
|---|---|---|
| Web search | on | Uses OpenRouter hosted web search. |
| Web fetch | on | Uses OpenRouter hosted page fetch. |
| Datetime | on | Uses OpenRouter hosted date and time. |
| Image generation | off | Adds OpenRouter image generation. |

### Local tools

| Tool | Default | Python implementation |
|---|---|---|
| File read | on | `pathlib.Path.read_text` with offset and limit handling. |
| File write | on | `Path.parent.mkdir` plus `Path.write_text`. |
| File edit | on | Search and replace with unified diff output. |
| Glob/find | on | `pathlib.Path.rglob` with ignore filtering. |
| Grep/search | on | `subprocess.run` for `rg`, with a Python fallback. |
| Directory list | on | `Path.iterdir` with metadata. |
| Shell | on | `subprocess.run` with timeout. |
| Custom template | on | A small Python function ready for domain logic. |
| Python REPL | off | Persistent Python process for exploratory execution. |
| Sub-agent spawn | off | Delegate bounded work to child agents where supported. |
| View image | off | Read local image bytes and return base64 data. |

### Modules

| Module | Default | What it does |
|---|---|---|
| Session persistence | on | JSONL append-only conversation log. |
| Retry with backoff | on | Retries 429 and 5xx responses before local side effects run. |
| Context compaction | off | Summarizes old messages when context grows. |
| System prompt composition | off | Builds instructions from static and dynamic context files. |
| Tool approval flow | off | Gates risky local tools behind an approval callback. |
| Structured event logging | off | Emits JSON events to stderr or a file. |
| Output schema validation | off | Checks final output against JSON Schema. |
| Webhook notifications | off | Posts completion status to a URL. |

## Generated project structure

```text
my-agent/
  pyproject.toml            Console script and project metadata
  requirements.txt          requests and optional validation dependencies
  .env.example              OPENROUTER_API_KEY=
  agent.config.json         Default model, tools, and limits
  src/
    config.py               Layered config from defaults, file, env, and args
    agent.py                Core runner with retries and tool loop
    cli.py                  CLI entry point
    session.py              JSONL conversation persistence
    tools/
      __init__.py           Tool registry and server tool declarations
      file_read.py          Read files with offset and limit
      file_write.py         Write files and create parent directories
      file_edit.py          Search and replace with diff
      glob_tool.py          Find files by pattern
      grep_tool.py          Search file contents by regex
      list_dir.py           List directory entries
      shell.py              Execute commands through subprocess
      custom.py             Domain-specific tool skeleton
  test/
    test_config.py          Config behavior
    test_retry.py           Retry safety
    test_output_schema.py   Output validation
```

Hosted OpenRouter tools are declared in `src/tools/__init__.py`; local tools are plain Python functions.

## Sample

A complete working agent is in [`sample/`](sample/).

```bash
cd sample
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
OPENROUTER_API_KEY=your-key python3 -m src.cli "List all Python files"
```

Install the console script during development:

```bash
pip install -e .
OPENROUTER_API_KEY=your-key my-agent "Summarize README.md"
```

Other usage:

```bash
echo "Summarize README.md" | OPENROUTER_API_KEY=your-key python3 -m src.cli
OPENROUTER_API_KEY=your-key python3 -m src.cli --json "Search for TODO comments"
OPENROUTER_API_KEY=your-key python3 -m src.cli -m anthropic/claude-sonnet-4.6 -p "Review this code"
```

## Highlighted features

### Safe retry on 429 and 5xx

`run_agent_with_retry` retries transient OpenRouter errors only before local tools have executed. After a mutating tool has run, replaying from the original prompt could repeat side effects, so the runner raises the error immediately.

### Structured output

Validate a final response against JSON Schema:

```bash
cat > report.schema.json <<'EOF'
{
  "type": "object",
  "properties": {
    "summary": { "type": "string" },
    "count": { "type": "integer", "minimum": 0 }
  },
  "required": ["summary", "count"],
  "additionalProperties": false
}
EOF

OPENROUTER_API_KEY=your-key python3 -m src.cli --output-schema report.schema.json \
  "Analyze README.md and return a JSON report with summary and count fields"
```

Exit codes:

- `0`: agent succeeded and output matched the schema.
- `1`: agent or API error.
- `2`: output failed schema validation.

## Environment

Requires `OPENROUTER_API_KEY`. Get one at [openrouter.ai/keys](https://openrouter.ai/keys).
