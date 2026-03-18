---
title: Develop with MCP
description: Learn how to build tools, resources, prompts, and plugins for the Actian MCP Server.
---

# Develop with MCP

This section covers everything you need to extend and customise the Actian MCP Server.

The server is built around a **plugin architecture** — each plugin exposes its own set of MCP primitives (tools, resources, prompts) that AI clients discover and use.

---

## MCP Primitives

| Primitive | What to build | Section |
|-----------|---------------|---------|
| **Tools** | Callable functions (query execution, DDL operations…) | [Tools](tools/index.md) |
| **Resources** | Readable context (schemas, table lists, metadata…) | [Resources](resources/index.md) |
| **Prompts** | Reusable prompt templates for common AI workflows | [Prompts](prompts/index.md) |
| **Plugins** | Self-contained modules that bundle all three primitives | [Plugins](plugins/index.md) |

---

## Development Workflow

```
1. Create a plugin module
       └── plugin.py          ← registers your plugin with the server

2. Implement features
       ├── features/tools.py       ← define MCP tools
       ├── features/resources.py   ← define MCP resources
       └── features/prompts.py     ← define MCP prompt templates

3. Register & test
       └── Run the server with your plugin and connect an MCP client
```

---

## Quick Example

```python
# my_plugin/plugin.py
from actian_mcp_server.server_interfaces import MCPPlugin

class MyPlugin(MCPPlugin):
    name = "my_plugin"

    def register(self, server):
        from .features.tools import register_tools
        from .features.resources import register_resources
        from .features.prompts import register_prompts

        register_tools(server)
        register_resources(server)
        register_prompts(server)
```

---

## Next Steps

- [Tools](tools/index.md) — Create callable tools
- [Resources](resources/index.md) — Expose readable data resources
- [Prompts](prompts/index.md) — Define prompt templates
- [Plugins](plugins/index.md) — Bundle everything into a plugin
