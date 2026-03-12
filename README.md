# Actian MCP Server
## Quick start
> NOTE: install the following dependencies **uv and unixodbc**, if not present.

```
git clone https://alm.actian.com/bitbucket/scm/~alokaj/actian_mcp_server.git
cd actian_mcp_server
uv sync
```
### Start the MCP server only
#### Configuration 
A configuration file is used to establish the connection to the database and start the server. The template of this file can be seen at [src/conf_temp.json](src/conf_temp.json). 
```
export DATABASE_USER=<your_database_username>
export DATABASE_PASSWORD=<your_database_password>

uv run actian-mcp-server --dbms=<dbms_name> --conf-file=<db_specific_conf_file> [ --transport=<transport_mode> ]
```

### OAuth Authentication
The server supports OAuth 2.0 / OIDC authentication (Keycloak, Auth0) for HTTP, SSE and streamable-http transports.
When enabled, every incoming request must carry a valid JWT — unauthenticated requests are rejected
before any tool or resource is invoked.

#### How authentication works
The MCP server's `OIDCProxy` handles the OAuth 2.0 flow directly:
1. When a user connects to the MCP server, they are redirected to Auth0 (or Keycloak) to authenticate
2. After successful login, Auth0 issues a JWT containing the user's identity claims
3. The MCP server validates the JWT on every request — unauthenticated requests are rejected

`client_id` and `client_secret` in the config are the MCP server's own credentials with Auth0
(one set, shared by all users). End users authenticate with their own Auth0 accounts or via a
federated identity provider (Keycloak, Google, corporate SSO) that Auth0 trusts.

> NOTE: OAuth is only supported with `--transport sse`, `http`, or `streamable-http`.
> `stdio` transport does not support OAuth.

#### Enable OAuth
Add an `oauth` block to your conf.json (see [src/conf_temp.json](src/conf_temp.json)):
```json
{
    ...
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "<oidc_discovery_url>",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "<client_id>",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<client_secret>",
        "FASTMCP_SERVER_AUTH_BASE_URL": "<server_base_url>",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "<audience>",
        "FASTMCP_SERVER_AUTH_SCOPE": "<scopes>",
        "user_impersonation": true
    }
}
```

OAuth is silently skipped if `FASTMCP_SERVER_AUTH_CONFIG_URL` or `FASTMCP_SERVER_AUTH_CLIENT_ID`
are absent — the server starts without authentication.

#### User impersonation (`user_impersonation`)
Controls whether the authenticated end-user's identity is forwarded to the database.

| Value | Behaviour |
|-------|-----------|
| `true` (default) | JWT verified + `SET SESSION AUTHORIZATION "<user>"` applied per query. Requires every OAuth user to have a matching database account. |
| `false` | JWT still verified (unauthenticated requests rejected), but all queries run under the service-account pool credentials. Use this when database accounts per end-user are not practical. |

Username is extracted from the token in priority order: `username` → `preferred_username` →
email prefix → sanitized `sub`. If no username can be extracted when `user_impersonation=true`, the query is rejected with an error.
When `user_impersonation=false`, username extraction is skipped entirely.

| OAuth configured | `user_impersonation` | Username in JWT | Result |
|---|---|---|---|
| No | (any) | N/A | Queries run as service account |
| Yes | `true` | Present | `SET SESSION AUTHORIZATION` applied |
| Yes | `true` | Absent | Query rejected with error |
| Yes | `false` | (any) | Queries run as service account |

---

### Instructions on supporting a new database
The server uses a plugin framework. Each database is a self-contained plugin that implements the
[MCPPlugin](src/actian_mcp_server/plugin.py) abstract base class.

#### Step 1 — Create a new file subtree
```
mkdir src/<dbms>

# Plugin entry point
touch src/<dbms>/plugin.py

# MCP Server feature subtree
mkdir src/<dbms>/features
touch src/<dbms>/features/tools.py
touch src/<dbms>/features/resources.py
touch src/<dbms>/features/prompts.py

# Docker subtree
mkdir src/<dbms>/docker
touch src/<dbms>/docker/Dockerfile-<dbms>
touch src/<dbms>/docker/entrypoint.sh
touch src/<dbms>/docker/docker-compose.yml
```

#### Step 2 — Implement the plugin
Create a class in `src/<dbms>/plugin.py` that extends `MCPPlugin`:
```python
from contextlib import asynccontextmanager
from actian_mcp_server.plugin import MCPPlugin

class <DBMS>Plugin(MCPPlugin):

    @asynccontextmanager
    async def lifespan(self, server):
        # open connections using self.config
        self.connection = await connect(self.config)
        try:
            yield
        finally:
            await self.connection.close()

    def register_tools(self, server):
        @server.tool(name="my_tool")
        async def my_tool(arg: str) -> str:
            ...

    def register_resources(self, server):
        @server.resource(uri="resource://my_resource")
        async def my_resource() -> str:
            ...

    def register_prompts(self, server):
        @server.prompt
        def my_prompt(question: str) -> str:
            return f"Answer: {question}"
```

See [src/example/plugin.py](src/example/plugin.py) for a complete working example and
[src/vector/plugin.py](src/vector/plugin.py) for the production Vector implementation.

#### Step 3 — Register the plugin
Add one line to the `PLUGINS` dict in [src/actian_mcp_server/server.py](src/actian_mcp_server/server.py):
```python
PLUGINS = {
    "vector": "vector.plugin:VectorPlugin",
    "<dbms>": "<dbms>.plugin:<DBMS>Plugin",   # add this
}
```

#### Step 4 — Adapt the configuration file
```
cp src/conf_temp.json src/<dbms>/conf.json
# adjust the configuration parameters in conf.json
```

### Testing the framework
```
uv run pytest src/tests [pytest args]
```

### Testing Vector
Apply the steps under [Step 4 — Adapt the configuration file](#step-4--adapt-the-configuration-file) first.
> NOTE: requires a Vector instance installation and ODBC setup.

#### Step 0: Source the Vector environment and the ODBC driver required variables (ODBCSYSINI, ODBCINI and II_ODBC_WCHAR_SIZE).

#### Step 1: Prepare the environment
```
export II_INSTALLATION=<your_inst_id>
export DATABASE_USER=<your_database_username>
export DATABASE_PASSWORD=<your_database_password>

source src/vector/setup.sh
```

#### Step 2: Prepare the database and container image
The setup script at src/vector/setup.sh includes the following options (can bee displayed using `bash src/vector/setup.sh --help`):
```
Usage:
  source src/vector/setup.sh
  bash src/vector/setup.sh <command>

Commands:
  --i                 Interactive mode for --all command
  --build-image       Build the Vector MCP server docker image
  --start-container   Start the Vector MCP server container
  --stop-container    Stop and remove the Vector MCP server container
  --init-db           Recreate and initialize the Vector test database
  --all               Prepare the database, build the Vector MCP Server image and start the container
  --help              Show this help message
```
Recommended for the first run:
```
bash src/vector/setup.sh --i
```

#### Step 3: Run the vector test suite
```
uv run pytest src/vector/tests
```


### Docker deployment
Apply the steps under [Step 4 — Adapt the configuration file](#step-4--adapt-the-configuration-file) first.
> NOTE: requires a DBMS instance installation and ODBC setup.

#### Step 1: Setup the environment
```
source set_env.sh
```
#### Step 2: Build the container image
```
bash make-docker-<dbms>.sh
```
#### Step 3: Start the container
```
docker compose -f src/<dbms>/docker/docker-compose.yml up -d
```
#### Step 4: Check the container status
```
docker compose ps
docker logs actian-mcp-server
```
