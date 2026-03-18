---
title: Tools
description: Learn how to define MCP tools that AI agents can call to interact with Actian data sources.
---

# Tools

MCP **tools** are callable functions exposed to AI clients. When an AI agent needs to query a database, run a DDL statement, or perform any action, it invokes a tool.

---

## Anatomy of a Tool

A tool has:

- **Name** — unique identifier (e.g., `execute_query`)
- **Description** — natural-language explanation the AI uses to decide when to call it
- **Input schema** — JSON Schema defining the parameters
- **Handler** — the Python function that executes the logic

---

## Defining a Tool

```python
# features/tools.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import json

def register_tools(server: Server):

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="execute_query",
                description="Execute a SQL SELECT query against the connected database.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SQL SELECT statement to execute."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return.",
                            "default": 100
                        }
                    },
                    "required": ["query"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "execute_query":
            query = arguments["query"]
            limit = arguments.get("limit", 100)
            # ... execute against data source ...
            results = []  # replace with actual query results
            return [TextContent(type="text", text=json.dumps(results))]
```

---

## Best Practices

- Write clear, specific `description` text — the AI uses this to choose the right tool
- Validate inputs early and return descriptive error messages
- Use `read_only` guards where appropriate to prevent destructive operations
- Return structured JSON for results the AI needs to reason over

---

## Built-in Tools

The Actian MCP Server ships with tools for:

| Tool | Description |
|------|-------------|
| `execute_query` | Run a SQL SELECT against a connected database |
| `execute_statement` | Run DDL/DML statements (insert, update, create table…) |
| `list_tables` | List all tables in the current schema |
| `describe_table` | Get column definitions for a table |
| `get_schema` | Retrieve full schema metadata |

See the [API Reference](../../APIs/index.md) for full signatures.
