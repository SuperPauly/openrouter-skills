# Python Tool Display Renderer

The renderer turns agent events into terminal output. Keep rendering separate from tool execution so tests can assert events without ANSI output.

## Event Shape

```python
AgentEvent = dict[str, object]
```

Example events:

```json
{"type": "tool_start", "name": "file_read", "args": {"path": "README.md"}}
{"type": "tool_end", "name": "file_read", "elapsed_ms": 18, "result": {"total_lines": 42}}
{"type": "text_delta", "text": "hello"}
```

## Renderer

```python
import sys

class TuiRenderer:
    def __init__(self, mode: str = "grouped") -> None:
        self.mode = mode
        self._pending_minimal: list[str] = []

    def handle(self, event: dict) -> None:
        event_type = event.get("type")
        if event_type == "text_delta":
            self.flush()
            sys.stdout.write(str(event.get("text", "")))
            sys.stdout.flush()
        elif event_type == "tool_start":
            self.tool_start(event)
        elif event_type == "tool_end":
            self.tool_end(event)

    def tool_start(self, event: dict) -> None:
        name = str(event.get("name", "tool"))
        if self.mode == "hidden":
            return
        if self.mode == "minimal":
            self._pending_minimal.append(name)
            return
        marker = "*" if self.mode == "emoji" else "tool"
        print(f"\n{marker} {name}", file=sys.stderr)

    def tool_end(self, event: dict) -> None:
        if self.mode in {"hidden", "minimal"}:
            return
        elapsed = event.get("elapsed_ms")
        print(f"  done in {elapsed} ms", file=sys.stderr)

    def flush(self) -> None:
        if self._pending_minimal:
            print("\nTools: " + ", ".join(self._pending_minimal), file=sys.stderr)
            self._pending_minimal.clear()
```

## Wiring

```python
renderer = TuiRenderer(config.display.tool_display)
result = run_agent_with_retry(config, user_input, on_event=renderer.handle)
renderer.flush()
print(result.text)
```
