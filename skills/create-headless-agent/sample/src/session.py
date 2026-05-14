"""
JSONL session persistence.
Python equivalent of session.ts
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Optional

DEFAULT_SESSION_DIR = ".sessions"


def make_session_path(session_dir: str = DEFAULT_SESSION_DIR) -> str:
    """Generate a timestamped session file path."""
    Path(session_dir).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return str(Path(session_dir) / f"session-{stamp}.jsonl")


def save_message(path: str, role: str, content: str) -> None:
    """Append a message to the session JSONL file."""
    entry = json.dumps({"role": role, "content": content, "ts": datetime.now().isoformat()})
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def load_session(path: str) -> list[dict]:
    """Load messages from a JSONL session file."""
    session_path = Path(path)
    if not session_path.exists():
        return []
    messages = []
    for line in session_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            messages.append({"role": msg["role"], "content": msg["content"]})
        except (json.JSONDecodeError, KeyError):
            continue
    return messages


def find_latest_session(session_dir: str = DEFAULT_SESSION_DIR) -> Optional[str]:
    """Find the most recent session file."""
    session_path = Path(session_dir)
    if not session_path.exists():
        return None
    files = sorted(
        session_path.glob("session-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return str(files[0]) if files else None
