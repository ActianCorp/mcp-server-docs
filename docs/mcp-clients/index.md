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

This section matters only if the server runs with `query_mode` set to `read-write`. On a read-only server, every client below works the same way.

When write support is enabled, the server asks a person to approve each `INSERT`, `UPDATE`, and `DELETE` before running it. It sends that request using the Model Context Protocol (MCP) elicitation capability, which not every client implements.

| Client | Displays the write approval prompt |
|--------|------------------------------------|
| Claude Code | Yes |
| Claude Desktop | No |
| GitHub Copilot | No |
| Cursor, fast-agent, Codex | Not confirmed. Treat as unsupported until you verify it. |

!!! warning "A client that cannot prompt cannot write"
    If the connected client does not support elicitation, the server rejects the write, exactly as if a person had declined it. There is no silent approval. Reads are unaffected.

    To let such a client write, set `write_confirmation` to `false` in `conf.json`. That runs writes without asking anyone first. See [Write support](../write-support/index.md#skipping-the-approval-prompt).

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

## Connect from Python

To script against the server or build your own agent, use the FastMCP Python client. It
works with every Actian database. See [Connect a Python client](python.md).

## Deployment Considerations

Review the following guidelines to ensure a stable and secure connection:

- **Port mapping:** Always connect using the specific port configured for the MCP Server container.
- **Production security:** Enforce HTTPS and configure authentication whenever you expose the server outside a trusted local environment.
- **Remote deployments:** If you enable OAuth on a non-localhost deployment, the server requires TLS and a public `https://` base URL. For detailed instructions on generating certificates, configuring Docker, and trusting self-signed certificates, see [HTTPS / TLS for remote deployments](../authentication/index.md#secure-remote-deployments-with-https-and-tls).
