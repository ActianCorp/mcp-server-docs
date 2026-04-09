---
title: Connecting to MCP Clients
description: Connect MCP-compatible clients to a running Actian MCP Server instance.
---

# Connecting to MCP Clients

Once the Actian MCP Server is running in a container, MCP-compatible clients can connect to it over the configured network transport.

The server inside the container runs in **HTTP** transport mode, and clients connect to the server endpoint exposed by the container.

## Connection URL Format

- Local deployment: `http://localhost:<port>/mcp`
- Remote deployment: `http://<hostname>:<port>/mcp`

The standard endpoint used for the server deployment is `/mcp`.

=== ":material-brain: Claude Desktop"

    Add the following server entry to `claude_desktop_config.json`:

    ```json
    {
        "mcpServers": {
            "actian-mcp-server": {
                "url": "http://localhost:<port>/mcp"
            }
        }
    }
    ```

    For a remote deployment, replace `localhost` and `<port>` with the public host and port of the Actian MCP Server.

=== ":material-cursor-default-click: Cursor"

    Add the following server entry to `~/.cursor/mcp.json`:

    ```json
    {
        "mcpServers": {
            "actian-mcp-server": {
                "url": "http://localhost:<port>/mcp"
            }
        }
    }
    ```

    For a remote deployment, replace `localhost` and `<port>` with the public host and port of the Actian MCP Server.

=== ":material-lightning-bolt: fast-agent"

    Add the following server entry to `fastagent.config.yaml`:

    ```yaml
    mcp:
        servers:
            actian-mcp-server:
                url: "http://localhost:<port>/mcp"
    ```

=== ":material-code-braces: Codex"

    Add the following server entry to `~/.codex/config.toml`:

    ```toml
    [mcp_servers.actian-mcp-server]
    url = "http://localhost:<port>/mcp"
    ```

    For a remote deployment, replace `localhost` and `<port>` with the public host and port of the Actian MCP Server.

## Python Client

The following example demonstrates how to connect to a running Actian MCP Server instance using the [FastMCP](https://pypi.org/project/fastmcp/) Python client. It works with any supported database plugin (Ingres, Analytics Engine, HCL Informix®, or Zen).

### Prerequisites

Install the required package:

```bash
pip install fastmcp
```

For the OAuth example, also install `httpx`:

```bash
pip install httpx
```

### Parameter Differences by Plugin

Most tools share the same interface, but parameter names differ slightly between plugins:

| Tool | Ingres / Analytics Engine / HCL Informix® | Zen |
|------|--------------------------------------|-----|
| `execute_query` | `query` | `sql` |
| `describe_table` | `table_name` | `table` |

The following examples use the Ingres / Analytics Engine / HCL Informix® parameter names. For Zen, substitute the parameter names from the table above.

### Basic Usage

```python
"""Actian MCP Server — Python client example."""

import asyncio
import json
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def main():
    # Replace with your Actian MCP Server URL
    server_url = "http://localhost:8000/mcp"

    transport = StreamableHttpTransport(url=server_url)

    async with Client(transport, timeout=60) as client:

        # 1. Discover available tools and their parameters
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools:
            print(f"  - {tool.name}")

        # Print parameter schema for a specific tool
        for tool in tools:
            if tool.name == "execute_query":
                print(f"\nexecute_query parameters:")
                print(json.dumps(tool.model_dump()["parameters"], indent=2))

        # 2. List tables in the connected database
        result = await client.call_tool("list_tables", {})
        print(f"\nTables:\n{result.content[0].text}")

        # 3. Describe a specific table
        # Replace "customers" with a table from your database
        # For Zen, use {"table": "customers"} instead
        result = await client.call_tool(
            "describe_table", {"table_name": "customers"}
        )
        print(f"\nTable structure:\n{result.content[0].text}")

        # 4. Execute a read-only SQL query
        # Replace table and column names to match your schema
        # For Zen, use {"sql": "..."} instead of {"query": "..."}
        result = await client.call_tool(
            "execute_query",
            {"query": "SELECT name, email FROM customers WHERE status = 'active'"},
        )
        print(f"\nQuery results:\n{result.content[0].text}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
```

### Connecting with OAuth Authentication

When the server is deployed with OAuth enabled over HTTPS, provide authentication and SSL parameters:

```python
"""Actian MCP Server — Python client with OAuth and TLS."""

import asyncio
import ssl
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
import httpx


async def main():
    server_url = "https://mcp.example.com:8000/mcp"

    # Trust a self-signed certificate (omit for publicly trusted certs)
    ssl_ctx = ssl.create_default_context(cafile="/path/to/server.crt")

    transport = StreamableHttpTransport(
        url=server_url,
        auth="oauth",
        httpx_client_factory=lambda **kwargs: httpx.AsyncClient(
            verify=ssl_ctx, **kwargs
        ),
    )

    async with Client(transport, timeout=120) as client:
        tools = await client.list_tools()
        print(f"Connected — {len(tools)} tools available")

        # Verify the authenticated database user
        # For Zen, use {"sql": "..."} instead of {"query": "..."}
        result = await client.call_tool(
            "execute_query", {"query": "SELECT CURRENT_USER"}
        )
        print(f"Current user: {result.content[0].text}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
```

!!! tip
    When using OAuth, the FastMCP client automatically handles the browser-based login flow. Ensure a browser is available on the machine running the client.

## Connection Notes

- Use the port configured for the MCP Server container.
- For production deployments, prefer **HTTPS** and configure authentication when you expose the server outside a trusted local environment.
- When OAuth is enabled on a non-localhost deployment, the server requires **TLS** and a public `https://` base URL.
  For certificate generation, Docker setup, and trusting self-signed certificates in MCP clients, see [HTTPS / TLS for remote deployments](../authentication/index.md#https-tls-for-remote-deployments).

