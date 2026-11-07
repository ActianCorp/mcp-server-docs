---
title: Multi-Target Deployments
description: Serve many Actian Analytics Engine databases from one Actian MCP Server container, with per-database OAuth scopes, hot-added targets, and per-target extensions.
---

# Multi-Target Deployments

A multi-target deployment lets one Actian MCP Server container serve many Analytics Engine databases, on one or more Analytics Engine installations, instead of running one container per database. Each database gets its own URL, and access to each database is granted separately through OAuth scopes.

A deployment without a `targets` block works exactly as before: one container, one database.

## When to Use Multi-Target

| | One container per database | Multi-target |
| :--- | :--- | :--- |
| 100 databases | 100 containers, configuration files, and credential sets | One container, one registry |
| Adding a database | Deploy a new container | Add a file to `targets.d/`; no restart |
| Access control | The deployment is the boundary | A scope per database, checked on every request |

One container per database remains fully supported. Use multi-target when the number of databases makes that model hard to operate.

---

## How It Works

1. You list your Analytics Engine installations and their databases in the `targets` block of `conf.json`, in files under `targets.d/`, or both. This list is the **target registry**.
2. Each database is reached through its own URL:

    ```text
    https://<mcp_server_host>:<port>/mcp/{host}/{instance}/{database}
    ```

    For example, `https://mcp.example.com:8000/mcp/sales-db.example.com/VW/salesmart`.

3. Every request is checked against the caller's OAuth token. The token must carry a read scope for that database:

    ```text
    actian:{host}:{instance}:{database}:read
    ```

4. The server connects only to databases in the registry. A URL that names anything else is never dialled.

The URL selects the database. No tool takes a database or target argument; a client chooses a database by connecting to its URL.

---

## Requirements

- **Authentication.** A registry with more than one target requires OAuth, so that per-target scopes can be checked. Configure either the default OAuth login ([Auth0](authentication/auth0.md#multi-target-deployments-per-target-permissions) or [Keycloak](authentication/keycloak.md#multi-target-deployments-per-target-scopes)) or [resource-server mode](authentication/resource-server.md). Without one of these, the server refuses to start with more than one target.
- **A registry with exactly one server** (one `host` and `instance`) can start without OAuth, even if it lists several databases. Without OAuth, nothing checks per-target scopes, so every database it lists is reachable.
- **A service account per installation.** The `username` and `password` in each target entry are used for every connection to that installation. With `user_impersonation` enabled, this account also needs the privileges to run `SET SESSION AUTHORIZATION`, exactly as in a single-database deployment. See [Service Account Privileges](authentication/index.md#service-account-privileges).

---

## Configure the Target Registry

Add a `targets` block to `conf.json`. Values in `defaults` apply to every entry; each entry in `list` describes one Analytics Engine installation and the databases it serves.

```json
{
  "host": "0.0.0.0",
  "port": 8000,
  "query_mode": "read-only",
  "max_rows": 1000,
  "targets": {
    "defaults": {
      "driver": "{Ingres}",
      "max_connections": 10
    },
    "list": [
      {
        "alias": "sales",
        "host": "<db_host_1>",
        "instance": "<installation_id_1>",
        "databases": [
          "salesmart",
          {
            "name": "finance",
            "username": "<finance_db_username>",
            "password": "<finance_db_password>"
          }
        ],
        "username": "<db_username_1>",
        "password": "<db_password_1>"
      },
      {
        "alias": "hr",
        "host": "<db_host_2>",
        "instance": "<installation_id_2>",
        "databases": ["hr"],
        "username": "<db_username_2>",
        "password": "<db_password_2>"
      }
    ]
  },
  "oauth": {
    "FASTMCP_SERVER_AUTH_CONFIG_URL": "<oidc_discovery_url>",
    "FASTMCP_SERVER_AUTH_CLIENT_ID": "<client_id>",
    "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<client_secret>",
    "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp_server_host>:8000",
    "FASTMCP_SERVER_AUTH_AUDIENCE": "<audience>",
    "user_impersonation": true
  }
}
```

With a `targets` block, the single-database keys `driver`, `server`, `database`, `database_user`, and `database_password` are not used. Each target entry supplies its own connection details.

### Target Entry Fields

| Field | Required | Description |
| :--- | :--- | :--- |
| `host` | Yes | The database server's host name. It is the first segment of the target's URL and of its scopes, and the address the server connects to. Use a stable DNS name; see [Choosing the Host Name](#choosing-the-host-name). |
| `instance` | Yes | The Analytics Engine installation ID, for example `VW`. It is the second segment of the target's URL and scopes. Letters, digits, and `_`, up to 32 characters. |
| `databases` | Yes | The databases this entry serves. Each item is a database name, or an object with per-database credentials (see below). Database names may contain letters, digits, `_`, and `$`, up to 32 characters. `iidbdb` cannot be listed. |
| `username`, `password` | Yes | The database account used for this installation. |
| `driver` | Yes | The ODBC driver name, `{Ingres}`. Usually set once in `defaults`. |
| `max_connections` | Yes | The maximum number of pooled connections for each database of this entry. Usually set in `defaults`. Must be greater than zero. |
| `port` | No | A numeric port to connect to instead of the installation ID. When set, the connection uses the port and the `instance` value is only used in the URL and scopes. |
| `alias` | No | A display name returned by `list_accessible_targets`. It is not used for routing. |

### Per-Database Credentials

An Analytics Engine installation (`host` and `instance`) can appear only **once** in the registry. When databases on the same installation need different accounts, keep one entry and give those databases an object instead of a plain name:

```json
"databases": [
  "salesmart",
  {"name": "finance", "username": "<finance_db_username>", "password": "<finance_db_password>"}
]
```

- A plain name uses the entry's `username` and `password`.
- An object needs `name`. Supply `username` and `password` together, or omit both to use the entry's account.
- The entry's own `username` and `password` remain required. They are used for every database without an override and to look up database users.
- With `user_impersonation` enabled, a per-database account needs the same impersonation privileges as the entry's account (see [Service Account Privileges](authentication/index.md#service-account-privileges)). A missing privilege shows up on the first query to that database, not at startup.
- Objects are not allowed in `defaults.databases`.

### Choosing the Host Name

The `host` value appears in client URLs and in every scope your identity provider grants. If the database later moves to another machine and `host` is that machine's name, every URL and grant changes with it.

Give each installation a stable DNS name, such as a CNAME `sales-db.example.com`, and use that name in `host`. A move is then a DNS change plus a restart of the MCP Server container. Where you cannot add a DNS record, a hosts entry in the container works the same way:

```bash
docker run --add-host sales-db.example.com:10.1.2.3 ...
```

---

## Add Databases Without a Restart: `targets.d/`

Targets in `conf.json` are read once at startup. To add or remove databases while the server runs, mount a directory of target files at `/app/targets.d` in the container. The server checks the directory about every 10 seconds and applies changes without a restart.

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -v $(pwd)/targets.d:/app/targets.d:ro \
    -p 8000:8000 \
    --name=actian-mcp \
    actian/analytics-engine-mcp-server:1.2.0
```

`conf.json` must still contain a `targets` block. It can hold only `defaults` when every target comes from `targets.d/`:

```json
{
  "targets": {
    "defaults": {"driver": "{Ingres}", "max_connections": 10}
  }
}
```

### File Format

Each `*.json` file in the directory holds either one target entry or a JSON list of entries. Entries use the same fields as `targets.list` and inherit `targets.defaults`.

```json
{
  "host": "<db_host>",
  "instance": "<installation_id>",
  "databases": ["salesmart", "finance"],
  "username": "<db_username>",
  "password": "<db_password>"
}
```

### Do Not Repeat a Server in Both Places

The server merges `targets.list` from `conf.json` with every file in `targets.d/` into one registry. **An Analytics Engine installation (`host` and `instance`) must appear in only one place.** If the same installation appears in `conf.json` and in a `targets.d/` file, or in two files, the registry is rejected as a duplicate:

- At startup, the server does not start.
- During a reload, the change is rejected and the server keeps serving the previous registry.

To serve another database on an installation that is already listed, add the database to that entry's `databases` list instead of creating a second entry.

### Reload Behavior

- **A new or changed file** is applied on the next check.
- **A removed file** removes its targets on the next check. Requests already running finish normally.
- **An invalid file** (malformed JSON, a duplicate, a missing field) is rejected. The server keeps serving the previous registry and logs an error once.
- **An unreadable directory** (for example, an unmounted volume) is treated as an error, not as "no targets".
- **The authentication requirement applies to reloads too.** If the server runs without OAuth, a file that would bring the registry above one target is rejected, and the server logs a warning about this at startup.

### Protecting the Files

Target files contain database passwords, just like `conf.json`:

- Mount the directory read-only.
- In Kubernetes, mount a **Secret**, not a ConfigMap.
- The files must be readable by the container's user.

---

## Scopes

Access to each database is granted by a scope in the caller's OAuth token:

```text
actian:{host}:{instance}:{database}:{read|write}
```

| Scope | Grants |
| :--- | :--- |
| `actian:sales-db.example.com:VW:salesmart:read` | Read `salesmart` |
| `actian:sales-db.example.com:VW:salesmart:write` | Read and write `salesmart` |
| `actian:sales-db.example.com:VW:*:read` | Read every database on that installation |
| `actian:*:*:*:read` | Read every database in the registry |

- `*` matches exactly one segment.
- A `write` scope also grants `read`.
- There are no deny scopes. What a token can reach is readable from its scopes.
- The server logs a warning each time a scope with a wildcard host is used.

A write on a target URL needs that target's `write` scope, the server in `read-write` mode, and, unless disabled, human approval. The `mcp:write` scope does not authorize writes on a target URL, and does not apply to a deployment with more than one server or database. For details, see [Write Support](write-support.md).

How to deliver these scopes depends on your identity provider:

- [Auth0: Per-Target Permissions](authentication/auth0.md#multi-target-deployments-per-target-permissions)
- [Keycloak: Per-Target Scopes](authentication/keycloak.md#multi-target-deployments-per-target-scopes)

### What a Caller Without a Grant Sees

| Request | Response |
| :--- | :--- |
| No token, or an invalid token | `401 Unauthorized` |
| Valid token without a read scope for the target | `403 Forbidden` with `WWW-Authenticate: Bearer error="insufficient_scope"`, naming the scope that is missing |
| Valid token, target not in the registry | The **same** `403` as above |

The server answers an unknown target and an ungranted one identically, so the responses cannot be used to discover which databases exist. The server log records the actual reason.

!!! note "Granting a missing scope"
    With the server's OAuth login, an MCP client may try to sign in again to obtain the missing scope. That attempt fails with an authorization error that names the missing scope. Grant the scope in your identity provider and sign in again.

Revoking a scope takes effect when the caller's current token expires. Tokens are verified locally against the identity provider's published keys. Use shorter token lifetimes if this matters.

### Running Without Scope Checks: `allow_unscoped_reads`

```json
{"allow_unscoped_reads": true}
```

This setting turns off per-target scope checks. Any authenticated caller can then read every database in the registry, and a registry with more than one target can start without per-target scopes. Writes on target URLs are refused while it is set.

!!! warning
    Use `allow_unscoped_reads` only temporarily, for example to test routing before scopes are provisioned in your identity provider. The server logs a warning at every startup while it is set.

---

## Discover Which Databases You Can Reach

The `list_accessible_targets` tool returns the databases the caller's token can read, with the path to connect to each one:

```json
{
  "targets": [
    {
      "host": "sales-db.example.com",
      "instance": "VW",
      "alias": "sales",
      "databases": [
        {
          "name": "salesmart",
          "path": "/mcp/sales-db.example.com/VW/salesmart",
          "url": "https://mcp.example.com:8000/mcp/sales-db.example.com/VW/salesmart"
        }
      ]
    }
  ]
}
```

- Only databases the caller can read are listed. When scope checks are off, every registered database is listed.
- `url` is filled in from `FASTMCP_SERVER_AUTH_BASE_URL`. When it is not configured, `url` is `null`; use `path` with the address you already use for the server.
- Credentials are never returned.

The same data is available as the resource `targets://accessible`, for applications that read it directly, for example to populate a database picker.

---

## Schema Resources

In a multi-target deployment, each database has its own schema resource:

```text
resource://database/{host}/{instance}/{database}/schema
```

A session connected to a target's URL sees only that target's schema resource. Reading another target's schema URI over that session returns "resource not found". A deployment without a `targets` block keeps the single `resource://database/schema` resource. For details, see [Resources](resources/index.md).

After a `targets.d/` change, a client must list resources again to see added or removed schema resources.

---

## Scope Extensions to Specific Targets

By default, an extension's tools, resources, and prompts are offered on every target. An extension written for particular tables fails on targets that do not have them. Add a `targets` list to the extension's entry in `conf.json` to offer it only where it applies:

```json
"extensions": [
  {
    "module": "catalog_insights",
    "config": {"products_table": "products", "low_stock_threshold": 10},
    "targets": ["<db_host_1>/<installation_id_1>/salesmart"]
  },
  {
    "module": "revenue_extension",
    "targets": ["<db_host_2>/<installation_id_2>/*"]
  },
  {
    "module": "catalog_resources"
  }
]
```

- Each selector is `host/instance/database`. `*` matches one whole segment.
- An entry without `targets` is offered on every target.
- A malformed selector stops the server from starting. A selector that names a target not in the registry only logs a warning, so you can configure an extension before its target is added to `targets.d/`.
- The filter follows the live registry, including `targets.d/` changes, without a restart.
- The filter controls where an extension is **offered**. It is not an access control: scopes and database privileges still decide what a caller can reach.

A complete example is in [`examples/conf.example.multi-target-with-extensions.json`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/conf.example.multi-target-with-extensions.json). For writing extensions, see [Extensions](extensions/index.md).

---

## Capacity and Connection Settings

These optional top-level `conf.json` settings control connections. Except for `connect_timeout`, they apply only to a deployment with a `targets` block.

| Field | Default | Description |
| :--- | :--- | :--- |
| `connect_timeout` | `10` | Seconds to wait for a new database connection. `0` waits without limit. Applies to every deployment. |
| `max_connections` (in each target entry or `defaults`) | — | Maximum pooled connections for each database. Required. |
| `global_max_connections` | Same as `db_thread_workers` | The maximum number of database connections across all targets. The server logs a warning at startup if the targets' `max_connections` values add up to more. Cannot exceed `db_thread_workers`. |
| `db_thread_workers` | The number of CPUs plus 4, at most 32 | The number of worker threads that run database calls. Each running call occupies one thread. |
| `pool_idle_ttl` | `300` | Seconds a database's connection pool can sit idle before it is closed. `0` or less keeps idle pools open. Pools are created on first use. |
| `breaker_enabled` | `true` | When an installation repeatedly fails to accept connections, stop trying for a while and refuse its requests immediately, so callers of other installations are not slowed down. After a pause, one request is let through to test whether it has recovered. |

---

## Load Balancer Requirements

When you run more than one container behind a load balancer, configure it as follows:

1. **Route each MCP session to one container.** The server keeps session state in memory, keyed by the `Mcp-Session-Id` header. Route by that header.
2. **Keep a streaming connection on one container for its whole duration.** Write approval sends its prompt over the client's open stream and waits for the answer on that same stream. If the stream is moved to another container, the approval times out.
3. **Keep the OAuth login on one container.** With the server's OAuth login, the `/mcp/authorize`, `/oauth/callback`, and `/mcp/oauth/token` requests of one sign-in must reach the same container. Use sticky routing for these paths, or serve them from a single container. Resource-server mode has no login endpoints and does not need this.

---

## Example Files

| File | Shows |
| :--- | :--- |
| [`conf.example.multi-target.json`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/conf.example.multi-target.json) | Two installations, per-database credentials, OAuth |
| [`conf.example.multi-target-targets-dir.json`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/conf.example.multi-target-targets-dir.json) | A `conf.json` that takes every target from `targets.d/` |
| [`targets.d/`](https://github.com/ActianCorp/mcp-server-docs/tree/main/examples/targets.d) | One-target and several-target files |
| [`conf.example.multi-target-with-extensions.json`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/conf.example.multi-target-with-extensions.json) | Extensions offered on specific targets |
| [`clients/multi_target_client.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/clients/multi_target_client.py) | A client that lists reachable targets and runs a tool on several of them |

---

## Next Steps

<div class="grid cards" markdown>

- :material-lock: **[Authentication](authentication/index.md)**  
  Set up OAuth and per-target scopes with your identity provider.

- :material-key-chain: **[Resource-Server Mode](authentication/resource-server.md)**  
  Accept access tokens from your own application's sign-in.

- :material-pencil: **[Write Support](write-support.md)**  
  Enable writes and grant per-target write scopes.

- :material-puzzle: **[Extensions](extensions/index.md)**  
  Add your own tools, and offer them on specific targets.

</div>
