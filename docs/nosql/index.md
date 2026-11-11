---
title: Actian NoSQL Database
description: Use the Actian MCP Server to connect MCP clients to Actian NoSQL Databases for schema discovery, read-only JPQL queries, optional write support, and custom Java extensions.
---

# Actian MCP Server for NoSQL

Connect your MCP-compatible client to Actian NoSQL Database using the Actian MCP Server. Once configured, clients can explore schema metadata, execute read-only JPQL queries, and inspect the full details of retrieved persistent objects. Object writes and custom Java extensions are also available, both turned off until an operator enables them.

## Capabilities

The Actian NoSQL MCP Server supports the following operations:

| Action | Description |
|--------|-------------|
| **Discover the Schema** | List all classes and explore their fields and inheritance hierarchy. |
| **Run JPQL queries** | Execute read-only queries against your database. |
| **Retrieve objects by ID** | Fetch one or many objects directly by LOID for the fastest retrieval path. |
| **Serve several databases** | Serve several NoSQL databases from one MCP server through named targets that clients reach at `/mcp/{target}`. See [Targets](targets/index.md). |
| **Write data** | Create, update, and delete objects, when write support is enabled. |
| **Extend the server** | Add custom tools, resources, and prompts with a Java extension JAR. |

### Targets

One MCP server can serve several NoSQL databases through named targets. A client works with a target's database at `/mcp/{target}`, while plain `/mcp` offers only `list_accessible_targets`, which lists the targets the caller can reach. Targets defined in a directory can be added, changed, and removed while the server runs. With authentication enabled, each target has its own read and write scopes.

[Targets](targets/index.md) covers targets, names, and what an agent sees, [Changing Targets Without a Restart](targets/without-restart.md) covers the targets directory, and [Scopes](authentication/scopes.md) covers the per-target scopes.

### Write Support

The server is read-only until writes are turned on. Once they are, tools for creating, updating, and deleting objects join the read-only ones, each running as a single all-or-nothing transaction. Every call then passes [three independent checks](write-support.md#what-each-call-must-clear): writes must be on, the caller's token must carry the write scope of the mode when authentication is enabled (`mcp:write` without targets, the target's own write scope with targets), and a person must approve the operation in the connected client.

[Write support](write-support.md) covers all three, plus [why the write tools may be missing from a client's tool list](write-support.md#missing-write-tools) and how object versions stop one client overwriting another's change.

### Extensions

An extension is a Java JAR that adds custom tools, resources, resource templates, and prompts to a running server — no fork, and no rebuild of the product. The server loads only the JARs an operator has declared in an allowlist, with each one's SHA-256 digest pinned by default. An extension's write tools pass the same checks the built-in ones do.

With targets, an extension can be offered at some targets only: see [Limiting an Extension to Some Targets](extensions/index.md#limiting-an-extension-to-some-targets).

[Extensions](extensions/index.md) covers authoring, the Extension SDK, deployment, and the trust model.

## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker installed and running on the host machine.
- **Database credentials:** Access details for the Actian NoSQL Database.
- **Secure deployment files (Optional):** TLS certificate and key files for secure deployments.
- **OIDC provider (Optional):** Required if you are using OAuth authentication.

!!! note "Database compatibility"
    This version of the Actian NoSQL MCP Server requires Actian NoSQL Database 11. Earlier Actian NoSQL versions are not supported.

## Configuration

All configuration is provided through an `application.properties` file mounted into the container at `/home/jboss/config/application.properties`. Environment variables are supported as an alternative — any property can be passed with a `-e` flag using `SCREAMING_SNAKE_CASE` notation, and they take precedence over the file.

### Actian NoSQL Properties

Set either `nsql.connectionURL` or targets, never both. The server does not start with both, or with neither. See [Choosing a Mode](targets/index.md#choosing-a-mode).

#### Without Targets

| Property | Default | Description |
|----------|---------|-------------|
| `nsql.connectionURL` | `None` | Required in this mode. Database connection URL in the format `database@host[:port][#user[:password]]`. The port, the user, and the password are optional. The distributed form `database@host|database@host` is not supported. See [Distributed Databases](limits.md#distributed-databases). |
| `nsql.db.connect-on-startup` | `true` | This mode only: whether the database is opened while the server starts. It has no effect when targets are configured. See [Starting with a Database Down](database-availability.md#starting-with-a-database-down). |

#### With Targets

The `nsql.targets[i]` entries are read once at startup. The files of `nsql.targets.dir` are read again at the reload interval, so a change to them needs no restart.

| Property | Default | Description |
|----------|---------|-------------|
| `nsql.targets[i].name` | `None` | The name of target `i`, which clients use in the path `/mcp/{name}`. Required for each target. See [Choosing a Mode](targets/index.md#choosing-a-mode). |
| `nsql.targets[i].connectionURL` | `None` | The connection URL of the database of target `i`, in the format `database@host[:port][#user[:password]]`. Required for each target, and the host is required. See [Target Names and Connection URLs](targets/index.md#target-names-and-connection-urls). |
| `nsql.targets.dir` | `None` | A directory of `*.properties` files, one target per file. Setting it selects this mode by itself. See [Targets Directory](targets/without-restart.md#targets-directory). |
| `nsql.targets.reload-interval` | `10s` | How often the directory is read again. `0` reads it once at startup. See [Targets Directory](targets/without-restart.md#targets-directory). |

#### Both Modes

| Property | Default | Description |
|----------|---------|-------------|
| `nsql.writes.enabled` | `false` | Turns on the write tools, which are otherwise unavailable. See [Write support](write-support.md#configuration-reference) for the batch ceiling and the two confirmation settings. |
| `nsql.extensions.enabled` | `false` | Turns on loading of declared Java extension JARs. See [Extensions](extensions/index.md#enabling-and-declaring-extensions) for the allowlist, digest pinning, and load order. |
| `nsql.db.max-calls` | `10` | Most calls in flight per database. `0` means no cap. See [Properties](database-availability.md#properties). |
| `nsql.db.call-deadline` | `30s` | Longest a read call may take. `0` means no deadline. See [Properties](database-availability.md#properties). |
| `nsql.db.connect-timeout` | `10s` | Longest the network connect to the NoSQL server may take. See [Properties](database-availability.md#properties). |
| `nsql.db.idle-timeout` | `10m` | Time without a call after which a database's connection pool is closed. `0` never closes it. See [Properties](database-availability.md#properties). |

For how these limits protect the server when a database is busy, slow, or down, see [Database Availability](database-availability.md).

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

With targets, console lines carry the target name. If you change `quarkus.log.console.format`, keep `%X{target}` before the message. See [Log Lines](targets/index.md#log-lines).

## Start the Server

Add settings to `application.properties` and mount it into the container:

```properties
nsql.connectionURL=<connection-url>
```

```bash
docker run \
  -v $(pwd)/application.properties:/home/jboss/config/application.properties:ro \
  -p 8080:8080 \
  actian/nsql-mcp-server:1.2.0
```

Once the container is running, connect the MCP client to the exposed MCP server endpoint using the host and port from the configuration.

---

## Connect Using a Python Client

!!! note "Other MCP clients"
    For connecting AI clients such as Claude Desktop, Cursor, fast-agent, and Codex, see the [Connecting MCP Clients](../mcp-clients/index.md) guide.

The following example demonstrates how to connect to a running Actian MCP Server for Actian NoSQL using the [FastMCP](https://pypi.org/project/fastmcp/) Python client.

Both examples below perform reads only. To write, the client must also be able to answer the server's confirmation prompt, which it can do only if you give it an elicitation handler — see [Answering the prompt from a Python client](write-support.md#answering-the-prompt-from-a-python-client).

### Client Prerequisites

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

- :material-pencil: **[Write support](write-support.md)**  
  Enable object writes, and what gates each one.

- :material-lock: **[Authentication](authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for NoSQL database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn more about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Use pre-built prompt templates for common workflows.

- :material-puzzle: **[Extensions](extensions/index.md)**  
  Add custom tools, resources, and prompts with a Java extension JAR.

- :material-database: **[Targets](targets/index.md)**  
  Serve several databases through named targets from one MCP server.

- :material-database-cog: **[Database Availability](database-availability.md)**  
  Limits on calls and connections, idle connections, and recovery when a database is down.

</div>
