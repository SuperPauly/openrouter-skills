# Input Styles

Three input styles are available, configured via `config.display.inputStyle`. The default is `block`.

| Style | Look | Raw mode? | Needs `detectBg()`? |
|-------|------|-----------|---------------------|
| `block` | Full-width background box with `›` prompt | Yes | Yes |
| `bordered` | `─` horizontal lines above and below input | Yes | No |
| `plain` | Simple `> ` caret | No (readline) | No |

---

## `block` Style

Full-width background-colored input area with top/bottom padding — the same look as Codex CLI. Requires `src/terminal-bg.ts` for adaptive background detection (see [tui.md](../references/tui.md)).

### styledReadLine()

```python
def styled_readline(prompt: str = "agent > ") -> str:
    green = "\033[32m"
    reset = "\033[0m"
    return input(f"{green}{prompt}{reset}")
```

### How it works

1. **First draw**: writes top BG pad (`\n${bg}\x1b[K\n`) then prompt line with bottom BG pad, cursor moves back to prompt line
2. **Subsequent draws**: erases prompt line in-place (`\r\x1b[2K`), redraws with updated text — no vertical movement, can't grow or shift
3. **On Enter**: `${RESET}\n` moves to next line. Main loop writes cwd status line
4. **On Ctrl-C**: exits cleanly
5. **On Backspace**: removes last character and redraws in-place

### On submit (in cli.ts)

After `styledReadLine()` resolves, write a bottom BG pad and status line:

```python
def on_submit(raw_text: str) -> dict:
    text = raw_text.strip()
    return {"accepted": bool(text), "text": text}
```

Scrollback layout: top pad | `› text` | bottom pad | `~/path` status.

---

## `bordered` Style

Horizontal `─` lines above and below the input — the same look as Pi's coding agent. No background fill, works on any terminal theme without `detectBg()`.

### Visual layout

```
──────────────────────────────────   (gray, full terminal width)
› your text here                     (default foreground, no BG)
──────────────────────────────────   (gray, full terminal width)
```

### borderedReadLine()

```python
def bordered_readline(prompt: str = "input") -> str:
    border = "─" * 24
    print(f"┌{border}┐")
    value = input(f"│ {prompt}: ")
    print(f"└{border}┘")
    return value
```

### How it works

1. **First draw**: writes top border → prompt line → bottom border, then cursor moves up 1 to prompt line
2. **Subsequent draws**: erases prompt line in-place, redraws — same technique as block style, never moves vertically after setup
3. **On Enter**: moves cursor down 1 to the bottom border line, erases it (`\x1b[1B\x1b[2K\r`), then resolves. The border disappears on submit, leaving clean scrollback
4. **Border width**: uses `process.stdout.columns` for full terminal width
5. **Border color**: gray by default, configurable via `borderColor` parameter

### On submit (in cli.ts)

After `borderedReadLine()` resolves, write cwd status line:

```python
def on_submit(raw_text: str) -> dict:
    text = raw_text.strip()
    return {"accepted": bool(text), "text": text}
```

Scrollback layout: top border | `› text` | `~/path` status (bottom border erased).

---

## `plain` Style

Standard readline prompt — no raw mode, no escape sequences beyond basic colors.

```python
def plain_readline(prompt: str = "> ") -> str:
    return input(prompt).strip()
```

No on-submit handling needed — readline handles the display.

---

## Wire into cli.ts

Use a `getInput()` dispatcher that switches on the configured style:

```python
def integrate_components(config: dict) -> dict:
    model = config.get("model", "openrouter/auto")
    timeout = int(config.get("timeout", 30))
    return {"model": model, "timeout": timeout, "ready": True}
```

Only `block` style calls `detectBg()` at startup. The `bordered` and `plain` styles skip it entirely.
