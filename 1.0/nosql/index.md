---
title: Actian NoSQL Database
description: Use the Actian MCP Server to connect MCP clients to Actian NoSQL Databases.
---

# Actian MCP Server for NoSQL

Connect your MCP-compatible client to Actian NoSQL using the Actian MCP Server. Once configured, clients can explore schema metadata, execute read-only JPQL queries, and inspect the full details of retrieved persistent objects.

## Capabilities

The Actian NoSQL MCP Server supports the following operations:

| Action | Description |
|--------|-------------|
| **Discover the Schema** | List all classes and explore their fields and inheritance hierarchy. |
| **Run JPQL queries** | Execute read-only queries against your database. |
| **Retrieve objects by ID** | Fetch one or many objects directly by LOID for the fastest retrieval path. |

## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker installed and running on the host machine.
- **Database credentials:** Access details for the Actian NoSQL database.
- **Secure deployment files (Optional):** TLS certificate and key files for secure deployments.
- **OIDC provider (Optional):** Required if you are using OAuth authentication.

## Configuration

All configuration is provided through an `application.properties` file mounted into the container at `/home/jboss/config/application.properties`. Environment variables are supported as an alternative — any property can be passed with a `-e` flag using `SCREAMING_SNAKE_CASE` notation, and they take precedence over the file.

### NoSQL Connection

| Property             | Required | Description                                                                                                              |
|----------------------|----------|--------------------------------------------------------------------------------------------------------------------------|
| `nsql.connectionURL` | Yes | Database connection URL in the format `database@server:port#user:password`. `port`, `user`, and `password` are optional. |

### Quarkus Properties

The server is a **Quarkus** application. Any standard Quarkus configuration property can be set in `application.properties`. Some commonly used properties:

| Property | Default | Description |
|----------|---------|-------------|
| `quarkus.http.port` | `8080` | HTTP listening port. |
| `quarkus.http.ssl-port` | `8443` | HTTPS listening port. |

!!! note "Securing the server"
    To enable OAuth 2.0 or TLS, additional properties are required. See [Authentication](authentication/index.md) for the full configuration reference.

#### Logging

The root log level is controlled by `quarkus.log.level` (default: `INFO`).

Available log levels:

| Level | Description |
|-------|-------------|
| `OFF` | A special level used in configuration to turn off logging. |
| `FATAL` | A critical service failure or total inability to handle any requests. |
| `ERROR` | A major issue in processing or an inability to complete a request. |
| `WARN` | A non-critical service error or problem that might not require immediate correction. |
| `INFO` | Service lifecycle events or other important infrequent information. |
| `DEBUG` | Additional information about lifecycle events or events not tied to specific requests, useful for debugging. |
| `TRACE` | Detailed per-request debugging information, potentially at a very high frequency. |
| `ALL` | A special level to turn on logging for all messages, including custom levels. |

Individual categories can be tuned independently using `quarkus.log.category."<package>".level`.
The following Actian-specific categories are available:

| Category | Description                                                                     |
|----------|---------------------------------------------------------------------------------|
| `com.actian` | All Actian components.                                                          |
| `com.actian.mcp` | MCP protocol layer — primitives, guardrails, and related handling. |
| `com.actian.nsql` | Actian NoSQL data layer — schema discovery, query execution, and object mapping. |

For example, to enable debug logging for the Actian NoSQL data layer:

```properties
quarkus.log.category."com.actian.nsql".level=DEBUG
```

See the [Quarkus logging guide](https://quarkus.io/guides/logging) for the full reference.

## Start the Server

Add settings to `application.properties` and mount it into the container:

```properties
nsql.connectionURL=<connection-url>
```

```bash
docker run \
  -v $(pwd)/application.properties:/home/jboss/config/application.properties:ro \
  -p 8080:8080 \
  actian/nsql-mcp-server:1.0.1
```

Once the container is running, connect the MCP client to the exposed server endpoint using the host and port from the configuration.

---

## Connect Using a Python Client

!!! note "Other MCP clients"
    For connecting AI clients such as Claude Desktop, Cursor, fast-agent, and Codex, see the [Connecting MCP Clients](../mcp-clients/index.md) guide.

The following example demonstrates how to connect to a running Actian MCP Server for Actian NoSQL using the [FastMCP](https://pypi.org/project/fastmcp/) Python client.

### Prerequisites

Install the required packages:

```bash
pip install fastmcp
pip install httpx  # required for OAuth authentication
```

### Basic Connection Example

```python
"""Actian MCP Server for Actian NoSQL — Python client example."""

import asyncio
import json
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def main():
    # Replace with your Actian MCP Server URL
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

### Connect Using OAuth Authentication

When you deploy the server with OAuth enabled over HTTPS, provide authentication and TLS/SSL parameters in the client code

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
CALLBACK_PORT = <callback-port>   # must match the redirect URI registered in your identity provider
CA_CERT = "/path/to/server.crt"  # self-signed certificate of the MCP server


def make_httpx_client(**kwargs) -> httpx.AsyncClient:
    """Create an HTTP client that trusts both the identity provider and the MCP server certificate."""
    # Load standard public certificates (for the identity provider)
    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    # Append the self-signed certificate (for the MCP server)
    ssl_ctx.load_verify_locations(cafile=CA_CERT)
    return httpx.AsyncClient(verify=ssl_ctx, **kwargs)


async def main():
    oauth = OAuth(
        client_id=CLIENT_ID,
        callback_port=CALLBACK_PORT,
        httpx_client_factory=make_httpx_client,  # used for identity provider requests
    )

    transport = StreamableHttpTransport(
        url=MCP_URL,
        auth=oauth,
        httpx_client_factory=make_httpx_client,  # used for MCP server requests
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
    The FastMCP `OAuth` helper automatically handles the browser-based login flow. Ensure you run the client on a machine with a web browser available.

---

## Next Steps

<div class="grid cards" markdown>

- :material-lock: **[Authentication](authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for NoSQL database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn more about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Use pre-built prompt templates for common workflows.

</div>
