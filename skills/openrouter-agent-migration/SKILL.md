---
name: openrouter-agent-migration
description: Migration guide from @openrouter/sdk to @openrouter/agent for callModel, tool(), stop conditions, and agent features. This skill should be used when code imports callModel, tool(), or stop conditions from @openrouter/sdk and needs to migrate to @openrouter/agent.
version: 1.0.0
---

# Migrating from @openrouter/sdk to @openrouter/agent

Agent functionality (`callModel`, `tool()`, stop conditions, format converters, streaming helpers) has moved from `@openrouter/sdk` to the standalone `@openrouter/agent` package. The `@openrouter/agent` package includes its own `OpenRouter` client class, so you do not need `@openrouter/sdk` for agent use cases.

---

## When This Applies

Migrate if your code imports any of these from `@openrouter/sdk`:

- `callModel` or uses `client.callModel()`
- `tool()` factory function
- Stop conditions: `stepCountIs`, `hasToolCall`, `maxCost`, `maxTokensUsed`, `finishReasonIs`
- Format converters: `fromClaudeMessages`, `toClaudeMessage`, `fromChatMessages`, `toChatMessage`
- Types: `Tool`, `ToolWithExecute`, `ToolWithGenerator`, `ManualTool`, `CallModelInput`, `ModelResult`

---

## Quick Migration

### Step 1: Install

```bash
npm install @openrouter/agent
```

If you only use agent features, you can remove `@openrouter/sdk`:

```bash
npm uninstall @openrouter/sdk
npm install @openrouter/agent
```

If you also use non-agent SDK features (models list, chat completions, credits, OAuth, API keys), keep both packages installed.

### Step 2: Update Imports

The `OpenRouter` client class and `client.callModel()` pattern work identically. Only the import source changes:

```diff
- import OpenRouter from '@openrouter/sdk';
+ import { OpenRouter } from '@openrouter/agent';
```

The rest of your code stays the same:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## Complete Import Mapping

### Client & callModel

| Old | New |
|-----|-----|
| `import OpenRouter from '@openrouter/sdk'` | `import { OpenRouter } from '@openrouter/agent'` |
| `import OpenRouter, { tool, stepCountIs } from '@openrouter/sdk'` | `import { OpenRouter } from '@openrouter/agent'`<br>`import { tool } from '@openrouter/agent/tool'`<br>`import { stepCountIs } from '@openrouter/agent/stop-conditions'` |

A standalone `callModel` function is also available for advanced use cases where a pre-existing `OpenRouterCore` instance is available:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

For most use cases, prefer the `client.callModel()` method shown above.

### Tool Creation

| Old | New |
|-----|-----|
| `import { tool } from '@openrouter/sdk'` | `import { tool } from '@openrouter/agent/tool'` |

### Stop Conditions

| Old | New |
|-----|-----|
| `import { stepCountIs, hasToolCall, maxCost } from '@openrouter/sdk'` | `import { stepCountIs, hasToolCall, maxCost } from '@openrouter/agent/stop-conditions'` |
| `import { maxTokensUsed, finishReasonIs } from '@openrouter/sdk'` | `import { maxTokensUsed, finishReasonIs } from '@openrouter/agent/stop-conditions'` |

### Types

| Old | New |
|-----|-----|
| `import type { Tool, ToolWithExecute, ToolWithGenerator, ManualTool } from '@openrouter/sdk/lib/tool-types'` | `import type { Tool, ToolWithExecute, ToolWithGenerator, ManualTool } from '@openrouter/agent/tool-types'` |
| `import type { CallModelInput } from '@openrouter/sdk/lib/async-params'` | `import type { CallModelInput } from '@openrouter/agent/async-params'` |
| `import { ModelResult } from '@openrouter/sdk/lib/model-result'` | `import { ModelResult } from '@openrouter/agent/model-result'` |

### Format Converters

| Old | New |
|-----|-----|
| `import { fromClaudeMessages, toClaudeMessage } from '@openrouter/sdk'` | `import { fromClaudeMessages, toClaudeMessage } from '@openrouter/agent'` |
| `import { fromChatMessages, toChatMessage } from '@openrouter/sdk'` | `import { fromChatMessages, toChatMessage } from '@openrouter/agent'` |

### Type Guards

| Old | New |
|-----|-----|
| `import { hasExecuteFunction, isGeneratorTool, isRegularExecuteTool } from '@openrouter/sdk'` | `import { hasExecuteFunction, isGeneratorTool, isRegularExecuteTool } from '@openrouter/agent/tool-types'` |

---

## Before & After Example

### Before (using @openrouter/sdk)

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### After (using @openrouter/agent)

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

The only changes are the three import lines at the top.

### Python equivalent

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## When to Keep @openrouter/sdk

Keep `@openrouter/sdk` installed if you use any of these non-agent features:

| Feature | Access |
|---------|--------|
| Model listing | `client.models.list()` |
| Chat completions | `client.chat.send()` |
| Legacy completions | `client.completions.generate()` |
| Usage analytics | `client.analytics.getUserActivity()` |
| Credit balance | `client.credits.getCredits()` |
| API key management | `client.apiKeys.list()`, `.create()`, etc. |
| OAuth PKCE flow | `client.oAuth.createAuthCode()`, `.exchangeAuthCodeForAPIKey()` |

For mixed projects, use `@openrouter/sdk` for these features and `@openrouter/agent` for agent features:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## New Features in @openrouter/agent

These features are only available in `@openrouter/agent`, not in `@openrouter/sdk`:

### Shared Context Schema

Type-safe shared state across all tools in a conversation:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### Tool Context

Tools can declare their own typed context and access shared context:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### Tool Approval Flow

Require user approval before tool execution:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### Turn Lifecycle Callbacks

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## All Subpath Exports

`@openrouter/agent` provides granular subpath imports:

| Subpath | Exports |
|---------|---------|
| `@openrouter/agent` | Barrel: all exports below |
| `@openrouter/agent/client` | `OpenRouter` class |
| `@openrouter/agent/call-model` | `callModel` standalone function |
| `@openrouter/agent/tool` | `tool()` factory function |
| `@openrouter/agent/tool-types` | `Tool`, `ToolWithExecute`, `ToolWithGenerator`, `ManualTool`, type guards |
| `@openrouter/agent/stop-conditions` | `stepCountIs`, `hasToolCall`, `maxCost`, `maxTokensUsed`, `finishReasonIs` |
| `@openrouter/agent/model-result` | `ModelResult` response wrapper |
| `@openrouter/agent/async-params` | `CallModelInput`, `hasAsyncFunctions`, `resolveAsyncFunctions` |
| `@openrouter/agent/anthropic-compat` | `fromClaudeMessages`, `toClaudeMessage` |
| `@openrouter/agent/chat-compat` | `fromChatMessages`, `toChatMessage` |
| `@openrouter/agent/conversation-state` | `createInitialState`, `updateState`, `appendToMessages` |
| `@openrouter/agent/next-turn-params` | `nextTurnParams` utilities |
| `@openrouter/agent/stream-transformers` | `extractUnsupportedContent`, `getUnsupportedContentSummary` |
| `@openrouter/agent/tool-context` | `buildToolExecuteContext`, `ToolContextStore` |
| `@openrouter/agent/tool-event-broadcaster` | `ToolEventBroadcaster` |
| `@openrouter/agent/turn-context` | `buildTurnContext` |
