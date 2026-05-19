# Python Slash Commands

Slash commands are small functions registered by name. They run before model calls and can mutate local session state.

## Registry

```python
from collections.abc import Callable
from dataclasses import dataclass, field

@dataclass
class CommandContext:
    model: str
    messages: list[dict] = field(default_factory=list)
    session_path: str | None = None

Command = Callable[[str, CommandContext], str | None]
COMMANDS: dict[str, Command] = {}

def register_command(name: str, handler: Command) -> None:
    COMMANDS[name] = handler

def dispatch(line: str, context: CommandContext) -> str | None:
    name, _, rest = line[1:].partition(" ")
    handler = COMMANDS.get(name)
    if handler is None:
        return f"Unknown command: {name}"
    return handler(rest.strip(), context)
```

## Built-ins

```python
def model_command(value: str, context: CommandContext) -> str:
    if value:
        context.model = value
    return f"Model: {context.model}"

def new_command(value: str, context: CommandContext) -> str:
    context.messages.clear()
    return "Started a new session"

def help_command(value: str, context: CommandContext) -> str:
    names = ", ".join(sorted(COMMANDS))
    return f"Commands: {names}"

register_command("model", model_command)
register_command("new", new_command)
register_command("help", help_command)
```

## Wiring

```python
context = CommandContext(model=config.model)
line = get_input(config.display.input_style).strip()
if line.startswith("/"):
    message = dispatch(line, context)
    if message:
        print(message)
else:
    result = run_agent_with_retry(config.with_model(context.model), line)
```
