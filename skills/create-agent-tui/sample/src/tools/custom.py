"""
Custom tool template — replace with your domain-specific logic.

This tool demonstrates the tool registration pattern.
Rename, extend, or delete this file as needed.
"""

SCHEMA = {
    "name": "my_tool",
    "description": "Describe what this tool does",
    "parameters": {
        "type": "object",
        "properties": {
            "param": {"type": "string", "description": "Description of the parameter"},
        },
        "required": ["param"],
    },
}


def execute(args: dict) -> dict:
    param = args.get("param", "")
    # Implement your tool logic here
    return {"result": "done", "param": param}
