# TUI Screenshot Test Notes

The sample screenshots are generated from Python demo scripts that exercise the renderer, loader, and input style functions in a real terminal session.

## Setup

```bash
cd skills/create-agent-tui/sample
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## Suggested Flow

1. Start a local terminal recorder or browser-backed pseudo terminal.
2. Run a Python demo script for each renderer style.
3. Capture the browser viewport as PNG.
4. Compare the images against `sample/screenshots/`.

## Demo Scripts

Recommended names:

```text
screenshot_demos.py
  demo_tools.py
  demo_input.py
  demo_loader.py
```

Each script should import from `src.renderer`, `src.loader`, or `src.cli` and render a deterministic sample. Keep network calls out of screenshot tests.

## Manual Smoke Test

```bash
OPENROUTER_API_KEY=your-key python3 -m src.cli --input bordered --tool-display grouped
```

Verify:

- The banner fits within the terminal width.
- The prompt does not overlap prior output.
- Tool rows appear once and clear before model text resumes.
- Loader output is removed when the response starts.
