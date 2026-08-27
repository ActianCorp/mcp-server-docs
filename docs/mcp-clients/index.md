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

## Elicitation Support for Write Approval

This section matters only if write support is enabled on the server. On a read-only server, every client below works the same way.

When write support is enabled, the server asks a person to approve each write before running it. It sends that request using the Model Context Protocol (MCP) elicitation capability, which not every client implements.

| Client | Displays the write approval prompt |
|--------|------------------------------------|
| Claude Code | Yes |
| Claude Desktop | No |
| GitHub Copilot | No |
| Cursor, fast-agent, Codex | Not confirmed. Treat as unsupported until you have confirmed elicitation support in the deployment. |

!!! warning "A client that cannot prompt cannot write"
    If the connected client does not support elicitation, no write goes through. There is no silent approval. Reads are not affected.

    On the SQL databases, the server rejects the write, exactly as if a person had declined it. To let such a client write, set `write_confirmation` to `false` in `conf.json`. That runs writes without asking anyone first. See [Write support](../ingres/write-support.md#skipping-the-approval-prompt).

    On Actian NoSQL, such a client is never offered the write tools in the first place: they are absent from its tool list, and calling one fails as an unknown tool. See [Why the write tools may not appear](../nosql/write-support.md#missing-write-tools).

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
            "http://<your-server-host>:<port>/mcp",
            "--allow-http"
          ]
        }
        ```

        !!! note
            If the server uses HTTPS and a self-signed TLS certificate, include the `env` block shown below to bypass certificate verification:

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

This section demonstrates how to connect to a running Actian MCP Server instance using the example Python client [`hitl_demo_client.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/clients/hitl_demo_client.py). It works for read-only queries and, on clients that cannot render a write-approval prompt (Claude Desktop, GitHub Copilot), for testing write-approval-gated tools directly. This approach supports all database plugins (Ingres, HCL Informix®, Zen, and Analytics Engine).

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

Most tools share the same interface across databases and the parameter names may vary depending on the specific plugin.

| Tool | Product | Parameter |
|------|---------|-----------|
| `execute_query` | Ingres / Analytics Engine / HCL Informix® | `query` |
| `execute_query` | Zen | `sql` |
| `describe_table` | Ingres / Analytics Engine / HCL Informix® | `table_name` |
| `describe_table` | Zen | `table` |
| `list_tables` | All databases | None |
| `list_functions` | Ingres / Analytics Engine / HCL Informix® | None |

`list_tables` and `list_functions` take no input parameters, so those calls are identical on every database. `list_functions` is not registered on Zen, and Zen adds tools the other databases do not have, such as `orm_operation` and `execute_write_query`. For the tools a given database exposes, see its Tools page, for example [Zen tools](../zen/tools/index.md).

The following examples use the Ingres, Analytics Engine, and HCL Informix® parameter names. For Zen, substitute the parameter names from the table above.

### Basic Connection Example

Run the script with a server URL, a tool name, and the tool's arguments as a JSON object:

```bash
python hitl_demo_client.py http://localhost:8000/mcp list_tables
python hitl_demo_client.py http://localhost:8000/mcp describe_table '{"table_name": "customers"}'
python hitl_demo_client.py http://localhost:8000/mcp execute_query '{"query": "SELECT name, email FROM customers"}'
```

Each call prints the tools available on the server, then the result, for example:

```text
Connected to http://localhost:8000/mcp (5 tools): describe_table, execute_query, list_functions, list_tables, ...
Calling execute_query({'query': 'SELECT name, email FROM customers'}) ...
Result: {"success": true, "columns": ["name", "email"], "rows": [["Ada", "ada@example.com"]], "row_count": 1}
```

The tool count and list depend on your deployment — a server with custom extensions loaded (like `adjust_stock` below) shows more.

Quoting JSON that contains SQL is painful on PowerShell — pass the arguments from a file or stdin instead:

```powershell
python hitl_demo_client.py http://localhost:8000/mcp execute_query @args.json
Get-Content args.json | python hitl_demo_client.py http://localhost:8000/mcp execute_query -
```

For Zen, use `{"sql": "..."}` and `{"table": "customers"}` instead — see [Parameter Naming Differences](#parameter-naming-differences) above.

### Connect Using OAuth Authentication

When the server requires OAuth, set `MCP_AUTH=oauth`. Add `MCP_CA_CERT` if the server presents a self-signed certificate:

```bash
export MCP_AUTH=oauth
export MCP_CA_CERT=/path/to/server.crt   # only needed for a self-signed certificate
python hitl_demo_client.py https://mcp.example.com:8000/mcp execute_query '{"query": "SELECT CURRENT_USER"}'
```

!!! tip
    When you use OAuth, the script opens your browser automatically to complete the login and continues once the token exchange finishes. Ensure you run it on a machine that has a web browser.

!!! note "In-memory token storage warning"
    The FastMCP client may print a `UserWarning` about using in-memory OAuth
    token storage. This is expected: by default the client does not persist
    tokens across restarts, so you will need to complete the browser login
    again each time you run the script. It does not indicate a connection
    problem. See the [FastMCP OAuth documentation](https://gofastmcp.com/clients/auth/oauth#token-storage)
    for configuring a persistent token store.

### Testing Write-Approval-Gated Tools

When write support is enabled and the connected client cannot render an approval prompt (see the client compatibility table above), use this same script to exercise those tools directly — it prints the approval request at the console and asks you to accept or decline:

```bash
python hitl_demo_client.py http://localhost:8000/mcp adjust_stock '{"product_id": 1, "delta": 5}'
```

See [Answering the Approval Prompt](../ingres/extensions/examples.md#answering-the-approval-prompt) for the full write-approval walkthrough.

## Deployment Considerations

Review the following guidelines to ensure a stable and secure connection:

- **Port mapping:** Always connect using the specific port configured for the MCP Server container.
- **Production security:** Enforce HTTPS and configure authentication whenever you expose the server outside a trusted local environment.
- **Remote deployments:** If you enable OAuth on a non-localhost deployment, the server requires TLS and a public `https://` base URL. For detailed instructions on generating certificates, configuring Docker, and trusting self-signed certificates, see [HTTPS / TLS for remote deployments](../ingres/authentication/index.md#secure-remote-deployments-with-https-and-tls).
