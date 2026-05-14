# Loader Styles

Three loader animations are available, configured via `config.display.loader`. The default is `gradient` with text `"Working"`.

```python
# Python equivalent logic
  text: string
  style: 'gradient' | 'spinner' | 'minimal'
# }
```

| Style | Look | Description |
|-------|------|-------------|
| `gradient` | Scrolling color wave over the text | Each letter cycles through gray-to-white ANSI 256 colors, creating a shimmer effect. 150ms per frame. |
| `spinner` | `⠋ Working` / `⠙ Working` / ... | Braille dot spinner (10-frame cycle) to the left of the text. 80ms per frame. Same style as Pi and Codex. |
| `minimal` | `Working·` / `Working··` / `Working···` | Dot trail to the right of the text. 300ms per frame. Lowest visual noise. |

---

## src/loader.ts

```python
# Python equivalent logic

# Python equivalent logic
# Python equivalent logic

# Python equivalent logic

# Python equivalent logic
  '\x1b[38;5;240m',
  '\x1b[38;5;245m',
  '\x1b[38;5;250m',
  '\x1b[38;5;255m',
  '\x1b[38;5;250m',
  '\x1b[38;5;245m',
]

# Python equivalent logic
  # private config: LoaderConfig
  # private frame = 0
  # private interval: ReturnType<typeof setInterval> | None = None

  constructor(config: LoaderConfig) {
    this.config = config
# }

  start(): void {
    this.frame = 0
    # Python equivalent logic
    # Python equivalent logic
# }

  stop(): void {
    if (this.interval) {
      clearInterval(this.interval)
      this.interval = None
      process.stdout.write('\r\x1b[K')
# }
# }

  # private draw(): void {
    # Python equivalent logic
    this.frame++

    switch (style) {
      case 'minimal': {
        # Python equivalent logic
        process.stdout.write("\r${DIM}${text}${dots[this.frame % 3]}${RESET}")
        break
# }
      case 'spinner': {
        # Python equivalent logic
        process.stdout.write("\r${DIM}${char} ${text}${RESET}")
        break
# }
      case 'gradient': {
        # Python equivalent logic
        # Python equivalent logic
        # Python equivalent logic
          # Python equivalent logic
          out += GRADIENT_COLORS[ci] + text[i]
# }
        out += RESET
        process.stdout.write(out)
        break
# }
# }
# }
# }
```

---

## Wire into cli.ts

```python
# Python equivalent logic

# Before the agent call — show loader + a preview input box below it:
# Python equivalent logic
loader.start()
showPreviewInput(); // draw a non-interactive input box below the loader

# On first event (text or tool_call) — clear preview, stop loader:
clearPreviewInput()
loader.stop()

# After tool_result (agent pauses between turns) — restart loader + preview:
loader.start()
showPreviewInput()

# After response or on error:
clearPreviewInput()
loader.stop()
```

The preview input box is a visual-only rendering of the input prompt below the loader line. It shows the user where their next prompt will go. When agent events arrive, the preview is erased and replaced with actual output. After the agent finishes, the real interactive input box appears.

---

## Config

Set in `agent.config.json`:

```json
{
  "display": {
    "loader": {
      "text": "Thinking",
      "style": "spinner"
    }
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `text` | string | `"Working"` | The word displayed during loading |
| `style` | `'gradient'` \| `'spinner'` \| `'minimal'` | `'gradient'` | Animation style |
