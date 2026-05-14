"""JSONL session persistence (same as headless agent)."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

DEFAULT_SESSION_DIR = ".sessions"


def make_session_path(session_dir: str = DEFAULT_SESSION_DIR) -> str:
    Path(session_dir).mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    return str(Path(session_dir) / f"session-{stamp}.jsonl")


def save_message(path: str, role: str, content: str) -> None:
    entry = json.dumps({"role": role, "content": content, "ts": datetime.now().isoformat()})
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry + "\n")


def load_session(path: str) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    messages = []
    for line in p.read_text(encoding="utf-8").splitlines():
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
    p = Path(session_dir)
    if not p.exists():
        return None
    files = sorted(p.glob("session-*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None
