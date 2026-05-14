#!/usr/bin/env python3
"""
TUI CLI entry point.
Python equivalent of cli.ts — visually identical terminal experience.

Usage: python -m src.cli [--model <id>]
"""

import sys
import os
import signal
import threading

# Allow: python src/cli.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import load_config
from src.session import make_session_path, save_message, load_session, find_latest_session
from src.banner import print_banner
from src.terminal_bg import detect_bg
from src.loader import Loader
from src.renderer import TuiRenderer
from src.commands import dispatch, CommandContext
from src.agent import run_agent_with_retry, AgentEvent

# ANSI constants
RESET = "\x1b[0m"
DIM   = "\x1b[2m"
BOLD  = "\x1b[1m"
CYAN  = "\x1b[36m"
GREEN = "\x1b[32m"
RED   = "\x1b[31m"
WHITE = "\x1b[97m"


def _styled_read_line(bg: str) -> str:
    """
    Read a line of input with a styled block prompt (block input style).
    Visually identical to the TypeScript styledReadLine() function.
    """
    import tty
    import termios

    line = ""
    first_draw = [True]

    def draw():
        if first_draw[0]:
            sys.stdout.write(f"\n{bg}\x1b[K{RESET}\n")
            sys.stdout.write(f"{bg}\x1b[K {WHITE}›{RESET}{bg}{WHITE} {line}{RESET}\n")
            sys.stdout.write(f"{bg}\x1b[K{RESET}\x1b[1A\r\x1b[{4 + len(line)}G")
            sys.stdout.flush()
            first_draw[0] = False
        else:
            sys.stdout.write(f"\r\x1b[2K")
            sys.stdout.write(f"{bg}\x1b[K {WHITE}›{RESET}{bg}{WHITE} {line}{RESET}")
            sys.stdout.write(f"\n{bg}\x1b[K{RESET}\x1b[1A\r\x1b[{4 + len(line)}G")
            sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        draw()
        while True:
            ch = sys.stdin.read(1)
            code = ord(ch)
            if ch == "\x1b":
                # Skip escape sequences (arrow keys etc.)
                try:
                    sys.stdin.read(2)
                except Exception:
                    pass
                continue
            if code in (13, 10):  # Enter / Return
                sys.stdout.write(f"{RESET}\n")
                sys.stdout.flush()
                break
            elif code in (127, 8):  # Backspace / Delete
                line = line[:-1]
                draw()
            elif code == 3:  # Ctrl-C
                sys.stdout.write(f"{RESET}\n")
                sys.stdout.flush()
                raise KeyboardInterrupt
            elif code == 4:  # Ctrl-D
                sys.stdout.write(f"{RESET}\n")
                sys.stdout.flush()
                raise EOFError
            elif code >= 32:
                line += ch
                draw()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return line


def _bordered_read_line(bg: str) -> str:
    """
    Read a line with a bordered prompt (line input style).
    Visually identical to TypeScript borderedReadLine().
    """
    import tty
    import termios

    line = ""
    border_top    = "╭" + "─" * 60 + "╮"
    border_bottom = "╰" + "─" * 60 + "╯"

    def draw_first():
        sys.stdout.write(f"\n{DIM}{border_top}{RESET}\n")
        sys.stdout.write(f"{DIM}│{RESET} {line}\n")
        sys.stdout.write(f"{DIM}{border_bottom}{RESET}\x1b[1A\r\x1b[{3 + len(line)}G")
        sys.stdout.flush()

    def draw_update():
        sys.stdout.write(f"\r\x1b[2K{DIM}│{RESET} {line}\x1b[0G\x1b[{3 + len(line)}C")
        sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        draw_first()
        while True:
            ch = sys.stdin.read(1)
            code = ord(ch)
            if ch == "\x1b":
                try:
                    sys.stdin.read(2)
                except Exception:
                    pass
                continue
            if code in (13, 10):
                sys.stdout.write(f"\n{RESET}")
                sys.stdout.flush()
                break
            elif code in (127, 8):
                line = line[:-1]
                draw_update()
            elif code == 3:
                sys.stdout.write(f"\n{RESET}")
                sys.stdout.flush()
                raise KeyboardInterrupt
            elif code == 4:
                sys.stdout.write(f"\n{RESET}")
                sys.stdout.flush()
                raise EOFError
            elif code >= 32:
                line += ch
                draw_update()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return line


def _plain_read_line() -> str:
    """Plain input style — standard readline prompt."""
    sys.stdout.write(f"\n{BOLD}›{RESET} ")
    sys.stdout.flush()
    return sys.stdin.readline().rstrip("\n")


def _read_input(input_style: str, bg: str) -> str:
    if input_style == "block":
        return _styled_read_line(bg)
    elif input_style == "line":
        return _bordered_read_line(bg)
    else:
        return _plain_read_line()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(prog="cli.py", description="OpenRouter agent TUI")
    parser.add_argument("--model", help="Model ID override")
    cli_args = parser.parse_args()

    overrides: dict = {}
    if cli_args.model:
        overrides["model"] = cli_args.model

    try:
        config = load_config(overrides)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if config.show_banner:
        print_banner(config.model)

    # Detect terminal background for styled input
    bg = detect_bg()

    renderer = TuiRenderer(config.display)
    loader = Loader(config.display.loader)

    # Session
    session_path = ""
    messages: list[dict] = []

    def reset_session() -> str:
        messages.clear()
        sp = make_session_path(config.session_dir)
        return sp

    latest = find_latest_session(config.session_dir)
    if latest:
        messages = load_session(latest)
        session_path = latest
    else:
        session_path = make_session_path(config.session_dir)

    total_tokens = {"input": 0, "output": 0}

    ctx = CommandContext(
        config=config,
        messages=messages,
        session_path=session_path,
        reset_session=reset_session,
        total_tokens=total_tokens,
    )

    print(f"{DIM}Type /help for commands, Ctrl-C or Ctrl-D to exit.{RESET}\n")

    while True:
        try:
            user_input = _read_input(config.display.input_style, bg)
        except (KeyboardInterrupt, EOFError):
            print(f"\n{DIM}Goodbye.{RESET}")
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Slash commands
        if user_input.startswith("/"):
            dispatch(user_input, ctx)
            continue

        # Save user message to session
        save_message(session_path, "user", user_input)

        # Build agent input (include history)
        if messages:
            agent_input = messages + [{"role": "user", "content": user_input}]
        else:
            agent_input = user_input

        loader.start()
        first_token = threading.Event()

        def on_event(event: AgentEvent) -> None:
            etype = event.get("type")
            if etype == "text" and not first_token.is_set():
                loader.stop()
                first_token.set()
            elif etype == "tool_call":
                loader.stop()
                first_token.set()
            renderer.handle(event)
            if etype == "turn_end":
                renderer.end_turn()
            elif etype == "done":
                renderer.end_streaming()
                usage = event.get("usage", {})
                total_tokens["input"] += usage.get("input_tokens", 0)
                total_tokens["output"] += usage.get("output_tokens", 0)
                ms = event.get("duration_ms", 0)
                total = total_tokens["input"] + total_tokens["output"]
                print(f"\n{DIM}[{total} tokens · {ms}ms]{RESET}\n")

        try:
            result = run_agent_with_retry(config, agent_input, on_event=on_event)
        except RuntimeError as e:
            loader.stop()
            print(f"\n{RED}Error: {e}{RESET}", file=sys.stderr)
            continue
        finally:
            loader.stop()

        final_text = result.get("text", "")
        if final_text:
            save_message(session_path, "assistant", final_text)
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": final_text})


if __name__ == "__main__":
    main()
