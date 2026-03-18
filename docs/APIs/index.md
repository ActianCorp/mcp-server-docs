---
title: API Reference
description: Complete reference for the Actian MCP Server Python API — server interfaces, plugin base classes, and built-in tools.
---

# API Reference

This section provides a complete reference for the Actian MCP Server's public Python API.

---

## Server

### `ActianMCPServer`

The main server class. Loads plugins and starts the MCP transport.

```python
from actian_mcp_server.server import ActianMCPServer

server = ActianMCPServer(
    config_path="conf.json",      # path to JSON config file
    plugins=[...]                  # optional: list of plugin instances
)
server.run()
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `config_path` | `str` | Path to the JSON configuration file |
| `plugins` | `list[MCPPlugin]` | Plugin instances to load (merged with config) |

---

## Plugin Interface

### `MCPPlugin`

Base class for all plugins. Subclass this and implement `register()`.

```python
from actian_mcp_server.server_interfaces import MCPPlugin

class MyPlugin(MCPPlugin):
    name: str = "my_plugin"          # required: unique plugin name
    version: str = "1.0.0"           # optional: plugin version

    def register(self, server) -> None:
        """Register tools, resources, and prompts with the server."""
        ...
```

| Attribute | Required | Description |
|-----------|----------|-------------|
| `name` | Yes | Unique plugin identifier |
| `version` | No | Plugin version string |

| Method | Description |
|--------|-------------|
| `register(server)` | Called at server startup. Register all MCP primitives here. |

---

## Built-in Tools

### Zen Plugin Tools

| Tool name | Parameters | Description |
|-----------|------------|-------------|
| `execute_query` | `query: str`, `limit?: int` | Execute a SELECT query |
| `execute_statement` | `statement: str` | Execute a DDL/DML statement |
| `list_tables` | — | List all tables in the active schema |
| `describe_table` | `table_name: str` | Get column definitions for a table |
| `get_schema` | — | Return full schema as JSON |

### Analytics Engine Plugin Tools

| Tool name | Parameters | Description |
|-----------|------------|-------------|
| `execute_query` | `query: str`, `limit?: int` | Execute an analytical SQL query |
| `list_datasets` | — | List available datasets |
| `describe_dataset` | `dataset_name: str` | Get dataset metadata |

---

## Built-in Resources

### Zen Plugin Resources

| URI | MIME Type | Description |
|-----|-----------|-------------|
| `actian://zen/schema/tables` | `application/json` | All table names |
| `actian://zen/schema/columns/{table}` | `application/json` | Column info for `{table}` |
| `actian://zen/schema/full` | `application/json` | Full schema |
| `actian://zen/server/info` | `application/json` | Connection metadata |

---

## Built-in Prompts

| Prompt name | Arguments | Description |
|-------------|-----------|-------------|
| `analyze_table` | `table_name: str` | Analyze structure and suggest queries |
| `generate_report` | `query: str` | Narrate query results in plain language |
| `optimize_query` | `query: str` | Review and improve a SQL query |
| `data_quality_check` | `table_name: str` | Audit table for data quality issues |

---

## Server Utilities

### `server_utils`

Common utilities available to plugin authors.

```python
from actian_mcp_server.server_utils import (
    format_query_results,    # Convert DB rows to JSON-serialisable list
    validate_read_only,      # Raise if server is in read-only mode
    get_tenant_id,           # Extract tenant ID from request context
)
```

---

## OAuth

### `oauth.verify_token(token: str) -> dict`

Verifies a JWT bearer token against the configured JWKS endpoint.

```python
from actian_mcp_server.oauth import verify_token

claims = verify_token(token)   # raises if invalid
user_id = claims["sub"]
```
