# Python Input Styles

The TUI offers three input styles. Each style returns one user message string and keeps all rendering in `src/cli.py`.

## Block

Full-width background-colored input with a prompt marker.

```python

def block_read_line(background: str = "\x1b[48;5;236m") -> str:
    reset = "\x1b[0m"
    prompt = f"{background}  > {reset}"
    return input(prompt)
```

Use this when the terminal supports ANSI colors. Pair it with `terminal_bg.detect_background` for adaptive colors.

## Bordered

```python
import shutil

def bordered_read_line() -> str:
    width = shutil.get_terminal_size((80, 20)).columns
    border = "-" * width
    print(border)
    value = input("> ")
    print(border)
    return value
```

## Plain

```python
def plain_read_line() -> str:
    return input("> ")
```

## Wiring

```python
def get_input(style: str) -> str:
    if style == "block":
        return block_read_line()
    if style == "bordered":
        return bordered_read_line()
    return plain_read_line()
```

Display the current working directory above the prompt if desired:

```python
from pathlib import Path

def prompt_header() -> str:
    home = str(Path.home())
    cwd = str(Path.cwd()).replace(home, "~", 1)
    return f"Working directory: {cwd}"
```
