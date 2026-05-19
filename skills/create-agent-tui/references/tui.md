# Python Terminal Background Detection

Use terminal background detection only for the block input style. If detection times out, fall back to a neutral ANSI background.

```python
import os
import select
import sys
import termios
import tty


def detect_background(timeout: float = 0.05) -> str:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return "#1f1f1f"
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdout.write("\x1b]11;?\x07")
        sys.stdout.flush()
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
        if not ready:
            return "#1f1f1f"
        data = os.read(fd, 128).decode(errors="ignore")
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if "rgb:" not in data:
        return "#1f1f1f"
    rgb = data.split("rgb:", 1)[1].split("\x07", 1)[0]
    parts = rgb.split("/")[:3]
    if len(parts) != 3:
        return "#1f1f1f"
    values = [int(part[:2], 16) for part in parts]
    return "#" + "".join(f"{value:02x}" for value in values)
```

Convert the color into a fixed ANSI fallback if true-color output is not needed.
