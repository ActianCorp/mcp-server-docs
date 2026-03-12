# MCP Transport Protocols

## stdio

**Use when:** The MCP server runs as a local subprocess on the same machine as the client.

The client (Claude Desktop, Cursor, VS Code) spawns the server process directly and communicates
via stdin/stdout. No network port is opened. The server lives and dies with the client session.

**Typical setup:**
```json
{
  "mcpServers": {
    "actian-zen": {
      "command": "uv",
      "args": ["run", "actian-zen", "--dsn", "demodata"]
    }
  }
}
```

**Good for:** Developer workstations, local database access, the default for most MCP servers today.

**Not for:** Remote databases, shared team access, containerized deployments where the client
and server are on different machines.

---

## http (request/response)

**Use when:** The server runs remotely and you want simple stateless request/response without
streaming. Each tool call is a single HTTP POST; the server processes it and returns the full
result before the connection closes.

**Good for:** Servers behind load balancers, serverless deployments (AWS Lambda, Azure Functions),
cases where you control both endpoints and don't need streaming progress updates.

**Not for:** Long-running queries where you want incremental output, or anything requiring
server-initiated messages.

---

## sse (Server-Sent Events) — deprecated

**Use when:** You have an existing deployment that already uses SSE and cannot migrate yet.

SSE is an older MCP transport where the server sends a stream of events over a long-lived HTTP
connection. The problem: it is one-directional. The server can push to the client, but client
messages go over a separate HTTP channel. This split makes the implementation awkward and is why
SSE was deprecated in the MCP spec.

**Avoid for new deployments.** Use `streamable-http` instead.

---

## streamable-http

**Use when:** The server runs remotely (different machine, container, cloud) and you want the
modern MCP standard.

This is the replacement for SSE. A single HTTP connection handles both directions: the client
sends requests and the server can stream responses back incrementally. Works through proxies,
load balancers, and firewalls that SSE often struggles with.

**Typical setup:**
```bash
actian-zen --transport streamable-http --dsn demodata
# server listens on http://localhost:8000/mcp
```

**Good for:**
- Team-shared MCP server accessible over a network
- Docker / Kubernetes deployments
- Claude.ai remote MCP server configuration
- Cases where you want streaming progress on long queries

**This is the direction MCP is moving.** If you're building something that needs remote access,
use streamable-http.

---

## Summary

┌───────────────────┬───────────────┬──────────────┬──────────────────────────────┐
│ Protocol          │ Remote?       │ Streaming?   │ When to use                  │
├───────────────────┼───────────────┼──────────────┼──────────────────────────────┤
│ stdio             │ No            │ N/A          │ Local dev, Claude Desktop    │
│ http              │ Yes           │ No           │ Stateless / serverless       │
│ sse               │ Yes           │ Server→Client│ Legacy only (deprecated)     │
│ streamable-http   │ Yes           │ Both ways    │ Remote, modern deployments   │
└───────────────────┴───────────────┴──────────────┴──────────────────────────────┘
