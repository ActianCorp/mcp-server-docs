---
title: Connecting to MCP Clients
description: Connect MCP-compatible clients to a running Actian MCP Server instance.
---

# Connecting to MCP Clients

Once the Actian MCP Server is running in a container, MCP-compatible clients can connect to it over the configured network transport.

The server inside the container runs in **HTTP** transport mode and clients connect to the server endpoint exposed by the container.

---

## Connection URL Format

- Local deployment: `http://localhost:<port>/mcp`
- Remote deployment: `http://<hostname>:<port>/mcp`

The standard endpoint used for the server deployment is `/mcp`.

---

## Claude Desktop

Add the server entry to `claude_desktop_config.json`:

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

---

## Cursor

Add the server entry to `~/.cursor/mcp.json`:

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

---

## fast-agent

Add the server entry to `fastagent.config.yaml`:

```yaml
mcp:
	servers:
		actian-mcp-server:
			url: "http://localhost:<port>/mcp"
```

---

## Codex

Add the server entry to `~/.codex/config.toml`:

```toml
[mcp_servers.actian-mcp-server]
url = "http://localhost:<port>/mcp"
```

For a remote deployment, replace `localhost` and `<port>` with the public host and port of the Actian MCP Server.

---

## Connection Notes

- Use the port configured for the MCP Server container.
- For production deployments, prefer **HTTPS** and configure authentication when exposing the server outside a trusted local environment.
- When OAuth is enabled on a non-localhost deployment, the server requires **TLS** and a public `https://` base URL.
See [HTTPS / TLS for Remote Deployments](../authentication/index.md#https-tls-for-remote-deployments) for certificate generation, Docker setup, and trusting self-signed certs in MCP clients.

---
