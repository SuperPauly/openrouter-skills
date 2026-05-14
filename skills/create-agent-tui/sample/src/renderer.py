"""
TUI renderer — format and print agent events.
Python equivalent of renderer.ts — visually identical output.
"""

import sys
from .config import DisplayConfig

# ANSI escape codes — exact same as TypeScript version
RESET   = "\x1b[0m"
DIM     = "\x1b[2m"
BOLD    = "\x1b[1m"
GREEN   = "\x1b[32m"
YELLOW  = "\x1b[33m"
RED     = "\x1b[31m"
CYAN    = "\x1b[36m"
GRAY    = "\x1b[90m"
MAGENTA = "\x1b[35m"

DEFAULT_FORMATTERS: dict[str, "ToolFormatter"] = {
    "shell":      lambda n, a: f"command={_trunc(str(a.get('command', '')))}",
    "file_read":  lambda n, a: f"path={_trunc(str(a.get('path', '')))}",
    "file_write": lambda n, a: f"path={_trunc(str(a.get('path', '')))}",
    "file_edit":  lambda n, a: f"path={_trunc(str(a.get('path', '')))}",
    "glob":       lambda n, a: f"pattern={_trunc(str(a.get('pattern', '')))}",
    "grep":       lambda n, a: f"pattern={_trunc(str(a.get('pattern', '')))}",
    "list_dir":   lambda n, a: f"path={_trunc(str(a.get('path', '')))}",
    "web_search": lambda n, a: f"query={_trunc(str(a.get('query', '')))}",
}

TOOL_LABELS: dict[str, dict[str, str]] = {
    "shell":      {"past": "Ran",      "noun": "shell command"},
    "file_read":  {"past": "Read",     "noun": "file"},
    "file_write": {"past": "Wrote",    "noun": "file"},
    "file_edit":  {"past": "Edited",   "noun": "file"},
    "glob":       {"past": "Explored", "noun": "pattern"},
    "grep":       {"past": "Searched", "noun": "pattern"},
    "list_dir":   {"past": "Listed",   "noun": "directory"},
    "web_search": {"past": "Fetched",  "noun": "search"},
}

ToolFormatter = object  # callable(name, args) -> str


def _trunc(s: str, max_len: int = 50) -> str:
    return s[:max_len] + "…" if len(s) > max_len else s


def _plural(n: int, noun: str) -> str:
    if n == 1:
        return f"1 {noun}"
    if noun.endswith("y"):
        return f"{n} {noun[:-1]}ies"
    return f"{n} {noun}s"


class _PendingCall:
    def __init__(self, name: str, call_id: str, args: dict) -> None:
        self.name = name
        self.call_id = call_id
        self.args = args
        self.output: str | None = None


class TuiRenderer:
    def __init__(
        self,
        display: DisplayConfig,
        tool_formatters: dict | None = None,
        tool_colors: dict | None = None,
    ) -> None:
        self._display = display
        self._formatters: dict = {**DEFAULT_FORMATTERS, **(tool_formatters or {})}
        self._tool_colors: dict = {"shell": RED, "web_search": MAGENTA, **(tool_colors or {})}
        self._tool_start: dict[str, float] = {}
        self._streaming = False
        self._line_buf = ""
        self._in_code_block = False
        self._grouped_pending: list[_PendingCall] = []
        self._grouped_category = ""
        self._minimal_batch: dict[str, int] = {}

    def handle(self, event: dict) -> None:
        etype = event.get("type")
        if etype == "text":
            self._render_text(event.get("delta", ""))
        elif etype == "tool_call":
            self._render_tool_call(event.get("name", ""), event.get("callId", ""), event.get("args", {}))
        elif etype == "tool_result":
            self._render_tool_result(event.get("name", ""), event.get("callId", ""), event.get("output", ""))
        elif etype == "reasoning":
            self._render_reasoning(event.get("delta", ""))

    def _render_text(self, delta: str) -> None:
        self._flush_grouped()
        self._flush_minimal()
        self._streaming = True
        self._line_buf += delta
        lines = self._line_buf.split("\n")
        self._line_buf = lines.pop()
        for line in lines:
            sys.stdout.write(self._format_markdown_line(line) + "\n")
        sys.stdout.flush()

    def _flush_line_buf(self) -> None:
        if self._line_buf:
            sys.stdout.write(self._format_markdown_line(self._line_buf))
            self._line_buf = ""

    def _format_markdown_line(self, line: str) -> str:
        import re
        if line.startswith("```"):
            self._in_code_block = not self._in_code_block
            return DIM if self._in_code_block else RESET
        if self._in_code_block:
            return f"{DIM}{line}{RESET}"
        if re.match(r"^#{1,3}\s", line):
            return f"\n{BOLD}{re.sub(r'^#+\\s*', '', line)}{RESET}"
        out = line
        out = re.sub(r"\*\*(.+?)\*\*", lambda m: f"{BOLD}{m.group(1)}{RESET}", out)
        out = re.sub(r"`([^`]+)`", lambda m: f"{CYAN}{m.group(1)}{RESET}", out)
        return out

    def _render_tool_call(self, name: str, call_id: str, args: dict) -> None:
        import time as _time
        if self._display.tool_display == "hidden":
            return
        self._end_streaming()
        self._tool_start[call_id] = _time.monotonic()

        if self._display.tool_display == "emoji":
            color = self._tool_colors.get(name, YELLOW)
            formatter = self._formatters.get(name, self._default_formatter)
            arg_str = formatter(name, args)
            print(f"  {color}⚡{RESET} {DIM}{name}{' ' + arg_str if arg_str else ''}{RESET}")
        elif self._display.tool_display == "grouped":
            category = TOOL_LABELS.get(name, {}).get("past", name)
            if category != self._grouped_category:
                self._flush_grouped()
                self._grouped_category = category
            self._grouped_pending.append(_PendingCall(name, call_id, args))
        elif self._display.tool_display == "minimal":
            self._minimal_batch[name] = self._minimal_batch.get(name, 0) + 1

    def _render_tool_result(self, name: str, call_id: str, output: str) -> None:
        import time as _time
        if self._display.tool_display == "hidden":
            return
        start = self._tool_start.get(call_id, _time.monotonic())
        ms = (_time.monotonic() - start) * 1000
        dur = f"({ms / 1000:.1f}s)"
        if self._display.tool_display == "emoji":
            print(f"  {GREEN}✓{RESET} {DIM}{name} {dur}{RESET}")
        elif self._display.tool_display == "grouped":
            for p in self._grouped_pending:
                if p.call_id == call_id:
                    p.output = output
                    break

    def _render_reasoning(self, delta: str) -> None:
        if not self._display.reasoning:
            return
        self._flush_minimal()
        self._end_streaming()
        sys.stdout.write(f"{DIM}{delta}{RESET}")
        sys.stdout.flush()

    def end_streaming(self) -> None:
        self._end_streaming()

    def _end_streaming(self) -> None:
        if self._streaming:
            self._flush_line_buf()
            self._in_code_block = False
            sys.stdout.write(RESET + "\n")
            sys.stdout.flush()
            self._streaming = False

    def end_turn(self) -> None:
        self._flush_grouped()
        self._flush_minimal()
        self._end_streaming()

    def _flush_grouped(self) -> None:
        if not self._grouped_pending:
            return
        first = self._grouped_pending[0]
        label = TOOL_LABELS.get(first.name, {}).get("past", first.name)
        formatter = self._formatters.get(first.name, self._default_formatter)
        if len(self._grouped_pending) == 1:
            arg_str = formatter(first.name, first.args)
            print(f"{GREEN}●{RESET} {BOLD}{label}{RESET} {arg_str}")
            if first.output:
                line0 = first.output.split("\n")[0]
                print(f"  └ {GRAY}{_trunc(line0, 70)}{RESET}")
        else:
            print(f"{GREEN}●{RESET} {BOLD}{label}{RESET}")
            for i, pending in enumerate(self._grouped_pending):
                arg_str = formatter(pending.name, pending.args)
                is_last = i == len(self._grouped_pending) - 1
                branch = "└" if is_last else "├"
                if pending.output:
                    line0 = pending.output.split("\n")[0]
                    print(f"  {branch} {DIM}{arg_str}{RESET} {GRAY}{_trunc(line0, 50)}{RESET}")
                else:
                    print(f"  {branch} {DIM}{arg_str}{RESET}")
        print()
        self._grouped_pending = []
        self._grouped_category = ""

    def _flush_minimal(self) -> None:
        if not self._minimal_batch:
            return
        parts = []
        for name, count in self._minimal_batch.items():
            label = TOOL_LABELS.get(name)
            if label:
                parts.append(f"{label['past'].lower()} {_plural(count, label['noun'])}")
            else:
                parts.append(_plural(count, name))
        print(f"  {GRAY}{', '.join(parts)}{RESET}")
        self._minimal_batch.clear()

    def _default_formatter(self, name: str, args: dict) -> str:
        if not args:
            return ""
        key = next(iter(args))
        return f"{key}={_trunc(str(args[key]))}"
