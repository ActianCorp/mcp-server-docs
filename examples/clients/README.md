# Example MCP Clients

Small clients for exercising the server directly, handy when your everyday MCP
client cannot drive a particular flow.

## `hitl_demo_client.py`, human-in-the-loop tester

Calls a tool and, when the server asks for approval (MCP **elicitation**), prints
the request and asks **you** at the console to approve or decline. Use it for the
approval-gated tools (`adjust_stock`, `tag_vip_customer`) and for write queries
through `execute_query`. Claude Desktop and Copilot Chat cannot render the
approval prompt, so on those clients the approval can never be answered and the
write fails closed.

```bash
pip install fastmcp
python hitl_demo_client.py http://localhost:8000/mcp adjust_stock '{"product_id": 1, "delta": 5}'
# -> prints the approval request, you type y/n, then shows the result
```

Approve, and the write commits (for example, stock changes). Decline, and it is
cancelled with nothing written.

### Passing tool arguments

A single JSON object:

```bash
python hitl_demo_client.py http://localhost:8000/mcp execute_query '{"query": "select * from customer limit 1"}'
```

### Environment variables

All optional.

| Variable | Purpose |
|---|---|
| `MCP_AUTH=oauth` | Do the OAuth browser login, for a server that runs the OAuth login. It does not work against a server in resource-server mode, which runs no login. Without this the client sends no credentials. |
| `MCP_CA_CERT=<path>` | Server certificate to trust, needed for a self-signed HTTPS server. |

On a multi-target server, pass a database's URL, such as
`https://<mcp-server-host>:8000/mcp/<db-host>/<instance>/<database>`. The plain
`/mcp` URL there can only list the databases, not query them.

Against an OAuth server with a self-signed certificate:

```bash
export MCP_AUTH=oauth
export MCP_CA_CERT=/path/to/server.crt
python hitl_demo_client.py https://<mcp-server-host>:8000/mcp \
    execute_query '{"query": "update products set stock_qty = 42 where product_id = 1"}'
# -> opens your browser to log in; continues automatically once you approve
```

### Running it

Run it from anywhere that can reach the server's HTTP endpoint. To reach a server
on a remote host, tunnel first with `ssh -L 8000:localhost:8000 <host>`, then use
`http://localhost:8000/mcp`.

To run it from the Actian MCP container image, which already has `fastmcp`, give
Docker an interactive stdin with `-it`:

```bash
docker run -it --rm --network <mcp-network> \
  -v "$PWD/hitl_demo_client.py:/tmp/c.py:ro" \
  --entrypoint /app/.venv/bin/python <actian-mcp-image> \
  -u /tmp/c.py http://<server-container>:8000/mcp adjust_stock '{"product_id": 1, "delta": 5}'
```

## `multi_target_client.py`, multi-target client

For an Ingres or Analytics Engine server with a `targets` registry (see
[Multi-Target Deployments](https://docs.actian.com/mcp-server/latest/ingres/multi-target.html)). The client first calls
`list_accessible_targets` to show which databases your token can reach, then runs
one tool against every `host/instance/database` you list on the command line, and
reports which calls succeeded and which were refused. One token can carry grants
for several databases, and one browser login covers every database in the run.

Different databases can have different schemas, so a query only applies to the
databases that have its tables. Give each schema its own run.

```bash
pip install fastmcp httpx

export MCP_AUTH=oauth
python multi_target_client.py https://<mcp-server-host>:8000/mcp execute_query \
    '{"query": "select count(*) from products"}' \
    <db-host-1>/<installation-id>/<database-1> <db-host-2>/<installation-id>/<database-2>
# -> opens your browser to log in once; every database above reuses that login
```

A database your token has no read scope for is reported as denied, naming the
scope it needs. The server answers `403 insufficient_scope`, the same way it
answers for a database that does not exist, so the two cannot be told apart.

The client reports the refusal instead of trying to sign in again for the missing
scope. With the server's OAuth login, a second sign-in cannot obtain a scope your
account was not granted; grant the scope in your identity provider and run the
client again.

`MCP_AUTH=oauth`, an interactive browser login (authorization code with PKCE), is
the only authentication mode this client supports. The login is reused for every
database in one run, but not across runs.

### Writes

A write (`INSERT`, `UPDATE`, or `DELETE` through `execute_query`) needs the server
in `read-write` mode, a `:write` scope for that database, and your approval at the
console. Like [`hitl_demo_client.py`](hitl_demo_client.py), this client prints the
approval request and waits for you to answer, once per database that reaches a write:

```bash
python multi_target_client.py https://<mcp-server-host>:8000/mcp execute_query \
    '{"query": "update products set unit_price = 24.99 where product_id = 2"}' \
    <db-host>/<installation-id>/<database>
# -> prints the approval request, you type y or n, then shows the result
```

Declining one database's write does not stop the others in the same run.

### Environment variables

| Variable | Purpose |
|---|---|
| `MCP_AUTH=oauth` | Interactive browser login. Required. |
| `MCP_CA_CERT=<path>` | Server certificate to trust, for a server with a self-signed certificate. Optional. |

Checking which databases are reachable with `list_tables`:

```bash
export MCP_AUTH=oauth
python multi_target_client.py https://<mcp-server-host>:8000/mcp list_tables '{}' \
    <db-host>/<installation-id>/<database-1> <db-host>/<installation-id>/<database-2>
```
