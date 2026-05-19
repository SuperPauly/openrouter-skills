# Create Agent TUI

A skill for scaffolding a complete Python terminal agent. It generates a runnable project with streaming output, configurable tools, session persistence, input styles, loaders, and banner rendering.

![My Harness banner](sample/screenshots/banner.png)

## Quickstart

```bash
gh skill install OpenRouterTeam/skills create-agent-tui
```

Then ask your coding agent to build an agent TUI. The generated project uses Python modules under `src/` and calls OpenRouter through the Responses API.

## What it looks like

Every visible part of the terminal experience is configurable.

### Tool display styles

Choose how tool calls appear during agent execution. Set `display.toolDisplay` in your config or pass `--tool-display` at launch.

**Emoji**: per-call markers with tool name, arguments, and timing.

![Emoji tool display](sample/screenshots/tool-display-emoji.png)

**Grouped**: bold action labels with tree-branch output, with consecutive same-type calls merged.

![Grouped tool display](sample/screenshots/tool-display-grouped.png)

**Minimal**: aggregated one-line summaries, flushed when text resumes.

![Minimal tool display](sample/screenshots/tool-display-minimal.png)

A hidden mode suppresses tool output entirely.

### Input styles

| Style | Description |
|-------|-------------|
| `block` | Full-width background-colored input box with a prompt marker. |
| `bordered` | Horizontal frame lines above and below the input. |
| `plain` | Simple readline prompt with no raw terminal mode. |

![Block input style](sample/screenshots/input-style-block.png)
![Bordered input style](sample/screenshots/input-style-bordered.png)
![Plain input style](sample/screenshots/input-style-plain.png)

### Loader animations

| Style | Description |
|-------|-------------|
| `spinner` | Braille dot animation. |
| `gradient` | Scrolling color shimmer. |
| `minimal` | Trailing dots. |

![Spinner loader](sample/screenshots/loader-spinner.png)
![Gradient loader](sample/screenshots/loader-gradient.png)
![Minimal loader](sample/screenshots/loader-minimal.png)

### ASCII banner

Enable `showBanner` to display generated block-letter art on startup. The fallback banner shows the agent name and model in a bordered box.

## When to use this

Build a custom TUI when:

- You need project-specific local tools.
- You want control over model selection, costs, approvals, or stop behavior.
- You are shipping an agent experience inside your own product.
- You want a clear reference implementation for debugging agent loops.

## Customizable features

### Hosted OpenRouter tools

| Tool | Default | What it does |
|------|---------|-------------|
| Web search | on | Hosted real-time search. |
| Datetime | on | Hosted current date and time. |
| Image generation | off | Hosted image creation. |

### Local tools

| Tool | Default | Python implementation |
|------|---------|-------------|
| File read | on | `Path.read_text` with offset and limit. |
| File write | on | `Path.write_text` with parent creation. |
| File edit | on | Search and replace with diff output. |
| Glob/find | on | `Path.rglob` and ignore filters. |
| Grep/search | on | `rg` through `subprocess.run`, with Python fallback. |
| Directory list | on | `Path.iterdir` metadata. |
| Shell | on | `subprocess.run` with timeout. |
| Python REPL | off | Persistent Python process. |
| Sub-agent spawn | off | Delegate bounded work where supported. |
| Plan/todo | off | Track multi-step work. |
| Request user input | off | Ask structured questions. |
| Web fetch | off | Fetch and extract URL text. |
| View image | off | Read image bytes as base64. |
| Custom template | on | Domain-specific tool skeleton. |

### Harness modules

| Module | Default | What it does |
|--------|---------|-------------|
| Session persistence | on | JSONL append-only conversation log. |
| Context compaction | off | Summarize old messages when context grows. |
| System prompt composition | off | Build instructions from context files. |
| Tool permissions | off | Gate risky local tools behind approval. |
| Structured logging | off | Emit events for tool calls, API requests, and errors. |

## Generated project structure

```text
my-agent/
  pyproject.toml
  requirements.txt
  .env.example
  src/
    config.py
    agent.py
    cli.py
    session.py
    terminal_bg.py
    renderer.py
    loader.py
    banner.py
    commands.py
    tools/
      __init__.py
      file_read.py
      file_write.py
      file_edit.py
      glob_tool.py
      grep_tool.py
      list_dir.py
      shell.py
      custom.py
```

## Sample

A complete working TUI is in [`sample/`](sample/).

```bash
cd sample
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
OPENROUTER_API_KEY=your-key python3 -m src.cli
```

Customize at launch:

```bash
OPENROUTER_API_KEY=your-key python3 -m src.cli --banner "Acme Bot" \
  --model anthropic/claude-sonnet-4.6 --input bordered --tool-display emoji
```
