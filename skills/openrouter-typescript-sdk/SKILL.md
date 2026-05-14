---
name: openrouter-python-sdk
description: Complete reference for integrating with 300+ AI models through the OpenRouter Python SDK using the requests library and Responses API
version: 2.0.0
---

# OpenRouter Python SDK

A comprehensive Python reference for interacting with OpenRouter's unified API, providing access to 300+ AI models through a single interface. This skill enables AI agents to leverage the `requests` library for text generation, tool usage, streaming, and multi-turn conversations via the Responses API.

---

## Installation

```bash
pip install requests
pip install jsonschema  # optional, for tool schema validation
```

## Setup

Get your API key from [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys), then initialize:

```python
import requests
import os

BASE_URL = "https://openrouter.ai/api/v1"
API_KEY = os.environ["OPENROUTER_API_KEY"]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}
```

---

## Authentication

The SDK supports two authentication methods: API keys for server-side applications and OAuth PKCE flow for user-facing applications.

### API Key Authentication

#### Obtaining an API Key

1. Visit [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
2. Create a new API key
3. Store securely in an environment variable

#### Environment Setup

```bash
export OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

#### Client Initialization

```python
import requests
import os

BASE_URL = "https://openrouter.ai/api/v1"
HEADERS = {
    "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
    "Content-Type": "application/json",
}
```

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "Hello!",
})
resp.raise_for_status()
print(resp.json()["output"][0]["content"][0]["text"])
```

#### Get Current Key Metadata

```python
resp = requests.get(f"{BASE_URL}/auth/key", headers=HEADERS)
resp.raise_for_status()
key_info = resp.json()
print("Label:", key_info.get("data", {}).get("label"))
print("Usage:", key_info.get("data", {}).get("usage"))
```

#### API Key Management

```python
# List all keys
resp = requests.get(f"{BASE_URL}/auth/keys", headers=HEADERS)
keys = resp.json()

# Create a new key
resp = requests.post(f"{BASE_URL}/auth/keys", headers=HEADERS, json={
    "name": "Production API Key"
})
new_key = resp.json()

# Delete a key
resp = requests.delete(f"{BASE_URL}/auth/keys/{{hash}}", headers=HEADERS)
```

### OAuth Authentication (PKCE Flow)

#### Complete OAuth Flow Example

```python
import requests
import os
from flask import Flask, redirect, request, jsonify

app = Flask(__name__)
BASE_URL = "https://openrouter.ai/api/v1"
HEADERS = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"}

@app.get("/auth/start")
def auth_start():
    resp = requests.post(f"{BASE_URL}/auth/keys", headers=HEADERS, json={
        "callback_url": "https://myapp.com/auth/callback"
    })
    auth_response = resp.json()
    return redirect(auth_response["authorization_url"])

@app.get("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return "Authorization code missing", 400
    try:
        resp = requests.post(f"{BASE_URL}/auth/keys/exchange", headers=HEADERS, json={"code": code})
        api_key_response = resp.json()
        return redirect("/dashboard?auth=success")
    except Exception:
        return redirect("/auth/error")

@app.post("/api/chat")
def chat():
    user_api_key = get_user_api_key(session["user_id"])
    user_headers = {"Authorization": f"Bearer {user_api_key}", "Content-Type": "application/json"}
    resp = requests.post(f"{BASE_URL}/responses", headers=user_headers, json={
        "model": "openai/gpt-5-nano",
        "input": request.json["message"],
    })
    return jsonify({"response": resp.json()["output"][0]["content"][0]["text"]})
```

---

## Core Concepts: Responses API

### Basic Usage

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "Explain quantum computing in one sentence.",
})
resp.raise_for_status()
data = resp.json()
print(data["output"][0]["content"][0]["text"])
```

### Key Benefits

- **Single endpoint** for all models — just change the `model` field
- **Tool use built-in** — pass tools array, API handles multi-turn execution
- **Streaming support** via SSE
- **Previous response chaining** via `previous_response_id`

---

## Input Formats

### String Input

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "Hello, how are you?",
})
```

### Message Arrays

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": [
        {"role": "user", "content": "What is the capital of France?"},
        {"role": "assistant", "content": "The capital of France is Paris."},
        {"role": "user", "content": "What is its population?"},
    ],
})
```

### System Instructions

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "instructions": "You are a helpful coding assistant. Be concise.",
    "input": "How do I reverse a string in Python?",
})
```

---

## Response Methods

| Field | Description |
|-------|-------------|
| `id` | Response ID for chaining with `previous_response_id` |
| `output` | Array of output items (messages, tool calls) |
| `usage` | Token usage: `input_tokens`, `output_tokens`, `total_tokens` |

### Extract Text

```python
data = resp.json()
text = data["output"][0]["content"][0]["text"]
```

### Get Usage

```python
usage = data.get("usage", {})
print("Input tokens:", usage.get("input_tokens"))
print("Output tokens:", usage.get("output_tokens"))
```

### Streaming with SSE

```python
import json

resp = requests.post(
    f"{BASE_URL}/responses",
    headers={**HEADERS, "Accept": "text/event-stream"},
    json={"model": "openai/gpt-5-nano", "input": "Write a short story", "stream": True},
    stream=True,
)
for line in resp.iter_lines():
    if not line:
        continue
    line = line.decode("utf-8")
    if line.startswith("data: "):
        payload = line[6:]
        if payload == "[DONE]":
            break
        event = json.loads(payload)
        if event.get("type") == "response.output_text.delta":
            print(event.get("delta", ""), end="", flush=True)
print()
```

---

## Tool System

### Defining Tools

```python
def get_weather(city: str) -> str:
    return f"Weather for {city}: 21C and clear"

TOOLS = [{
    "name": "get_weather",
    "description": "Return current weather for a city",
}]
```

### Using Tools with the Responses API

```python
import json

def get_weather(location: str, units: str = "celsius") -> dict:
    return {"temperature": 22, "conditions": "Sunny", "humidity": 45}

resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "What is the weather in Paris?",
    "tools": [weather_tool],
})
resp.raise_for_status()
data = resp.json()
response_id = data["id"]

tool_outputs = []
for item in data.get("output", []):
    if item.get("type") == "function_call":
        args = json.loads(item["arguments"])
        result = get_weather(**args)
        tool_outputs.append({
            "type": "function_call_output",
            "call_id": item["call_id"],
            "output": json.dumps(result),
        })

if tool_outputs:
    resp2 = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
        "model": "openai/gpt-5-nano",
        "previous_response_id": response_id,
        "input": tool_outputs,
    })
    resp2.raise_for_status()
    final = resp2.json()
    print(final["output"][0]["content"][0]["text"])
```

### Server Tools

```python
server_tools = [
    {"type": "openrouter:web_search"},
    {"type": "openrouter:web_fetch"},
    {"type": "openrouter:datetime", "parameters": {"timezone": "UTC"}},
    {"type": "openrouter:image_generation", "parameters": {"model": "openai/dall-e-3"}},
]
```

---

## Multi-Turn Conversations with Stop Conditions

```python
def run_agent(model: str, prompt: str, tools: list, max_steps: int = 10) -> str:
    input_items = [{"role": "user", "content": prompt}]
    previous_id = None
    accumulated_text = ""

    for step in range(max_steps):
        payload = {"model": model, "tools": tools, "input": input_items}
        if previous_id:
            payload["previous_response_id"] = previous_id

        resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json=payload)
        resp.raise_for_status()
        data = resp.json()
        previous_id = data["id"]

        tool_calls = []
        for item in data.get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "output_text":
                        accumulated_text += part["text"]
            elif item.get("type") == "function_call":
                tool_calls.append(item)

        if not tool_calls:
            break

        input_items = []
        for tc in tool_calls:
            args = json.loads(tc["arguments"])
            result = execute_tool(tc["name"], args)
            input_items.append({
                "type": "function_call_output",
                "call_id": tc["call_id"],
                "output": json.dumps(result),
            })

    return accumulated_text
```

---

## Generation Parameters

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "Write a creative story",
    "temperature": 0.7,
    "max_output_tokens": 1000,
    "top_p": 0.9,
})
```

---

## Streaming

```python
import json

def stream_response(model: str, prompt: str) -> str:
    resp = requests.post(
        f"{BASE_URL}/responses",
        headers={**HEADERS, "Accept": "text/event-stream"},
        json={"model": model, "input": prompt, "stream": True},
        stream=True,
    )
    resp.raise_for_status()
    accumulated = ""
    for line in resp.iter_lines():
        if not line:
            continue
        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue
        payload = decoded[6:]
        if payload == "[DONE]":
            break
        event = json.loads(payload)
        if event.get("type") == "response.output_text.delta":
            delta = event.get("delta", "")
            accumulated += delta
            print(delta, end="", flush=True)
    print()
    return accumulated
```

---

## Responses API Message Shapes

### Tool Call Message

```python
{
    "type": "function_call",
    "id": "fc_123",
    "call_id": "call_abc",
    "name": "get_weather",
    "arguments": '{"location": "Paris", "units": "celsius"}',
}
```

### Tool Result Message

```python
{
    "type": "function_call_output",
    "call_id": "call_abc",
    "output": '{"temperature": 22, "conditions": "Sunny"}',
}
```

---

## Models API

```python
resp = requests.get(f"{BASE_URL}/models", headers=HEADERS)
resp.raise_for_status()
models = resp.json()["data"]
for m in models[:5]:
    print(m["id"], "-", m.get("name"))
```

---

## Credits API

```python
resp = requests.get(f"{BASE_URL}/credits", headers=HEADERS)
resp.raise_for_status()
credits = resp.json()
print("Total credits:", credits.get("data", {}).get("total_credits"))
```

---

## Error Handling

```python
import requests

try:
    resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
        "model": "openai/gpt-5-nano",
        "input": "Hello!",
    })
    resp.raise_for_status()
    data = resp.json()
except requests.HTTPError as e:
    if e.response is not None:
        status = e.response.status_code
        if status == 401:
            print("Authentication failed — check OPENROUTER_API_KEY")
        elif status == 429:
            print("Rate limit exceeded — back off and retry")
        elif status == 402:
            print("Insufficient credits")
        elif 500 <= status < 600:
            print(f"Server error {status} — retry with backoff")
    raise
except requests.RequestException as e:
    print(f"Network error: {e}")
    raise
```

### Retry Pattern

```python
import time

def post_with_retry(url: str, payload: dict, max_retries: int = 3) -> dict:
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(url, headers=HEADERS, json=payload)
            resp.raise_for_status()
            return resp.json()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            retryable = status == 429 or (500 <= status < 600)
            if not retryable or attempt == max_retries:
                raise
            time.sleep(min(1.0 * (2 ** attempt), 30.0))
    raise RuntimeError("Unreachable")
```

---

## Structured Output

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "List 3 programming languages with their use cases",
    "text": {
        "format": {
            "type": "json_schema",
            "name": "languages",
            "schema": {
                "type": "object",
                "properties": {
                    "languages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "use_case": {"type": "string"},
                            },
                            "required": ["name", "use_case"],
                        },
                    }
                },
                "required": ["languages"],
            },
            "strict": True,
        }
    },
})
import json
result = json.loads(resp.json()["output"][0]["content"][0]["text"])
print(result["languages"])
```

---

## Context Management

### Response Chaining

```python
resp1 = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "What is the capital of France?",
})
resp1.raise_for_status()
data1 = resp1.json()

resp2 = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "previous_response_id": data1["id"],
    "input": "What is its population?",
})
resp2.raise_for_status()
data2 = resp2.json()
print(data2["output"][0]["content"][0]["text"])
```

---

## Provider Routing

```python
resp = requests.post(f"{BASE_URL}/responses", headers=HEADERS, json={
    "model": "openai/gpt-5-nano",
    "input": "Hello!",
    "provider": {
        "order": ["OpenAI", "Azure"],
        "allow_fallbacks": True,
        "data_collection": "deny",
    },
})
```

---

## Complete Working Example

```python
import os
import requests

def run_example(prompt: str) -> str:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"},
        json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]
```
