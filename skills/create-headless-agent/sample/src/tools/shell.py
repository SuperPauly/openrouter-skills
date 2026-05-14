"""shell tool — execute a shell command."""

import os
import subprocess
import signal
import sys

SCHEMA = {
    "name": "shell",
    "description": "Execute a shell command and return output",
    "parameters": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Shell command to execute"},
            "timeout": {"type": "number", "description": "Timeout in seconds (default: 120)"},
        },
        "required": ["command"],
    },
}

MAX_LINES = 2000
MAX_BYTES = 256 * 1024


def execute(args: dict) -> dict:
    command = args.get("command", "")
    timeout = int(args.get("timeout") or 120)
    shell = os.environ.get("SHELL", "/bin/bash")

    try:
        proc = subprocess.run(
            [shell, "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        combined = proc.stdout + proc.stderr
        lines = combined.splitlines()
        truncated = len(lines) > MAX_LINES or len(combined.encode()) > MAX_BYTES
        if truncated:
            output = "\n".join(lines[-MAX_LINES:])
        else:
            output = combined
        result: dict = {"output": output, "exitCode": proc.returncode}
        if truncated:
            result["truncated"] = True
        return result
    except subprocess.TimeoutExpired:
        return {"output": "", "exitCode": -1, "timedOut": True}
    except OSError as e:
        return {"error": str(e)}
