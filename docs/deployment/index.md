---
title: Deployment
description: Deploy the Actian MCP Server in different environments — local, Docker, and production.
---

# Deployment

The Actian MCP Server can be deployed in multiple ways depending on your use case.

---

## Local (stdio)

The simplest deployment — ideal for desktop AI tools like **Claude Desktop** or **Cursor**.

### Prerequisites

- Python 3.10+
- Actian Zen or Analytics Engine accessible from the machine

### Install

```bash
pip install actian-mcp-server
```

### Configure Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "actian": {
      "command": "actian-mcp-server",
      "args": ["--config", "/path/to/conf.json"]
    }
  }
}
```

### Configure Cursor

Add to Cursor's MCP settings:

```json
{
  "actian": {
    "command": "actian-mcp-server",
    "args": ["--config", "/path/to/conf.json"]
  }
}
```

---

## Docker

Run the server as a Docker container with SSE transport for remote access.

### Using the pre-built image

```bash
docker run -p 8080:8080 \
  -e MCP_ZEN_DSN=MyDatabase \
  -e MCP_ZEN_PASSWORD=secret \
  -v /path/to/conf.json:/app/conf.json \
  actian/mcp-server:latest
```

### docker-compose

```yaml
version: "3.9"
services:
  actian-mcp:
    image: actian/mcp-server:latest
    ports:
      - "8080:8080"
    environment:
      MCP_ZEN_DSN: MyDatabase
      MCP_ZEN_PASSWORD: secret
    volumes:
      - ./conf.json:/app/conf.json
    restart: unless-stopped
```

Start with:

```bash
docker compose up -d
```

---

## Production (SSE)

For production deployments, use SSE transport behind a reverse proxy.

### Server configuration

```json
{
  "server": {
    "transport": "sse",
    "host": "0.0.0.0",
    "port": 8080
  }
}
```

For OAuth-secured deployments, add an `oauth` block to your configuration.
See [Authentication](../authentication/index.md) for the full configuration
reference and provider setup guides (Auth0, Keycloak).

### nginx reverse proxy

```nginx
server {
    listen 443 ssl;
    server_name mcp.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## Health Check

The SSE server exposes a health endpoint:

```bash
curl http://localhost:8080/health
# {"status": "ok", "version": "1.0.0"}
```

---

## Updating

```bash
pip install --upgrade actian-mcp-server
```

For Docker:

```bash
docker pull actian/mcp-server:latest
docker compose up -d
```

---

## Next Steps

- [Configuration](../configuration/index.md) — Full configuration reference
- [API Reference](../APIs/index.md) — Server and plugin API
