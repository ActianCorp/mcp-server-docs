---
title: Connecting MCP Clients
description: Connect MCP clients to a running Actian MCP Server instance.
---

# Connect MCP Clients to the Actian MCP Server

After you deploy the Actian MCP Server container, you can connect an MCP client to it. The server uses HTTP transport mode, and the client connects directly to the endpoint that the container exposes.

## Connection URL Formats

Identify the deployment type to determine the connection URL. The standard endpoint path for the server is `/mcp`.

- Local deployment: `http://localhost:<port>/mcp`
- Remote deployment: `http://<hostname>:<port>/mcp`

## Elicitation Support for Write Approval

This section applies only when write support is enabled on the server. On a read-only server, every client in the following table behaves the same way.

When write support is enabled, the server asks a person to approve each write before it runs. The server sends that request through the Model Context Protocol (MCP) elicitation capability, which not every client implements.

| Client | Displays the write approval prompt |
|--------|------------------------------------|
| Claude Code | Yes |
| Claude Desktop | No |
| GitHub Copilot | No |
| Cursor, fast-agent, Codex | Not verified. Treat these clients as unsupported until you confirm elicitation support in your deployment. |

!!! warning "A client that cannot prompt cannot write"
    If the connected client does not support elicitation, no write goes through. The server never approves a write silently. Read queries are not affected.

    On the SQL databases, the server rejects the write in the same way as it rejects a write that a person declines. To let such a client write, set `write_confirmation` to `false` in `conf.json`. The server then runs writes without asking anyone first. For more information, see [Write support](../ingres/write-support.md#skipping-the-approval-prompt).

    On Actian NoSQL, the server does not offer the write tools to such a client at all. The tools are absent from the tool list, and a call to one of them fails as an unknown tool. For more information, see [Why the write tools may not appear](../nosql/write-support.md#missing-write-tools).

## Client Configuration Examples

You can connect MCP clients such as Claude Desktop, Cursor, fast-agent, and Codex using the connection URL.

=== ":material-brain: Claude Desktop"

    ### Connecting Claude Desktop to the Actian MCP Server

    Claude Desktop connects to the Actian MCP Server through the `mcp-remote` bridge. This connection requires Node.js version 18 or later on the local machine.

    #### Prerequisites

    Before starting the connection, ensure the following requirements are met:

    - **Node.js:** Version 18 or later.
    - **Actian MCP Server:** Running and accessible over the network.

    #### Configuration

    1. Open the Claude Desktop configuration file:
        - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
        - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
    2. Add the following entry under the `mcpServers` section:

        ```json
        "actian-mcp-server": {
          "command": "npx",
          "args": [
            "mcp-remote",
            "http://<your-server-host>:<port>/mcp",
            "--allow-http"
          ]
        }
        ```

    3. Replace the placeholder URL with the address of your server.

        !!! note
            If the server uses HTTPS with a self-signed TLS certificate, include the following `env` block to bypass certificate verification:

            ```json
            "actian-mcp-server": {
              "command": "npx",
              "args": [
                "mcp-remote",
                "https://<your-server-host>:<port>/mcp"
              ],
              "env": {
                "NODE_TLS_REJECT_UNAUTHORIZED": "0"
              }
            }
            ```

    4. Save the file and restart Claude Desktop. The Actian MCP Server then appears as an available tool in your conversations.

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

## Connect Using a Python Client

!!! warning "Actian NoSQL"
    Actian NoSQL uses different tools, such as JPQL-based queries and LOID fetches, and a different authentication model. For a NoSQL-specific Python client example, see [Connect Using a Python Client](../nosql/index.md#connect-using-a-python-client).

This section describes how to connect to a running Actian MCP Server instance with the example Python client [`hitl_demo_client.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/clients/hitl_demo_client.py). The script runs read-only queries against every database plugin: Ingres, HCL Informix®, Zen, and Analytics Engine. It also calls write-approval-gated tools directly, which is useful on clients that cannot render a write-approval prompt, such as Claude Desktop and GitHub Copilot.

### Prerequisites

1. Download the client script:

    ```bash
    curl -O https://raw.githubusercontent.com/ActianCorp/mcp-server-docs/main/examples/clients/hitl_demo_client.py
    ```

2. Install the required FastMCP package:

    ```bash
    pip install fastmcp
    ```

### Parameter Naming Differences

Most tools share the same interface across databases, but the parameter names vary by plugin.

| Tool | Product | Parameter |
|------|---------|-----------|
| `execute_query` | Ingres / Analytics Engine / HCL Informix® | `query` |
| `execute_query` | Zen | `sql` |
| `describe_table` | Ingres / Analytics Engine / HCL Informix® | `table_name` |
| `describe_table` | Zen | `table` |
| `list_tables` | All databases | None |
| `list_functions` | Ingres / Analytics Engine / HCL Informix® | None |

`list_tables` and `list_functions` take no input parameters, so those calls are identical on every database. Zen does not register `list_functions`, and Zen adds tools that the other databases do not have, such as `orm_operation` and `execute_write_query`. For the tools that a given database exposes, see its Tools page, for example [Zen tools](../zen/tools/index.md).

The following examples use the parameter names for Ingres, Analytics Engine, and HCL Informix®. For Zen, substitute the parameter names from the preceding table.

### Basic Connection Example

Run the script with a server URL, a tool name, and the arguments for the tool as a JSON object:

```bash
python hitl_demo_client.py http://localhost:8000/mcp list_tables
python hitl_demo_client.py http://localhost:8000/mcp describe_table '{"table_name": "customers"}'
python hitl_demo_client.py http://localhost:8000/mcp execute_query '{"query": "SELECT name, email FROM customers"}'
```

Each call prints the tools available on the server, and then the result, for example:

```text
Connected to http://localhost:8000/mcp (5 tools): describe_table, execute_query, list_functions, list_tables, ...
Calling execute_query({'query': 'SELECT name, email FROM customers'}) ...
Result: {"success": true, "columns": ["name", "email"], "rows": [["Ada", "ada@example.com"]], "row_count": 1}
```

The tool count and the tool list depend on the deployment. A server with custom extensions loaded, such as `adjust_stock` described below, shows more tools.

In PowerShell, quoting JSON that contains SQL is error-prone. Pass the arguments from a file or from standard input instead:

```powershell
python hitl_demo_client.py http://localhost:8000/mcp execute_query @args.json
Get-Content args.json | python hitl_demo_client.py http://localhost:8000/mcp execute_query -
```

For Zen, use `{"sql": "..."}` and `{"table": "customers"}` instead. For more information, see [Parameter Naming Differences](#parameter-naming-differences).

### Connect Using OAuth Authentication

When the server requires OAuth, set `MCP_AUTH=oauth`. Add `MCP_CA_CERT` if the server presents a self-signed certificate:

```bash
export MCP_AUTH=oauth
export MCP_CA_CERT=/path/to/server.crt   # only needed for a self-signed certificate
python hitl_demo_client.py https://mcp.example.com:8000/mcp execute_query '{"query": "SELECT CURRENT_USER"}'
```

!!! tip
    When you use OAuth, the script opens your browser automatically to complete the login, and continues after the token exchange finishes. Run the script on a machine that has a web browser.

!!! note "In-memory token storage warning"
    The FastMCP client might print a `UserWarning` about in-memory OAuth token
    storage. This warning is expected. By default, the client does not persist
    tokens across restarts, so you complete the browser login again each time
    you run the script. The warning does not indicate a connection problem. For
    information about configuring a persistent token store, see the
    [FastMCP OAuth documentation](https://gofastmcp.com/clients/auth/oauth#token-storage).

### Testing Write-Approval-Gated Tools

When write support is enabled and the connected client cannot render an approval prompt, use this script to call those tools directly. The script prints the approval request at the console and asks you to accept or decline it. For the clients affected, see [Elicitation Support for Write Approval](#elicitation-support-for-write-approval).

```bash
python hitl_demo_client.py http://localhost:8000/mcp adjust_stock '{"product_id": 1, "delta": 5}'
```

For the full write-approval walkthrough, see [Answering the Approval Prompt](../ingres/extensions/examples.md#answering-the-approval-prompt).

## Deployment Considerations

Review the following guidelines to ensure a stable and secure connection:

- **Port mapping:** Always connect using the specific port configured for the MCP Server container.
- **Production security:** Enforce HTTPS and configure authentication whenever you expose the server outside a trusted local environment.
- **Remote deployments:** If you enable OAuth on a deployment other than localhost, the server requires TLS and a public `https://` base URL. For instructions about generating certificates, configuring Docker, and trusting self-signed certificates, see [HTTPS / TLS for remote deployments](../ingres/authentication/index.md#secure-remote-deployments-with-https-and-tls).