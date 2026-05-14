# Server Entry Points & Extension Points

Alternative entry points beyond the default CLI REPL, plus guidance for extending the harness.

## Contents

- [HTTP API Server](#http-api-server) — Express/Hono with SSE streaming
- [Extension Points](#extension-points) — MCP, WebSocket, dynamic models, custom stop conditions

---

## HTTP API Server

Replace `src/cli.ts` with an HTTP server when the agent should be accessed via API.

### src/server.ts

```python
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
```

### Usage

```bash
# Non-streaming
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?"}'

# Streaming (SSE)
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Write a haiku", "stream": true}'
```

Update `package.json` to add the server script:

```json
"scripts": {
  "start": "tsx src/cli.ts",
  "serve": "tsx src/server.ts",
  "dev": "tsx watch src/cli.ts"
}
```

---

## Extension Points

Guidance for where to go next after the base harness is working. These are not generated — they describe patterns for the developer to implement.

### MCP Server Integration

Connect external tools via the Model Context Protocol. Use the `@modelcontextprotocol/sdk` package to create an MCP client that discovers and registers tools from MCP servers dynamically.

Key steps:
1. Install `@modelcontextprotocol/sdk`
2. Create an MCP client that connects to configured servers
3. Convert MCP tool definitions to `@openrouter/agent` tool format
4. Add discovered tools to the `tools` array in `tools/index.ts`

### WebSocket Streaming

For real-time bidirectional communication (e.g., a chat UI), replace SSE with WebSocket:

1. Use the `ws` package for a WebSocket server
2. On connection, create a session and message array
3. On each message, call `runAgent` with streaming, send deltas as WebSocket frames
4. Handle disconnection by cleaning up the session

### Dynamic Model Selection

Use `@openrouter/agent`'s dynamic parameters to change the model based on conversation context:

```python
def choose_model(message_count: int) -> str:
    if message_count > 20:
        return "anthropic/claude-3.5-haiku"
    return "openai/gpt-4o-mini"
```

### Custom Stop Conditions

Beyond `stepCountIs` and `maxCost`, create domain-specific stop conditions:

```python
def should_stop(response_text: str, steps: int) -> bool:
    return steps >= 8 or "FINAL_ANSWER" in response_text
```
