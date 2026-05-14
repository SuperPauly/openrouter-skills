"""
Slash command dispatcher.
Python equivalent of commands.ts — same commands with same output.
"""

import sys
import json

try:
    import requests as _requests
except ImportError:
    _requests = None  # type: ignore

from .config import AgentConfig

DIM   = "\x1b[2m"
RESET = "\x1b[0m"
CYAN  = "\x1b[36m"
GREEN = "\x1b[32m"


class CommandContext:
    def __init__(
        self,
        config: AgentConfig,
        messages: list[dict],
        session_path: str,
        reset_session,
        total_tokens: dict[str, int],
    ) -> None:
        self.config = config
        self.messages = messages
        self.session_path = session_path
        self.reset_session = reset_session
        self.total_tokens = total_tokens


class SlashCommand:
    def __init__(self, name: str, description: str, execute) -> None:
        self.name = name
        self.description = description
        self._execute = execute

    def execute(self, args: str, ctx: CommandContext) -> None:
        self._execute(args, ctx)


_COMMANDS: list[SlashCommand] = []


def _ask(prompt: str) -> str:
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return sys.stdin.readline().rstrip("\n")


def _cmd_model(args: str, ctx: CommandContext) -> None:
    print(f"  {DIM}Current:{RESET} {CYAN}{ctx.config.model}{RESET}")
    query = _ask(f"  {DIM}Search models:{RESET} ")
    if not query.strip():
        return
    sys.stdout.write(f"  {DIM}Fetching…{RESET}")
    sys.stdout.flush()
    if _requests is None:
        print("\r\x1b[K  requests package required for /model command.", file=sys.stderr)
        return
    try:
        res = _requests.get("https://openrouter.ai/api/v1/models", timeout=10)
        data = res.json().get("data", [])
    except Exception as e:
        print(f"\r\x1b[K  Error fetching models: {e}", file=sys.stderr)
        return
    sys.stdout.write("\r\x1b[K")
    sys.stdout.flush()
    q = query.lower()
    matches = [m for m in data if q in m.get("id", "").lower() or q in m.get("name", "").lower()][:15]
    if not matches:
        print(f'  {DIM}No models matching "{query}".{RESET}')
        return
    for i, m in enumerate(matches):
        print(f"  {DIM}{str(i + 1).rjust(2)}){RESET} {m['id']}")
    pick = _ask(f"\n  {DIM}Select (1-{len(matches)}):{RESET} ")
    try:
        idx = int(pick) - 1
        if 0 <= idx < len(matches):
            ctx.config.model = matches[idx]["id"]
            print(f"  {DIM}Model →{RESET} {CYAN}{ctx.config.model}{RESET}")
        else:
            print(f"  {DIM}Cancelled.{RESET}")
    except ValueError:
        print(f"  {DIM}Cancelled.{RESET}")


def _cmd_new(args: str, ctx: CommandContext) -> None:
    ctx.messages.clear()
    ctx.session_path = ctx.reset_session()
    print(f"  {GREEN}✓{RESET} {DIM}New session started.{RESET}")


def _cmd_help(args: str, ctx: CommandContext) -> None:
    for cmd in _COMMANDS:
        print(f"  {CYAN}{cmd.name.ljust(12)}{RESET}{DIM}{cmd.description}{RESET}")


_COMMANDS.extend([
    SlashCommand("/model", "Switch to a different model", _cmd_model),
    SlashCommand("/new",   "Start a fresh conversation",  _cmd_new),
    SlashCommand("/help",  "List available commands",     _cmd_help),
])


def dispatch(user_input: str, ctx: CommandContext) -> bool:
    """Handle a slash command. Returns True if input was a command (recognised or not)."""
    parts = user_input.split(" ", 1)
    name = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    cmd = next((c for c in _COMMANDS if c.name == name), None)
    if not cmd:
        print(f"  {DIM}Unknown command: {name}. Type /help for available commands.{RESET}")
        return True
    cmd.execute(args, ctx)
    return True
