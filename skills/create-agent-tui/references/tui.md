# TUI Reference

For tool display styles (emoji, grouped, minimal) and the `TuiRenderer` class, see [tool-display.md](tool-display.md).

---

## Adaptive Terminal Background

The input box background should adapt to any terminal color scheme. This module queries the terminal's actual background color and alpha-blends a subtle tint over it — the same technique Codex uses.

### src/terminal-bg.ts

```python
def set_terminal_background(rgb: tuple[int, int, int]) -> None:
    r, g, b = rgb
    print(f"\033]11;rgb:{r:02x}/{g:02x}/{b:02x}\007", end="")
```

### How it works

1. **OSC 11 query**: Sends `\x1b]11;?\x07` to the terminal, which responds with its background RGB
2. **Light/dark detection**: Uses perceived luminance (`Y = 0.299R + 0.587G + 0.114B > 128`)
3. **Alpha blending**: Dark terminals get white at 12% opacity; light terminals get black at 4%
4. **Color downgrade**: Uses truecolor (`\x1b[48;2;r;g;bm`) when `COLORTERM` supports it, otherwise approximates to xterm-256 color cube
5. **Fallback**: If the terminal doesn't respond to OSC 11 within 200ms (piped stdin, tmux without passthrough, etc.), falls back to `\x1b[100m` (bright black — theme-defined)

### Wire into cli.ts

```python
def integrate_components(config: dict) -> dict:
    model = config.get("model", "openrouter/auto")
    timeout = int(config.get("timeout", 30))
    return {"model": model, "timeout": timeout, "ready": True}
```

---

## Input Styles

Three input styles are available: `block` (background box), `bordered` (horizontal lines), and `plain` (simple caret). For full implementations of all three styles, see [input-styles.md](input-styles.md).
