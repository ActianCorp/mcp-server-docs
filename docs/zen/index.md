---
title: Actian Zen
description: Connect MCP clients to Actian Zen for database exploration, SQL queries, and optional write support.
---

# Actian MCP Server for Zen

Connect the MCP-compatible client to Actian Zen using the Actian MCP Server. The server handles automatic Zen dialect translation, allowing you to explore schema metadata, execute SQL queries, and perform ORM operations through a standard interface.

Writes are disabled by default. Setting `query_mode` to `read-write` enables them and changes which tools the server registers — see [Write support](write-support.md) and [Tools](tools/index.md).

## Capabilities

The Actian MCP Server for Zen supports the following operations:

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Execute `SELECT` with automatic translation to Zen dialect. |
| **List tables and views** | Discover available objects and inspect their structures.|
| **ORM operations** | Query data using `JOIN`, `WHERE`, `ORDER BY`, and `LIMIT` clauses. |
| **Write data** | `INSERT`, `UPDATE`, `DELETE`, and `MERGE`, when `query_mode` is `read-write`. A conditional write states how many rows currently match before it is approved. |
| **Blob and file data** | List and download blob or file data stored in the database. Read-only mode. |
| **Server management** | Query server capabilities, list DSNs, and release locks. Read-only mode.|
| **Schema metadata** | View the database schema as a structured resource. |
| **Several databases from one server** | Serve many databases and personas from one container. Each has its own URL, with read-only personas and per-URL grants. See [Multiple Databases](multi-target.md). |
| **Call log** | One JSON record per tool call in the container log. Each record shows who made the call, the target, the tool, and the outcome. See [Call log](#call-log). |



## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker installed and running on the host machine.
- **Actian Zen Instance:** A running instance that the container can reach.
- **Credentials (Optional):** Required if the Zen database uses authentication.
- **OIDC provider (Optional):** Required if you are using OAuth authentication.


## Configuration

You can configure the MCP Server for Zen using a `conf.json` file. Mount this file into the container at `/app/conf.json`. Choose one of the two connection formats below based on the security requirements (credentials).

### Connection Formats

**DSN connection (no credentials)**

Use this format when the built-in is `odbc.ini` and DSN is sufficient for requirements:

```json
{
  "database": "demodata",
  "conn_string": "DSN=demodata",
  "host": "0.0.0.0",
  "port": 8000,
  "query_mode": "read-only",
  "write_confirmation": true
}
```

**Full driver connection (with credentials)**

Use this format when the database requires authentication. This bypasses the container's built-in `odbc.ini` and connects directly to the Zen engine.

```json
{
  "database": "demodata",
  "conn_string": "Driver=/opt/actianzen/lib64/libodbcci.so;ServerName=host.docker.internal:1583;DBQ=DEMODATA;UID=myuser;PWD=mypassword",
  "host": "0.0.0.0",
  "port": 8000,
  "query_mode": "read-only",
  "write_confirmation": true
}
```

### Configuration Reference

**Required Fields**

| Field | Type | Description |
|-------|------|-------------|
| `conn_string` | `string` | ODBC connection string. Use `DSN=<name>` for the built-in DSN, or a full driver string with `UID` and `PWD` for authenticated connections. |
| `host` | `string` | Bind address for the MCP server inside the container. Set this to `0.0.0.0` so the server is reachable from outside the container.|
| `port` | `integer` | Port the MCP server listens on. This must match the port exposed by Docker (default `8000`). |

**Optional Fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `database` | `string` | — | Logical database name used for display purposes. |
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. Default is `1000`. |
| `log_level` | `string` | `INFO` | Server log verbosity. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `query_mode` | `string` | `read-only` | `read-only` or `read-write`. Determines which tools are registered. See [Write support](write-support.md). |
| `write_confirmation` | `boolean` | `true` | Set to `false` to run the built-in write tools without the human approval prompt. The `mcp:write` scope check still applies. Applies only when `query_mode` is `read-write`. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments, see [Authentication](authentication/index.md) for more information. |
| `auth_mode` | `string` | — | `resource-server` makes the server verify tokens that your identity provider issued, instead of running its own login. See [Resource-server mode](authentication/index.md#resource-server-mode). |
| `ssl_certfile`, `ssl_keyfile` | `string` | — | In-container paths of the TLS certificate and key, `/app/server.crt` and `/app/server.key`. Required when OAuth is on and `host` is not `localhost`. See [HTTPS and TLS](authentication/index.md#secure-remote-deployments-with-https-and-tls). |
| `call_log` | `boolean` | `true` | One JSON record per tool call in the container log. See [Call log](#call-log). |
| `call_log_statements` | `boolean` | `false` | Adds the SQL text of `execute_query` and `execute_write_query` calls to the call log. While this is on, the server logs a warning at every start. |
| `targets` | `object` | — | Serve several databases and personas from one container. Each has its own URL. See [Multiple Databases](multi-target.md). |
| `zen_readonly_personas` | `array` | `[]` | Persona labels (the `instance` of a target entry) whose connections open read-only. See [Read-only personas](multi-target.md#read-only-personas). |
| `allow_unscoped_reads` | `boolean` | `false` | Lets a caller without a per-target grant read. You need it to run several targets without authentication. Otherwise, use it only for testing. |
| `targets_dir`, `targets_reload_interval` | `string`, `integer` | `/app/targets.d`, `10` | Directory of additional target files, and how often the server checks it. See [Adding a database without a restart](multi-target.md#adding-a-database-without-a-restart). |
| `extensions` | `array` | — | Extension modules to load, each an object with a required `module` and an optional `config`. For more information, see [Extensions](extensions/index.md). |

!!! note "OAuth and user impersonation"
    Actian Zen does not support `SET SESSION AUTHORIZATION`. If you use OAuth, set `user_impersonation` to `false` inside the `oauth` block. The server ignores a top-level key of that name. The server records the authenticated user in the call log, but every query runs as the login in the connection string.

## Several Databases from One Server

A `targets` block turns the one-database server into one URL per engine, persona, and database. Each URL has its own connection to Zen: `http://<mcp-host>:8000/mcp/{host}/{instance}/{database}/mcp`. Personas listed in `zen_readonly_personas` open read-only. With an identity provider, each URL gets its own read and write grants. [Multiple Databases](multi-target.md) covers configuration, URLs, adding and removing targets while the server runs, and limits.

## Call Log

Every tool call writes one JSON line to the container log (`docker logs <container>`):

```json
{"ts": "2026-11-12T09:41:07.118+00:00", "user": "mcp_test_user", "target": "zen16/admin/DEMODATA",
 "tool": "execute_write_query", "action": "write", "status": "ok", "rows": 1, "latency_ms": 62.0,
 "correlation_id": "3f9c1c0b6d2d4a5e9f0e2a7b8c6d5e4f", "request_id": "3"}
```

| Field | Meaning |
|-------|---------|
| `ts` | When the record was written, UTC. |
| `user` | The authenticated user from the token when OAuth is on, otherwise `null`. Zen cannot run a query as that user, so this field records who asked. The query itself runs as the connection-string login. |
| `target` | `host/instance/database` of the routed URL, or the server and database of `conn_string` on a single-database server. |
| `tool`, `action` | The tool, and the action: `read`, `write`, or `admin`. The server decides the action from the tool and its arguments, never by parsing SQL. |
| `status` | `ok`, `error`, or `rejected` when the approval prompt was declined. |
| `rows` | Rows returned for a read (capped by `max_rows`), rows affected for a write. |
| `latency_ms` | How long the call took inside the server. |
| `correlation_id`, `request_id` | The MCP session ID, which the calls of one conversation share, and the request number within that session. |
| `detail` | Appears only on tools whose arguments name a table or an operation, such as `orm_operation`: `{"table": "Person", "operation": "insert"}`. The SQL tools have no `detail`. |

The server never records SQL text or row values unless `call_log_statements` is `true`. The log records what the server did. It is not an audit trail, because nothing in it is tamper-evident. Set `"call_log": false` to turn it off.


## Start Server {#start-the-server}

Once the `conf.json` is ready, start the container and mount the configuration file:

```bash
docker run -d \
  --name zen-mcp \
  -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/zen-mcp-server:1.2.0
```

!!! note "Container networking"
    `-p 8000:8000` exposes the server port on the host. `--add-host=host.docker.internal:host-gateway` allows the container to reach services on the host machine (such as the Zen engine on port 1583). Docker Desktop on Windows and macOS resolves `host.docker.internal` automatically; Linux requires the `--add-host` flag.

Once the container is running, connect the MCP client to the exposed server endpoint using the host and port from the configuration.


## Usage

After connecting, the MCP client automatically discovers the server's capabilities. You can then perform the following tasks:

- **Inspect before querying:** List tables and review structure before writing SQL.
- **Run a query:** Execute a read-only SQL statement and receive formatted results.
- **Explore relationships:**  Traverse foreign keys and related tables using ORM operations.



## Next Steps

<div class="grid cards" markdown>

- :material-pencil: **[Write Support](write-support.md)**  
  Enable data-modifying SQL, and what gates each write.

- :material-lock: **[Authentication](authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

- :material-database-cog: **[Multiple Databases](multi-target.md)**
  Serve several databases and personas from one container. Each has its own URL.

- :material-server-network: **[Deployment Scenarios](deployment.md)**
  Where the engine, the server, and the agents run, and which settings each layout needs.

- :material-tools: **[Tools](tools/index.md)**
  Learn more about the SQL, ORM, and blob tools exposed by the Zen server.

- :material-folder-open: **[Resources](resources/index.md)**
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**
  Use the built-in prompt templates for common workflows.

- :material-puzzle: **[Extensions](extensions/index.md)**
  Add custom tools to the server with a Python extension.

</div>
