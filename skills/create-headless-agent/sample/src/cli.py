#!/usr/bin/env python3
"""
Headless agent CLI entry point.
Python equivalent of cli.ts

Usage:
  python -m src.cli [--model <id>] [--output text|json|quiet] [--no-session]
                     [--schema <json>] [--max-steps <n>] [--max-cost <f>]
                     [message]
  echo "message" | python -m src.cli
"""

import sys
import json
import os
import argparse

# Allow running as: python src/cli.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.config import load_config
from src.session import make_session_path, save_message, load_session, find_latest_session
from src.agent import run_agent_with_retry, AgentEvent


def print_event(event: AgentEvent, output_mode: str) -> None:
    if output_mode == "quiet":
        return
    etype = event.get("type")
    if etype == "text":
        sys.stdout.write(event.get("delta", ""))
        sys.stdout.flush()
    elif etype == "tool_call" and output_mode != "json":
        name = event.get("name", "")
        args = event.get("args", {})
        key = next(iter(args), None)
        arg_str = f" {key}={str(args[key])[:50]}" if key else ""
        print(f"\n  ⚡ {name}{arg_str}", file=sys.stderr)
    elif etype == "tool_result" and output_mode != "json":
        name = event.get("name", "")
        print(f"  ✓ {name}", file=sys.stderr)
    elif etype == "done":
        usage = event.get("usage", {})
        ms = event.get("duration_ms", 0)
        if output_mode != "json":
            tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
            print(f"\n\n  [{tokens} tokens · {ms}ms]", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Headless OpenRouter agent"
    )
    parser.add_argument("message", nargs="?", help="Message to send (or pipe via stdin)")
    parser.add_argument("--model", help="Model ID override")
    parser.add_argument("--output", choices=["text", "json", "quiet"], default=None,
                        help="Output mode: text (default), json, or quiet")
    parser.add_argument("--no-session", action="store_true", help="Disable session persistence")
    parser.add_argument("--schema", help="JSON schema for output validation (JSON string)")
    parser.add_argument("--max-steps", type=int, help="Override maximum agent steps")
    parser.add_argument("--max-cost", type=float, help="Override maximum cost in USD")

    args = parser.parse_args()

    overrides: dict = {}
    if args.model:
        overrides["model"] = args.model
    if args.output:
        overrides["output_mode"] = args.output
    if args.no_session:
        overrides["session_enabled"] = False
    if args.max_steps:
        overrides["max_steps"] = args.max_steps
    if args.max_cost:
        overrides["max_cost"] = args.max_cost

    output_schema = None
    if args.schema:
        try:
            output_schema = json.loads(args.schema)
            overrides["validate_output"] = True
            overrides["output_schema"] = output_schema
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON schema: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        config = load_config(overrides)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Get user message
    if args.message:
        user_input = args.message
    elif not sys.stdin.isatty():
        user_input = sys.stdin.read().strip()
    else:
        print("Error: Provide a message as an argument or pipe it via stdin.", file=sys.stderr)
        parser.print_usage(sys.stderr)
        sys.exit(1)

    if not user_input:
        print("Error: Empty message.", file=sys.stderr)
        sys.exit(1)

    # Load previous session
    messages: list[dict] = []
    session_path = ""
    if config.session_enabled:
        latest = find_latest_session(config.session_dir)
        if latest:
            messages = load_session(latest)
            session_path = latest
        else:
            session_path = make_session_path(config.session_dir)
        save_message(session_path, "user", user_input)

    # Build input — use prior messages + new input
    agent_input: list | str
    if messages:
        full_msgs = messages + [{"role": "user", "content": user_input}]
        agent_input = full_msgs
    else:
        agent_input = user_input

    output_mode = config.output_mode

    def on_event(event: AgentEvent) -> None:
        print_event(event, output_mode)

    try:
        result = run_agent_with_retry(config, agent_input, on_event=on_event)
    except RuntimeError as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)

    final_text = result.get("text", "")

    # Validate output schema if requested
    if config.validate_output and config.output_schema:
        try:
            import jsonschema
            jsonschema.validate(json.loads(final_text), config.output_schema)
        except ImportError:
            print(
                "Warning: jsonschema not installed. Install with: pip install jsonschema",
                file=sys.stderr,
            )
        except json.JSONDecodeError:
            print("Warning: Output is not valid JSON — schema validation skipped.", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Schema validation failed: {e}", file=sys.stderr)

    if config.session_enabled and session_path:
        save_message(session_path, "assistant", final_text)

    if output_mode == "json":
        print(json.dumps({
            "text": final_text,
            "usage": result.get("usage"),
            "duration_ms": result.get("duration_ms"),
        }))
    elif output_mode != "quiet":
        # text mode — text was already streamed, just ensure newline
        if final_text and not final_text.endswith("\n"):
            print()


if __name__ == "__main__":
    main()
