"""
Animated terminal loader.
Python equivalent of loader.ts — visually identical output.
"""

import sys
import threading
import time

from .config import LoaderConfig

DIM   = "\x1b[2m"
RESET = "\x1b[0m"

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

GRADIENT_COLORS = [
    "\x1b[38;5;240m",
    "\x1b[38;5;245m",
    "\x1b[38;5;250m",
    "\x1b[38;5;255m",
    "\x1b[38;5;250m",
    "\x1b[38;5;245m",
]


class Loader:
    def __init__(self, config: LoaderConfig) -> None:
        self._config = config
        self._frame = 0
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._frame = 0
        ms = 150 if self._config.style == "gradient" else 80 if self._config.style == "spinner" else 300

        def _run() -> None:
            while self._running:
                self._draw()
                time.sleep(ms / 1000)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)
        sys.stdout.write("\r\x1b[K")
        sys.stdout.flush()

    def _draw(self) -> None:
        text = self._config.text
        style = self._config.style
        self._frame += 1
        f = self._frame

        if style == "minimal":
            dots = ["·", "··", "···"]
            sys.stdout.write(f"\r{DIM}{text}{dots[f % 3]}{RESET}")
        elif style == "spinner":
            char = SPINNER_FRAMES[f % len(SPINNER_FRAMES)]
            sys.stdout.write(f"\r{DIM}{char} {text}{RESET}")
        elif style == "gradient":
            n = len(GRADIENT_COLORS)
            out = "\r"
            for i, ch in enumerate(text):
                out += GRADIENT_COLORS[(f + i) % n] + ch
            out += RESET
            sys.stdout.write(out)
        sys.stdout.flush()
