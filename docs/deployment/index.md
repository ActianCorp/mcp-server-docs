---
title: Zen Deployment
description: Deploy the Zen MCP Server locally, in a Podman container, or connect from MCP clients like Claude Desktop and Cursor.
---

# Zen Deployment

The Zen MCP Server can run locally via stdio or inside a Podman container with HTTP transport.

---

## Local (stdio)

### Install dependencies

```bash
uv sync
```

### Run the server

```bash
uv run actian-mcp-server --dbms zen --dsn DEMODATA
```

This starts the server in stdio mode. The MCP client (Claude Desktop, Cursor) launches it as a subprocess.

---

## Podman Container

### Build the image

```bash
podman build -f src/zen/docker/Dockerfile-zen -t zen-mcp-server .
```

### Run via start script

The `start-zen-mcp.ps1` PowerShell script handles networking, IP detection, and port mapping automatically:

```powershell
.\start-zen-mcp.ps1
```

### Manual podman run

```bash
podman run -d --name zen-mcp \
  -p 8000:8000 \
  --add-host=host.docker.internal:<host_ip> \
  actian/zen-mcp-server:latest
```

Port 8000 serves the MCP HTTP transport.

### Load from a tar archive

If you received the image as a tar file:

```bash
podman load -i zen-mcp-server.tar
```

Then run with the commands above.

---

## Container Networking

The container needs to reach the Zen engine on the host machine (port 1583). On Windows with WSL:

- The start script probes `host.docker.internal` and detected WSL IP addresses for port 1583 connectivity.
- Once a reachable IP is found, it is passed to the container as an environment variable.
- If the Zen engine runs on a different host, set the `ZEN_HOST` environment variable manually.

### WSL IP detection

The `start-zen-mcp.ps1` script discovers the WSL virtual adapter IP and tests whether port 1583 is open before launching the container.

---

## Verify the Container

Check container logs:

```bash
podman logs zen-mcp
```

Verify the MCP HTTP endpoint is listening:

```bash
netstat -an | grep 8000
```

---

## MCP Client Configuration

### Claude Desktop

#### stdio mode

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zen": {
      "command": "uv",
      "args": [
        "run",
        "--directory", "/path/to/actian_mcp_server",
        "actian-mcp-server",
        "--dbms", "zen",
        "--dsn", "DEMODATA"
      ]
    }
  }
}
```

#### HTTP mode (container)

```json
{
  "mcpServers": {
    "zen": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Cursor

#### stdio mode

Add to Cursor's MCP settings:

```json
{
  "zen": {
    "command": "uv",
    "args": [
      "run",
      "--directory", "/path/to/actian_mcp_server",
      "actian-mcp-server",
      "--dbms", "zen",
      "--dsn", "DEMODATA"
    ]
  }
}
```

#### HTTP mode (container)

```json
{
  "zen": {
    "url": "http://localhost:8000/mcp"
  }
}
```

---

## Next Steps

- [Configuration](../configuration/index.md) — Full configuration reference
- [Tools](../develop_with_mcp/tools/index.md) — Available Zen MCP tools
- [Testing](../testing/index.md) — QA test plan and results
