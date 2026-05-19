# OpenRouter Python SDK

Complete Python reference for OpenRouter chat, Responses, streaming, tool calling, model metadata, and authentication. Use the official `openrouter` package for typed SDK calls and `requests` for low-level Responses API flows.

## Install

```bash
pip install openrouter requests
```

## SDK Quickstart

```python
from openrouter import OpenRouter
import os

with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
    response = client.chat.send(
        model="minimax/minimax-m2",
        messages=[{"role": "user", "content": "Explain quantum computing"}],
    )
    print(response.choices[0].message.content)
```

## Async SDK

```python
import asyncio
import os
from openrouter import OpenRouter

async def main() -> None:
    async with OpenRouter(api_key=os.getenv("OPENROUTER_API_KEY")) as client:
        response = await client.chat.send_async(
            model="minimax/minimax-m2",
            messages=[{"role": "user", "content": "Hello"}],
        )
        print(response.choices[0].message.content)

asyncio.run(main())
```

## Responses API with Requests

```python
import os
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/responses",
    headers={
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
    },
    json={"model": "openai/gpt-4o", "input": "Tell me a joke"},
    timeout=60,
)
response.raise_for_status()
print(response.json())
```

## Tool Definitions

```python
weather_tool = {
    "type": "function",
    "name": "get_weather",
    "description": "Get the current weather in a location.",
    "parameters": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City and region"},
            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
        },
        "required": ["location"],
    },
}
```

## Streaming with Requests

```python
import json
import os
import requests

with requests.post(
    "https://openrouter.ai/api/v1/responses",
    headers={
        "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    },
    json={"model": "openai/gpt-4o", "input": "Count to five", "stream": True},
    stream=True,
    timeout=120,
) as response:
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        payload = line.removeprefix("data: ")
        if payload == "[DONE]":
            break
        event = json.loads(payload)
        print(event)
```

## Model Metadata

```python
from openrouter import OpenRouter

with OpenRouter() as client:
    models = client.models.list()
    for model in models.data[:10]:
        print(model.id, getattr(model, "context_length", None))
```

## Environment

Set `OPENROUTER_API_KEY` in your shell, process manager, or `.env` loader before running examples.
