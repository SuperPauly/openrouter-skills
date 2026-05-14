"""
Agent loop using OpenRouter Responses API with SSE streaming.
Same implementation as headless sample — imported by cli.py.
"""

import os
import json
import time
import sys
from typing import Optional, Callable

try:
    import requests
except ImportError:
    print("Error: 'requests' package required. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

from .config import AgentConfig
from .tools import ALL_TOOL_SCHEMAS, get_tool_executor

BASE_URL = "https://openrouter.ai/api/v1"
AgentEvent = dict
ChatMessage = dict


def _call_api(api_key, model, input_items, tools, instructions, previous_response_id):
    payload: dict = {
        "model": model,
        "input": input_items,
        "tools": tools,
        "stream": True,
    }
    if instructions:
        payload["instructions"] = instructions
    if previous_response_id:
        payload["previous_response_id"] = previous_response_id
    return requests.post(
        f"{BASE_URL}/responses",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        stream=True,
        timeout=120,
    )


def _process_stream(response, on_event):
    accumulated_text = ""
    fc_map: dict[str, dict] = {}
    response_id = None
    usage: dict = {}
    for raw_line in response.iter_lines():
        if not raw_line:
            continue
        line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
        if not line.startswith("data:"):
            continue
        data_str = line[5:].strip()
        if data_str == "[DONE]":
            break
        try:
            ev = json.loads(data_str)
        except json.JSONDecodeError:
            continue
        etype = ev.get("type", "")
        if etype in ("response.created", "response.in_progress"):
            resp_obj = ev.get("response") or {}
            if resp_obj.get("id"):
                response_id = resp_obj["id"]
        elif etype == "response.output_text.delta":
            delta = ev.get("delta", "")
            if delta:
                accumulated_text += delta
                if on_event:
                    on_event({"type": "text", "delta": delta})
        elif etype == "response.output_item.added":
            item = ev.get("item") or {}
            if item.get("type") == "function_call":
                item_id = item.get("id") or str(ev.get("output_index", len(fc_map)))
                fc_map[item_id] = {"call_id": item.get("call_id", ""), "name": item.get("name", ""), "arguments_buf": item.get("arguments", "")}
        elif etype == "response.function_call_arguments.delta":
            item_id = ev.get("item_id")
            if item_id and item_id in fc_map:
                fc_map[item_id]["arguments_buf"] += ev.get("delta", "")
        elif etype == "response.function_call_arguments.done":
            item_id = ev.get("item_id")
            if item_id and item_id in fc_map:
                fc_map[item_id]["arguments_buf"] = ev.get("arguments", fc_map[item_id]["arguments_buf"])
        elif etype == "response.completed":
            resp_obj = ev.get("response") or {}
            if resp_obj.get("id"):
                response_id = resp_obj["id"]
            u = resp_obj.get("usage") or {}
            usage = {"input_tokens": u.get("input_tokens", 0), "output_tokens": u.get("output_tokens", 0)}
    return accumulated_text, list(fc_map.values()), response_id, usage


def run_agent(config: AgentConfig, user_input, *, on_event=None) -> dict:
    started = time.monotonic()
    if isinstance(user_input, str):
        input_items: list = [{"type": "message", "role": "user", "content": user_input}]
    else:
        input_items = [{"type": "message", "role": m["role"], "content": m["content"]} for m in user_input]
    instructions = config.system_prompt.replace("{cwd}", os.getcwd())
    total_usage = {"input_tokens": 0, "output_tokens": 0}
    accumulated_text = ""
    previous_response_id = None
    step = 0
    while step < config.max_steps:
        resp = _call_api(config.api_key, config.model, input_items, ALL_TOOL_SCHEMAS, instructions, previous_response_id)
        if not resp.ok:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text[:500]}")
        text, function_calls, response_id, usage = _process_stream(resp, on_event)
        accumulated_text += text
        previous_response_id = response_id
        total_usage["input_tokens"] += usage.get("input_tokens", 0)
        total_usage["output_tokens"] += usage.get("output_tokens", 0)
        if not function_calls:
            break
        tool_results = []
        for fc in function_calls:
            call_id = fc["call_id"]
            name = fc["name"]
            try:
                parsed_args = json.loads(fc["arguments_buf"]) if fc["arguments_buf"] else {}
            except json.JSONDecodeError:
                parsed_args = {}
            if on_event:
                on_event({"type": "tool_call", "name": name, "callId": call_id, "args": parsed_args})
            executor = get_tool_executor(name)
            if executor:
                try:
                    result = executor(parsed_args)
                except Exception as e:
                    result = {"error": str(e)}
                output_str = json.dumps(result) if not isinstance(result, str) else result
                preview = output_str[:200] + "…" if len(output_str) > 200 else output_str
                if on_event:
                    on_event({"type": "tool_result", "name": name, "callId": call_id, "output": preview})
                    on_event({"type": "turn_end"})
                tool_results.append({"type": "function_call_output", "call_id": call_id, "output": output_str})
        input_items = tool_results
        step += 1
    duration_ms = int((time.monotonic() - started) * 1000)
    if on_event:
        on_event({"type": "done", "usage": total_usage, "duration_ms": duration_ms})
    return {"text": accumulated_text, "usage": total_usage, "duration_ms": duration_ms}


def run_agent_with_retry(config, user_input, *, on_event=None, max_retries=3) -> dict:
    for attempt in range(max_retries + 1):
        tool_calls_made = 0
        def tracking(event, _tcm=None):
            nonlocal tool_calls_made
            if event.get("type") == "tool_call":
                tool_calls_made += 1
            if on_event:
                on_event(event)
        try:
            return run_agent(config, user_input, on_event=tracking)
        except RuntimeError as e:
            msg = str(e)
            status = None
            if msg.startswith("API error "):
                try:
                    status = int(msg.split()[2].rstrip(":"))
                except (IndexError, ValueError):
                    pass
            retryable = status == 429 or (status is not None and 500 <= status < 600)
            if not retryable or attempt == max_retries or tool_calls_made > 0:
                raise
            time.sleep(min(1.0 * (2 ** attempt), 30.0))
    raise RuntimeError("Unreachable")
