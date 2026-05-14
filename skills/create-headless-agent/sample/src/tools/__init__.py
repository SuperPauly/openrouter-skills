"""
Tool registry for the headless agent.
Python equivalent of tools/index.ts

Add or remove tools by editing this module.
Server tools (web_search, datetime) are declared here but executed by OpenRouter.
"""

from . import file_read, file_write, file_edit, glob_tool, grep_tool, list_dir, shell

# Map tool name -> execute function
_TOOL_EXECUTORS = {
    "file_read": file_read.execute,
    "file_write": file_write.execute,
    "file_edit": file_edit.execute,
    "glob": glob_tool.execute,
    "grep": grep_tool.execute,
    "list_dir": list_dir.execute,
    "shell": shell.execute,
    # Note: custom.execute can be added here if desired
}

# Client-executed tools (schemas sent to OpenRouter for the model to call)
_CLIENT_TOOL_SCHEMAS = [
    {"type": "function", **file_read.SCHEMA},
    {"type": "function", **file_write.SCHEMA},
    {"type": "function", **file_edit.SCHEMA},
    {"type": "function", **glob_tool.SCHEMA},
    {"type": "function", **grep_tool.SCHEMA},
    {"type": "function", **list_dir.SCHEMA},
    {"type": "function", **shell.SCHEMA},
]

# Server-executed tools (OpenRouter runs these; no client code needed)
_SERVER_TOOL_SCHEMAS = [
    {"type": "openrouter:web_search"},
    {"type": "openrouter:datetime", "parameters": {"timezone": "UTC"}},
]

ALL_TOOL_SCHEMAS = _CLIENT_TOOL_SCHEMAS + _SERVER_TOOL_SCHEMAS


def get_tool_executor(name: str):
    """Return the execute() function for a client-executed tool, or None."""
    return _TOOL_EXECUTORS.get(name)
