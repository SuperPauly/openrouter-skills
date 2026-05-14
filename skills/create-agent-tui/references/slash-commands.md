# Slash Commands

A command registry pattern for handling `/command` input in the REPL. The skill presents slash commands as a checklist — users select which ones to include. `/model`, `/new`, and `/help` are ON by default.

---

## src/commands.ts

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## Default-ON Commands

### /model

Move the existing `selectModel` logic into the registry:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### /new

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### /help

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## Optional Commands (OFF by default)

### /compact

Requires the Context Compaction module (`src/compaction.ts`).

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### /session

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

### /export

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

---

## Wire into cli.ts

Replace inline `/model` handling with the registry:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```

The agent generates a `src/commands-init.ts` file that imports and registers only the commands the user selected. For default-ON commands:

```python
# Python equivalent (simplified)
# Converted from the previous JavaScript/TypeScript-oriented snippet.
pass
```
