---
name: openrouter-agent-migration
description: Convert older OpenRouter agent examples to Python using the OpenRouter Python SDK, requests, JSON Schema dictionaries, and Python tool functions.
version: 2.0.0
---

# OpenRouter Agent Migration

This skill helps convert older OpenRouter agent examples into Python. Prefer the official OpenRouter Python SDK for chat and platform operations, and use the low-level Responses API with `requests` when you need direct tool-call control.

## What to replace

| Older concept | Python equivalent |
|---|---|
| Agent client object | `OpenRouter` from the `openrouter` Python package, or a small `requests` wrapper. |
| Schema helper libraries | Python dictionaries containing JSON Schema. |
| Local tool callbacks | Plain Python functions that accept `dict` arguments. |
| Stop conditions | A Python loop with `max_steps`, cost checks, or a named finish tool. |
| Streaming helpers | SDK streaming iterators or Server-Sent Events through `requests`. |

## Minimal Python Target

```python
from openrouter import OpenRouter
import os

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    response = client.chat.send(
        model="minimax/minimax-m2",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(response.choices[0].message.content)
```

## Tool-Calling Target

```python
import json
import os
import requests

API_URL = "https://openrouter.ai/api/v1/responses"
HEADERS = {
    "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
    "Content-Type": "application/json",
}

weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
}

def get_weather(args: dict) -> dict:
    return {"location": args["location"], "forecast": "sunny"}

def call_model(input_items: list[dict]) -> dict:
    response = requests.post(
        API_URL,
        headers=HEADERS,
        json={"model": "openai/o4-mini", "input": input_items, "tools": [weather_tool]},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()

items = [{"role": "user", "content": "Weather in Paris?"}]
result = call_model(items)
for item in result.get("output", []):
    if item.get("type") == "function_call" and item.get("name") == "get_weather":
        args = json.loads(item.get("arguments") or "{}")
        tool_result = get_weather(args)
        items.append(item)
        items.append({"type": "function_call_output", "call_id": item["call_id"], "output": json.dumps(tool_result)})
        result = call_model(items)

print(result)
```

## Migration Checklist

- Replace old manifests with `pyproject.toml` and `requirements.txt`.
- Replace extension-based imports with Python package imports.
- Replace schema builders with JSON Schema dictionaries.
- Replace async callback tools with plain functions or `async def` functions if the surrounding app is async.
- Replace process, file, and glob helpers with `subprocess`, `pathlib`, and `glob`.
- Add tests for config loading, retry behavior, and local tool side effects.
