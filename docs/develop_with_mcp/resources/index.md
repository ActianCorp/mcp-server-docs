---
title: Resources
description: Learn how to expose readable data resources that AI agents can consume for context.
---

# Resources

MCP **resources** are readable data sources that provide context to AI agents. Unlike tools (which perform actions), resources expose information — database schemas, table lists, metadata, documentation — that the AI reads to understand the environment.

---

## Anatomy of a Resource

A resource has:

- **URI** — unique address (e.g., `actian://schema/main`)
- **Name** — human-readable label
- **Description** — what the resource contains
- **MIME type** — format of the content (usually `text/plain` or `application/json`)
- **Handler** — Python function that returns the content

---

## Defining a Resource

```python
# features/resources.py
from mcp.server import Server
from mcp.types import Resource, TextContent
import json

def register_resources(server: Server):

    @server.list_resources()
    async def list_resources():
        return [
            Resource(
                uri="actian://schema/tables",
                name="Database Tables",
                description="List of all tables available in the connected database.",
                mimeType="application/json"
            ),
            Resource(
                uri="actian://schema/full",
                name="Full Database Schema",
                description="Complete schema definition including columns, types, and constraints.",
                mimeType="application/json"
            )
        ]

    @server.read_resource()
    async def read_resource(uri: str):
        if uri == "actian://schema/tables":
            tables = []  # replace with actual table list from DB
            return [TextContent(type="text", text=json.dumps(tables))]

        if uri == "actian://schema/full":
            schema = {}  # replace with actual schema introspection
            return [TextContent(type="text", text=json.dumps(schema))]
```

---

## URI Conventions

Use a consistent URI scheme across your plugin:

```
actian://<plugin>/<resource-type>/<identifier>

Examples:
  actian://zen/schema/tables
  actian://zen/schema/columns/customers
  actian://analytics/datasets/list
```

---

## Built-in Resources

| URI | Description |
|-----|-------------|
| `actian://schema/tables` | All tables in the active database |
| `actian://schema/columns/{table}` | Column definitions for a specific table |
| `actian://schema/full` | Full schema as JSON |
| `actian://server/info` | Server version and connection metadata |

---

## Best Practices

- Keep resources **read-only** — resources should not produce side effects
- Return JSON for structured data the AI needs to reason over
- Use descriptive names and descriptions — the AI reads these to decide what to fetch
- Cache expensive schema introspection calls where possible
