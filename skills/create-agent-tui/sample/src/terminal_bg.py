"""
Detect terminal background color and compute a subtle input-area background.
Python equivalent of terminal-bg.ts — exact same algorithm.
"""

import sys
import os
import select
import termios
import tty

FALLBACK = "\x1b[100m"


def _blend(fg: tuple[int, int, int], bg: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
    return (
        round(fg[0] * alpha + bg[0] * (1 - alpha)),
        round(fg[1] * alpha + bg[1] * (1 - alpha)),
        round(fg[2] * alpha + bg[2] * (1 - alpha)),
    )


def _is_light(r: int, g: int, b: int) -> bool:
    return 0.299 * r + 0.587 * g + 0.114 * b > 128


def _to_ansi(r: int, g: int, b: int) -> str:
    colorterm = os.environ.get("COLORTERM", "")
    if "truecolor" in colorterm or "24bit" in colorterm:
        return f"\x1b[48;2;{r};{g};{b}m"
    ri = round(r / 255 * 5)
    gi = round(g / 255 * 5)
    bi = round(b / 255 * 5)
    return f"\x1b[48;5;{16 + 36 * ri + 6 * gi + bi}m"


def _query_terminal_bg(timeout_ms: int = 200) -> tuple[int, int, int] | None:
    """Send OSC 11 query and parse the response for the terminal background colour."""
    if not sys.stdin.isatty():
        return None
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        sys.stdout.write("\x1b]11;?\x07")
        sys.stdout.flush()
        ready, _, _ = select.select([sys.stdin], [], [], timeout_ms / 1000)
        if not ready:
            return None
        buf = os.read(fd, 64).decode("latin-1", errors="replace")
    except Exception:
        return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

    import re
    m = re.search(r"\x1b\]11;rgb:([0-9a-fA-F]+)/([0-9a-fA-F]+)/([0-9a-fA-F]+)", buf)
    if not m:
        return None
    return (
        int(m.group(1)[:2], 16),
        int(m.group(2)[:2], 16),
        int(m.group(3)[:2], 16),
    )


def detect_bg() -> str:
    """Return an ANSI background colour escape sequence for the input area."""
    bg = _query_terminal_bg()
    if not bg:
        return FALLBACK
    r, g, b = bg
    if _is_light(r, g, b):
        top: tuple[int, int, int] = (0, 0, 0)
        alpha = 0.04
    else:
        top = (255, 255, 255)
        alpha = 0.12
    br, bg2, bb = _blend(top, (r, g, b), alpha)
    return _to_ansi(br, bg2, bb)
