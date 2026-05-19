# Python Loader Animations

The loader runs while waiting for a model response. Keep it isolated so the agent loop can start and stop it around network calls.

## Loader Class

```python
from __future__ import annotations

import itertools
import sys
import threading
import time

class Loader:
    def __init__(self, text: str = "thinking", style: str = "spinner") -> None:
        self.text = text
        self.style = style
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=1)
        sys.stderr.write("\r" + " " * 80 + "\r")
        sys.stderr.flush()

    def _run(self) -> None:
        frames = itertools.cycle(["|", "/", "-", "\\"])
        dots = itertools.cycle(["", ".", "..", "..."])
        while not self._stop.is_set():
            if self.style == "minimal":
                frame = next(dots)
                sys.stderr.write(f"\r{self.text}{frame}")
            else:
                sys.stderr.write(f"\r{next(frames)} {self.text}")
            sys.stderr.flush()
            time.sleep(0.12)
```

## Wiring

```python
loader = Loader(config.display.loader_text, config.display.loader_style)
loader.start()
try:
    result = run_agent_with_retry(config, user_input)
finally:
    loader.stop()
```
