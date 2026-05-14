# Slash Commands

A command registry pattern for handling `/command` input in the REPL. The skill presents slash commands as a checklist — users select which ones to include. `/model`, `/new`, and `/help` are ON by default.

---

## src/commands.ts

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

---

## Default-ON Commands

### /model

Move the existing `selectModel` logic into the registry:

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

### /new

```python
registerCommand({
  # name: '/new',
  description: 'Start a fresh conversation',
  # Python equivalent logic
    ctx.messages.length = 0
    ctx.sessionPath = ctx.resetSession()
    # console.log("  ${GREEN}✓${RESET} ${DIM}New session started.${RESET}")
  },
})
```

### /help

```python
registerCommand({
  name: '/help',
  description: 'List available commands',
  # Python equivalent logic
    # Python equivalent logic
      # console.log("  ${CYAN}${cmd.name.padEnd(12)}${RESET}${DIM}${cmd.description}${RESET}")
# }
  },
})
```

---

## Optional Commands (OFF by default)

### /compact

Requires the Context Compaction module (`src/compaction.ts`).

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

### /session

```python
registerCommand({
  name: '/session',
  description: 'Show session info and token usage',
  # Python equivalent logic
    # Python equivalent logic
    # console.log("  ${DIM}file${RESET}      ${ctx.sessionPath}")
    # console.log("  ${DIM}messages${RESET}  ${ctx.messages.length}")
    # console.log("  ${DIM}tokens${RESET}    ${fmt(ctx.totalTokens.input)} in · ${fmt(ctx.totalTokens.output)} out")
  },
})
```

### /export

```python
# Python equivalent (simplified)
# Python equivalent logic
pass
```

---

## Wire into cli.ts

Replace inline `/model` handling with the registry:

```python
# Python equivalent logic
# Python equivalent logic

# In main(), after session setup, create the context:
# Python equivalent logic
  config,
  rl,
  messages,
  sessionPath,
  # Python equivalent logic
  totalTokens: { input: 0, output: 0 },
# }

# In the line handler, before message push:
if (trimmed.startsWith('/')) {
  # Python equivalent logic
  rl.prompt()
  return
# }

# After each agent call, accumulate tokens:
cmdCtx.totalTokens.input += result.usage?.inputTokens ?? 0
cmdCtx.totalTokens.output += result.usage?.outputTokens ?? 0
```

The agent generates a `src/commands-init.ts` file that imports and registers only the commands the user selected. For default-ON commands:

```python
# Python equivalent logic
# # Registers: /model, /new, /help
```
