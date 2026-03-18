---
title: Plugins
description: Build a self-contained plugin that bundles tools, resources, and prompts for any Actian data source.
---

# Plugins

A **plugin** is the top-level unit of extension in the Actian MCP Server. It bundles tools, resources, and prompts into a self-contained module that the server loads at startup.

Actian ships two first-party plugins:

| Plugin | Data Source |
|--------|-------------|
| **Zen Plugin** | Actian Zen embedded relational database |
| **Analytics Engine Plugin** | Actian Analytics Engine (columnar analytics) |

---

## Plugin Structure

A plugin follows this layout:

```
my_plugin/
├── __init__.py
├── plugin.py              ← Entry point — registers the plugin
├── core/
│   ├── connection.py      ← Database connection management
│   └── config.py          ← Plugin configuration
└── features/
    ├── tools.py           ← MCP tool definitions
    ├── resources.py       ← MCP resource definitions
    └── prompts.py         ← MCP prompt definitions
```

---

## Creating a Plugin

### 1. Implement the plugin entry point

```python
# my_plugin/plugin.py
from actian_mcp_server.server_interfaces import MCPPlugin

class MyPlugin(MCPPlugin):
    """Plugin for MyDatabase."""

    name = "my_plugin"           # unique plugin identifier
    version = "1.0.0"

    def register(self, server):
        """Called once at server startup to register all MCP primitives."""
        from .features.tools import register_tools
        from .features.resources import register_resources
        from .features.prompts import register_prompts

        register_tools(server)
        register_resources(server)
        register_prompts(server)
```

### 2. Implement features

Create `features/tools.py`, `features/resources.py`, and `features/prompts.py`.  
See the [Tools](tools/index.md), [Resources](resources/index.md), and [Prompts](prompts/index.md) sections for details.

### 3. Register the plugin

Add your plugin to the server configuration:

```json
{
  "plugins": [
    "my_plugin.plugin.MyPlugin"
  ]
}
```

Or pass it programmatically:

```python
from actian_mcp_server.server import ActianMCPServer
from my_plugin.plugin import MyPlugin

server = ActianMCPServer(plugins=[MyPlugin()])
server.run()
```

---

## Plugin Lifecycle

```
Server starts
    └── Plugin.register(server) is called
            ├── Tools registered via @server.list_tools / @server.call_tool
            ├── Resources registered via @server.list_resources / @server.read_resource
            └── Prompts registered via @server.list_prompts / @server.get_prompt

AI Client connects
    └── Discovers tools, resources, and prompts from all loaded plugins

AI Client makes a request
    └── Server routes to the correct plugin handler
```

---

## Multi-tenancy

Plugins can support multiple tenants by scoping connections per request context:

```python
async def call_tool(name: str, arguments: dict, context: dict):
    tenant_id = context.get("tenant_id")
    connection = get_connection_for_tenant(tenant_id)
    # ... use connection ...
```

See [Configuration](../../configuration/index.md) for multi-tenant setup.

---

## Reference Plugins

Study the first-party implementations for patterns:

- [`zen/plugin.py`](../../APIs/index.md) — Actian Zen plugin
- [`analytics_engine/plugin.py`](../../APIs/index.md) — Analytics Engine plugin
