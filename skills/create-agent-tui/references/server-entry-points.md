# Python Server Entry Points

Use these entry points when the TUI needs to run behind an API or serve browser clients.

## FastAPI Server

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .agent import run_agent_with_retry, stream_agent_events
from .config import load_config

app = FastAPI()
config = load_config()

class PromptRequest(BaseModel):
    prompt: str
    model: str | None = None

@app.post("/agent")
def agent(request: PromptRequest):
    local_config = config.with_model(request.model or config.model)
    result = run_agent_with_retry(local_config, request.prompt)
    return {"text": result.text, "usage": result.usage}

@app.post("/agent/stream")
def agent_stream(request: PromptRequest):
    local_config = config.with_model(request.model or config.model)
    return StreamingResponse(stream_agent_events(local_config, request.prompt), media_type="text/event-stream")
```

Run it with:

```bash
pip install fastapi uvicorn
OPENROUTER_API_KEY=your-key uvicorn src.server:app --reload
```

## Background Worker

```python
from queue import Queue
from threading import Thread

from .agent import run_agent_with_retry
from .config import load_config

jobs: Queue[str] = Queue()
config = load_config()

def worker() -> None:
    while True:
        prompt = jobs.get()
        try:
            result = run_agent_with_retry(config, prompt)
            print(result.text)
        finally:
            jobs.task_done()

Thread(target=worker, daemon=True).start()
```
