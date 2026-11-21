---
title: Multi-Target Deployments
description: Configure one HCL Informix MCP Server to route clients to multiple Informix databases.
---

# Multi-Target Deployments

A multi-target deployment lets one Actian MCP Server for HCL Informix serve databases on one or more Informix installations. Each database has its own URL, so a client selects the database by connecting to that URL. A configuration without a `targets` block continues to use the single-database settings described in [HCL Informix configuration](index.md#configuration).

## Configure Targets

Add a `targets` block to `conf.json`. Shared connection settings go in `defaults`; each entry in `list` describes an Informix installation and its databases.

```json
{
  "dbms": "informix",
  "transport": "streamable-http",
  "host": "0.0.0.0",
  "port": 8000,
  "query_mode": "read-only",
  "max_rows": 1000,
  "connect_timeout": 10,
  "allow_unscoped_reads": true,
  "targets": {
    "defaults": {
      "driver": "<informix_odbc_driver>",
      "max_connections": 10
    },
    "list": [
      {
        "host": "<database_host>",
        "port": 15893,
        "instance": "<informix_server_name>",
        "databases": [
          {
            "name": "<database_name>",
            "connection_options": {
              "CLIENT_LOCALE": "<client_locale>",
              "DB_LOCALE": "<database_locale>"
            }
          }
        ],
        "username": "<database_user>",
        "password": "<database_password>"
      }
    ]
  },
  "targets_dir": "/app/targets.d",
  "targets_reload_interval": 10
}
```

Do not include the single-database `servername`, `service`, `dsn`, `server`, `database`, `database_user`, or `database_password` settings alongside a target registry. Keep credentials in a protected configuration or secret store.

### Target fields

| Field | Description |
| :--- | :--- |
| `targets.defaults.driver` | Informix ODBC driver name shared by target entries. |
| `targets.defaults.max_connections` | Maximum connections in the pool for each target database. |
| `targets.list[].host` | Database host. This is part of the target URL. |
| `targets.list[].port` | Informix listener port. |
| `targets.list[].instance` | Informix server name. This is part of the target URL. |
| `targets.list[].databases` | Databases served by this entry. Each database is an object with a required `name` and optional `connection_options`. |
| `targets.list[].username`, `targets.list[].password` | Database credentials for the entry. |
| `targets_dir` | Directory configured for additional target files; the example uses `/app/targets.d`. |
| `targets_reload_interval` | Target reload interval in seconds; the example uses `10`. |

The `connection_options` object carries Informix connection options such as `CLIENT_LOCALE` and `DB_LOCALE`. Use the values appropriate for the database and client environment.

The supplied configuration includes `targets_dir` and `targets_reload_interval`; confirm whether Informix reloads additions and removals without a restart and how it handles invalid target files.

## Connect to a Database

Connect the MCP client to the URL for the database:

```text
https://<mcp_server_host>:<port>/mcp/{host}/{instance}/{database}
```

For example:

```text
https://mcp.example.com:8000/mcp/ifx-db.example.com/ol_informix/warehouse
```

The URL selects the database for the session. A client connected to `/mcp` without a target can call `list_accessible_targets` to discover target URLs, but should connect to a target URL to use database tools. For client configuration examples, see [Connect MCP Clients](../mcp-clients/index.md#client-configuration-examples).

## Authentication and Scope Behavior

Target URL requests use a per-target grant in the caller's access token:

```text
actian:{host}:{instance}:{database}:{read|write}
```

Target requests use the matching `:read` or `:write` grant; `*` matches one whole segment, and `:write` also permits reads on that target. The target's `:write` grant is required for writes to its URL. The `mcp:write` scope is for the unqualified `/mcp` URL in a single-database deployment. The supplied example sets `allow_unscoped_reads` to `true`; confirm whether it bypasses Informix read-scope checks before relying on it. For general OAuth setup, see [Authentication](authentication/index.md), [Write support](write-support.md#which-scope-authorizes-a-write), [Auth0](authentication/auth0.md#multi-target-deployments-per-target-permissions), and [Keycloak](authentication/keycloak.md#multi-target-deployments-per-target-scopes).

## Next Steps

<div class="grid cards" markdown>

- :material-lock: **[Authentication](authentication/index.md)**  
  Configure OAuth for the Informix server.

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available Informix tools.

- :material-folder-open: **[Resources](resources/index.md)**  
  Retrieve schema metadata.

</div>
