---
title: Get Started
description: Install, configure, and run your first Actian MCP Server in minutes.
---

# Get Started

Get the Actian MCP Server running in your environment quickly.

---

## Prerequisites

- **Python 3.10+**
- Access to an **Actian Zen** database or **Actian Analytics Engine**
- An MCP-compatible AI client (Claude Desktop, Cursor, or any MCP client)

Verify Python:

```bash
python --version   # 3.10 or later
pip --version
```

---

## Installation

```bash
pip install actian-mcp-server
```

Verify the installation:

```bash
actian-mcp-server --version
```

---

## Quick Configuration

Create a `conf.json` file:

```json
{
  "server": {
    "name": "actian-mcp-server",
    "transport": "stdio"
  },
  "plugins": [
    "actian_mcp_server.zen.plugin.ZenPlugin"
  ],
  "zen": {
    "dsn": "MyDatabase",
    "host": "localhost",
    "port": 1583,
    "username": "admin",
    "password": "yourpassword"
  }
}
```

---

## Connect to Claude Desktop

Add the server to Claude Desktop's config at  
`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "actian": {
      "command": "actian-mcp-server",
      "args": ["--config", "/path/to/conf.json"]
    }
  }
}
```

Restart Claude Desktop. You should see the Actian MCP tools available.

---

## Connect to Cursor

In Cursor settings, add under **MCP Servers**:

```json
{
  "actian": {
    "command": "actian-mcp-server",
    "args": ["--config", "/path/to/conf.json"]
  }
}
```

---

## Test the Connection

Start the server manually to confirm it works:

```bash
actian-mcp-server --config conf.json --transport stdio
```

You should see:

```
INFO  Actian MCP Server 1.0.0 starting...
INFO  Loaded plugin: ZenPlugin
INFO  Server ready. Waiting for MCP client...
```

---

## Next Steps

- [Configuration](../configuration/index.md) — All server and plugin options
- [Develop with MCP](../develop_with_mcp/index.md) — Build custom tools and plugins
- [Deployment](../deployment/index.md) — Deploy with Docker or in production
