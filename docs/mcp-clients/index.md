---
title: Connecting MCP Clients
description: Connect MCP-compatible clients to a running Actian MCP Server instance.
---

# Connect AI Clients to Actian MCP Server

After you deploy the Actian MCP Server container, you can connect to the MCP-compatible artificial intelligence (AI) clients. The server uses HTTP transport mode, and clients can connect directly to the endpoint exposed by the container.

## Connection URL Formats

Identify the deployment type to determine the connection URL. The standard endpoint path used for the server deployment is `/mcp`.

- Local deployment: `http://localhost:<port>/mcp`
- Remote deployment: `http://<hostname>:<port>/mcp`

#### Client Configuration Examples

You can connect to popular AI clients like Claude Desktop, Cursor, fast-agent, and Codex using the connection URL.

=== ":material-brain: Claude Desktop"

    ### Connecting Claude Desktop to the Actian MCP Server

    Claude Desktop connects to the Actian MCP Server via the `mcp-remote` bridge. This connection requires Node.js (version 18 or later) to be installed on the local machine.

    #### Prerequisites

    Before starting the connection, ensure the following requirements are met:

    - **Node.js:** Version 18 or higher.
    - **Actian MCP Server:** Running and accessible over the network.

    #### Configuration

    1. Open the Claude Desktop configuration file located at the following path:
        - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
        - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
    2. Add the following entry under the `mcpServers` section and replace the placeholder URL with the specific server address:

        ```json
        "actian-mcp-server": {
          "command": "npx",
          "args": [
            "mcp-remote",
            "https://<your-server-host>:<port>/mcp"
            "--allow-http"
          ]
        }
        ```

        !!! note
            If the server utilizes a self-signed TLS certificate, include the `env` block shown below to bypass certificate verification:

            ```json
            "actian-mcp-server": {
              "command": "npx",
              "args": [
                "mcp-remote",
                "https://<your-server-host>:<port>/mcp"
                "--allow-http"
              ],
              "env": {
                "NODE_TLS_REJECT_UNAUTHORIZED": "0"
              }
            }
            ```

    3. Save the file and restart Claude Desktop. The Actian MCP Server appears as an available tool within the conversations.

=== ":material-cursor-default-click: Cursor"

    To connect Cursor, add the following server entry to the `~/.cursor/mcp.json` file:

    ```json
    {
        "mcpServers": {
            "actian-mcp-server": {
                "url": "http://localhost:<port>/mcp"
            }
        }
    }
    ```

    For a remote deployment, replace `localhost` and `<port>` with the public hostname and port of the Actian MCP Server.

=== ":material-lightning-bolt: fast-agent"

    To connect fast-agent, add the following server entry to the `fastagent.config.yaml` file:

    ```yaml
    mcp:
        servers:
            actian-mcp-server:
                url: "http://localhost:<port>/mcp"
    ```

=== ":material-code-braces: Codex"

    To connect Codex, add the following server entry to the `~/.codex/config.toml` file:

    ```toml
    [mcp_servers.actian-mcp-server]
    url = "http://localhost:<port>/mcp"
    ```

    For a remote deployment, replace `localhost` and `<port>` with the public hostname and port of the Actian MCP Server.

## Connect Using Python Client

!!! warning "Actian NoSQL"
    Actian NoSQL uses different tools (JPQL-based queries, LOID fetches, etc) and a different authentication model. For a NoSQL-specific Python client example, see [Connect Using a Python Client](../nosql/index.md#connect-using-a-python-client).

This section demonstrates how to connect to a running Actian MCP Server instance using the [FastMCP](https://pypi.org/project/fastmcp/) Python client. This approach supports all database plugins (Ingres, HCL Informix®, Zen, and Analytics Engine).

### Prerequisites


1. Install the required FastMCP package:

    ```bash
    pip install fastmcp
    ```

2. To use OAuth authentication, install the `HTTPX` library:

    ```bash
    pip install httpx
    ```

### Parameter Naming Differences

Most tools share the same interface across databases and the parameter names may vary depending on the specific plugin.

| Tool | Product | Parameter |
|------|---------|-----------|
| `execute_query` | Ingres / Analytics Engine / HCL Informix® | `query` |
| `execute_query` | Zen | `sql` |
| `describe_table` | Ingres / Analytics Engine / HCL Informix® | `table_name` |
| `describe_table` | Zen | `table` |

The following examples use the Ingres, Analytics Engine, and HCL Informix® parameter names. For Zen, substitute the parameter names from the table above.

### Basic Connection Example

The following Python script demonstrates a standard connection:

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

### Connect Using OAuth Authentication

When you deploy the server with OAuth enabled over HTTPS, provide authentication and TLS/SSL parameters in the client code:

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
    When you use OAuth, the FastMCP client automatically handles the browser-based login flow. Ensure you run the client on a machine that has a web browser.

## Deployment Considerations

Review the following guidelines to ensure a stable and secure connection:

- **Port mapping:** Always connect using the specific port configured for the MCP Server container.
- **Production security:** Enforce HTTPS and configure authentication whenever you expose the server outside a trusted local environment.
- **Remote deployments:** If you enable OAuth on a non-localhost deployment, the server requires TLS and a public `https://` base URL. For detailed instructions on generating certificates, configuring Docker, and trusting self-signed certificates, see [HTTPS / TLS for remote deployments](../authentication/index.md#https-tls-for-remote-deployments).
