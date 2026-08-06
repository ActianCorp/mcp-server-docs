---
title: Python Client
description: Connect to the Actian MCP Server from Python with the FastMCP client.
---

# Connect a Python client

The [FastMCP](https://pypi.org/project/fastmcp/) Python client talks to any Actian MCP
Server. Use it to script against the server, to test a deployment, or to build your own
agent instead of using a desktop AI client.

The connection itself is the same for every database. What differs is the port the server
listens on and the tools it exposes, so pick your database in the tabs below.

## Prerequisites

Install the client:

```bash
pip install fastmcp
```

OAuth authentication additionally needs `httpx` and `certifi`:

```bash
pip install httpx certifi
```

## Tool and parameter names

The SQL engines expose the same tools, but two parameter names differ on Zen:

| Tool | Ingres / HCL Informix® / Analytics Engine | Zen |
|------|------------------------------------------|-----|
| `execute_query` | `query` | `sql` |
| `describe_table` | `table_name` | `table` |

The examples below use the Ingres, HCL Informix® and Analytics Engine names. For Zen,
substitute from this table.

Actian NoSQL exposes a different set of tools entirely — `list_classes`,
`describe_class`, LOID lookups, and JPQL queries. See
[NoSQL tools](../nosql/tools/index.md).

## Connect to the server

=== "SQL databases"

    ```python
    """Actian MCP Server — Python client example."""

    import asyncio
    import json
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport


    async def main():
        server_url = "http://localhost:8000/mcp"

        transport = StreamableHttpTransport(url=server_url)

        async with Client(transport, timeout=60) as client:

            # 1. Discover available tools and their parameters
            tools = await client.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}")

            # 2. List the tables in the database
            result = await client.call_tool("list_tables", {})
            print(f"\nTables:\n{json.dumps(result.structured_content, indent=2)}")

            # 3. Run a read-only query
            result = await client.call_tool(
                "execute_query", {"query": "SELECT CURRENT_USER"}
            )
            print(f"\nCurrent user:\n{json.dumps(result.structured_content, indent=2)}")


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")
    ```

=== "Actian NoSQL"

    ```python
    """Actian MCP Server for Actian NoSQL — Python client example."""

    import asyncio
    import json
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport


    async def main():
        server_url = "http://localhost:8080/mcp"

        transport = StreamableHttpTransport(url=server_url)

        async with Client(transport, timeout=60) as client:

            # 1. Discover available tools and their parameters
            tools = await client.list_tools()
            print("Available tools:")
            for tool in tools:
                print(f"  - {tool.name}")

            # 2. List all classes in the database
            result = await client.call_tool("list_classes", {})
            print(f"\nClasses:\n{json.dumps(result.structured_content, indent=2)}")

            # 3. Describe a specific class
            # Replace "Employee" with a class name from your database
            result = await client.call_tool(
                "describe_class", {"className": "Employee"}
            )
            print(f"\nEmployee class schema:\n{json.dumps(result.structured_content, indent=2)}")

            # 4. Execute a read-only JPQL query
            # Replace class and field names to match your schema
            result = await client.call_tool(
                "execute_query",
                {"jpql": "select e from Employee e"},
            )
            print(f"\nQuery results:\n{json.dumps(result.structured_content, indent=2)}")


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")
    ```

## Connect with OAuth

When the server runs with OAuth enabled over HTTPS, the client needs both the
authentication flow and a TLS context.

!!! warning "Trust both certificate sources"
    If the MCP server uses a self-signed certificate, do **not** pass it as
    `ssl.create_default_context(cafile=…)`. That *replaces* the trust store, so requests to
    your identity provider — which uses a public certificate authority — then fail
    verification. Start from `certifi.where()` and add the self-signed certificate with
    `load_verify_locations()`, as both examples below do.

=== "SQL databases"

    ```python
    """Actian MCP Server — Python client with OAuth and TLS."""

    import asyncio
    import ssl
    import httpx
    import certifi
    from fastmcp import Client
    from fastmcp.client.transports import StreamableHttpTransport


    # Replace with your values
    MCP_URL = "https://mcp.example.com:8000/mcp"
    CA_CERT = "/path/to/server.crt"   # self-signed certificate of the MCP server


    def make_httpx_client(**kwargs) -> httpx.AsyncClient:
        """Trust both the identity provider and the MCP server certificate."""
        # Public certificate authorities, for the identity provider
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        # Plus the server's own certificate
        ssl_ctx.load_verify_locations(cafile=CA_CERT)
        return httpx.AsyncClient(verify=ssl_ctx, **kwargs)


    async def main():
        transport = StreamableHttpTransport(
            url=MCP_URL,
            auth="oauth",
            httpx_client_factory=make_httpx_client,
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

=== "Actian NoSQL"

    ```python
    """Actian MCP Server for Actian NoSQL — Python client with OAuth and TLS."""

    import asyncio
    import json
    import ssl
    import httpx
    import certifi
    from fastmcp import Client
    from fastmcp.client.auth import OAuth
    from fastmcp.client.transports import StreamableHttpTransport


    # Replace with your values
    MCP_URL = "https://mcp.example.com:8443/mcp"
    CLIENT_ID = "<your-client-id>"    # OAuth 2.0 client ID registered in your identity provider
    CALLBACK_PORT = 8765              # must match the redirect URI registered in your identity provider
    CA_CERT = "/path/to/server.crt"   # self-signed certificate of the MCP server


    def make_httpx_client(**kwargs) -> httpx.AsyncClient:
        """Trust both the identity provider and the MCP server certificate."""
        # Public certificate authorities, for the identity provider
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        # Plus the server's own certificate
        ssl_ctx.load_verify_locations(cafile=CA_CERT)
        return httpx.AsyncClient(verify=ssl_ctx, **kwargs)


    async def main():
        oauth = OAuth(
            client_id=CLIENT_ID,
            callback_port=CALLBACK_PORT,
            httpx_client_factory=make_httpx_client,
        )

        transport = StreamableHttpTransport(
            url=MCP_URL,
            auth=oauth,
            httpx_client_factory=make_httpx_client,
        )

        async with Client(transport, timeout=120) as client:
            tools = await client.list_tools()
            print(f"Connected — {len(tools)} tools available")

            result = await client.call_tool(
                "execute_query",
                {"jpql": "select e from Employee e"},
            )
            print(f"Results:\n{json.dumps(result.structured_content, indent=2)}")


    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            print(f"Error: {e}")
    ```

!!! tip
    The FastMCP OAuth flow opens a browser window for login. Run the client on a machine
    that has a browser available.

## Next steps

<div class="grid cards" markdown>

- :material-connection: **[Connect an AI client](index.md)**  
  Configuration for Claude Desktop, Cursor, GitHub Copilot, Codex, and fast-agent.

- :material-shield-check: **[Secure the server](../authentication/index.md)**  
  Set up OAuth 2.0 with Keycloak or Auth0.

</div>
