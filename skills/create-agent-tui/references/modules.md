# Harness Modules

Optional architectural modules that extend the core harness. Each section includes purpose, complete code, and how to wire it into `agent.ts` and `cli.ts`.

## Contents

- [Session Persistence](#session-persistence) — JSONL conversation log (DEFAULT ON)
- [Context Compaction](#context-compaction) — summarize older messages
- [System Prompt Composition](#system-prompt-composition) — dynamic instructions from context files
- [Tool Approval](#tool-approval) — gate dangerous tools behind user confirmation
- [Structured Event Logging](#structured-event-logging) — emit events for observability

---

## Session Persistence

JSONL (newline-delimited JSON) append-only log for crash-safe conversation persistence. Pattern from pi-mono's session manager.

### src/session.ts

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

### Integration

In `cli.ts`, wrap the message loop:

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

---

## Context Compaction

When conversation history grows too long, summarize older messages to fit within the model's context window. Pattern from pi-mono's compaction with file tracking.

### src/compaction.ts

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

### Integration

In `agent.ts`, call before `callModel`:

```python
# Python equivalent logic

# Inside runAgent, when input is a message array, compact before calling callModel:
if (Array.isArray(input)) {
  # Python equivalent logic
  # Python equivalent logic
    threshold: 40,
    keepRecent: 10,
  })
# }
# Then pass input to callModel as usual
```

---

## System Prompt Composition

Compose the system prompt from a static base plus dynamically loaded context files (similar to how pi-mono loads AGENTS.md/CLAUDE.md from project directories).

### src/system-prompt.ts

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

### Integration

In `agent.ts`, use as the `instructions` parameter:

```python
# Python equivalent logic

# Python equivalent logic
  base: config.systemPrompt,
  contextFiles: ['AGENTS.md', 'CLAUDE.md', '.agent-context.md'],
  projectDir: process.cwd(),
})

# Pass to callModel:
client.callModel({ instructions, ... })
```

---

## Tool Approval

Gate dangerous tools behind user confirmation. Uses `requireApproval` from `@openrouter/agent/tool` plus a session-scoped approval cache. Pattern from Codex's approval flow.

### Adding requireApproval to tools

For tools that should require approval, set `requireApproval: true` in the tool definition:

```python
# Python equivalent logic
  name: 'shell',
  description: 'Execute a shell command',
  inputSchema: z.object({ command: z.string(), timeout: z.number().optional() }),
  requireApproval: True,  // <-- user must confirm before execution
  # Python equivalent logic
})
```

Or use a function for conditional approval based on the config:

```python
# Python equivalent logic
  return tool({
    name: 'shell',
    description: 'Execute a shell command',
    inputSchema: z.object({ command: z.string(), timeout: z.number().optional() }),
    requireApproval: approvalPolicy == 'always'
      ? True
      : approvalPolicy == 'never'
        ? False
        # Python equivalent logic
    # Python equivalent logic
  })
# }
```

### Integration

Add `approvalPolicy` to the config:

```python
# Python equivalent logic
approvalPolicy: 'always' | 'never' | 'dangerous-only'

# Python equivalent logic
# Python equivalent logic

# Python equivalent logic
  return [
    fileReadTool,   // never needs approval
    fileWriteTool,  // maybe
    createShellTool(config.approvalPolicy),
  ]
# }
```

---

## Structured Event Logging

Emit structured events for tool calls, API requests, and errors. Entry point decides how to render them. Pattern from Codex's tracing.

### src/logger.ts

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

### Integration

In `agent.ts`, emit events in callbacks:

```python
# Python equivalent logic

# Python equivalent logic
  # Python equivalent logic

  # Python equivalent logic
# ...
    # Python equivalent logic
      logger.emit('turn_start', { turn: ctx.numberOfTurns })
    },
    # Python equivalent logic
      logger.emit('turn_end', { turn: ctx.numberOfTurns })
    },
  })
# ...
# }
```

In `cli.ts`, attach a handler:

```python
# Python equivalent logic

# Python equivalent logic
logger.on(consoleLogHandler); // or a custom handler
```

---

## `@`-file References

Let users type `@filename` to attach file content to their message. Before sending to the agent, scan the input for `@path` tokens, read each file, and prepend the content.

### Integration

In `cli.ts`, before pushing the user message:

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

Optional: add tab completion for `@` using `rl.completer` to fuzzy-match files in the working directory.

---

## `!` Shell Shortcut

`!command` runs a shell command and injects stdout into context as a user message, without going through a tool call. `!!command` runs silently (output not shown).

### Integration

In `cli.ts`, before command dispatch:

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

---

## Multi-line Input

Replace readline with raw terminal mode to support Shift+Enter for newlines. Enter sends the message.

### src/multi-line-input.ts

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

### Integration

Replace the `rl.on('line')` loop with calls to `readMultiLine(prompt)` in a `while` loop.

