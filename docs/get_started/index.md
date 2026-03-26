---
title: Get Started
description: Install, configure, and run the Actian Zen MCP Server.
---

# Get Started

Get the Actian Zen MCP Server running in your environment.

---

## Prerequisites

- **Python 3.12+** and **uv** package manager
- **Actian Zen** engine running with ODBC configured
- An MCP-compatible AI client (Claude Desktop, Cursor, VS Code)

Verify:

```bash
python --version   # 3.12 or later
uv --version
```

---

## Installation

```bash
git clone https://alm.actian.com/bitbucket/scm/~alokaj/actian_mcp_server.git
cd actian_mcp_server
uv sync
```

---

## Quick Configuration

Create `zen_config.json` in the project root:

```json
{
    "database": "DEMODATA",
    "readonly": true,
    "transport": "stdio"
}
```

Or use a DSN name directly via CLI:

```bash
uv run actian-mcp-server --dbms zen --dsn DEMODATA
```

---

## Start the Server

### stdio (for IDE integration)

```bash
uv run actian-mcp-server --dbms zen --transport stdio
```

### HTTP (for container / remote access)

```bash
uv run actian-mcp-server --dbms zen --transport streamable-http
```

Server listens on `http://localhost:8000/mcp`.

---

## Connect to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
    "mcpServers": {
        "actian-zen": {
            "command": "uv",
            "args": ["run", "actian-mcp-server", "--dbms", "zen", "--dsn", "DEMODATA"]
        }
    }
}
```

Restart Claude Desktop.

---

## Connect to Cursor / VS Code

For stdio (local):

```json
{
    "mcpServers": {
        "actian-zen": {
            "command": "uv",
            "args": ["run", "actian-mcp-server", "--dbms", "zen", "--dsn", "DEMODATA"]
        }
    }
}
```

For container (HTTP):

```json
{
    "mcpServers": {
        "actian-zen": {
            "url": "http://localhost:8000/mcp"
        }
    }
}
```

---

## Test the Connection

```bash
uv run actian-mcp-server --dbms zen --dsn DEMODATA --transport stdio
```

You should see:

```
INFO  Schema summary injected into server instructions
INFO  Uvicorn running on http://0.0.0.0:8000
```

---

## Next Steps

- [Configuration](../configuration/index.md) — Connection options, readonly mode, CLI arguments
- [Deployment](../deployment/index.md) — Podman container deployment
- [Testing](../testing/index.md) — QA test plan and results
- [Develop with MCP](../develop_with_mcp/index.md) — Build custom tools and plugins
