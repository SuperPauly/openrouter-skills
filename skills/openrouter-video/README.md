# OpenRouter Video

Create and poll video generation jobs from Python.

## Setup

```bash
pip install requests
OPENROUTER_API_KEY=your-key python3 scripts/example.py
```

## Files

- `scripts/lib.py`: shared Python request helpers.
- `scripts/example.py`: minimal runnable example for this skill.

## Pattern

```python
import os
import requests

response = requests.post(
    "https://openrouter.ai/api/v1/responses",
    headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "Content-Type": "application/json"},
    json={"model": "openai/gpt-4o", "input": "Hello"},
    timeout=60,
)
response.raise_for_status()
print(response.json())
```
