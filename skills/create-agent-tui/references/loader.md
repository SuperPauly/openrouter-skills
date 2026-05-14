# Loader Styles

Three loader animations are available, configured via `config.display.loader`. The default is `gradient` with text `"Working"`.

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

| Style | Look | Description |
|-------|------|-------------|
| `gradient` | Scrolling color wave over the text | Each letter cycles through gray-to-white ANSI 256 colors, creating a shimmer effect. 150ms per frame. |
| `spinner` | `⠋ Working` / `⠙ Working` / ... | Braille dot spinner (10-frame cycle) to the left of the text. 80ms per frame. Same style as Pi and Codex. |
| `minimal` | `Working·` / `Working··` / `Working···` | Dot trail to the right of the text. 300ms per frame. Lowest visual noise. |

---

## src/loader.ts

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## Wire into cli.ts

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
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
