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

Approve and the write commits (for example, stock changes). Decline and it is
cancelled with nothing written.

### Passing tool arguments

Three forms are accepted:

| Form | Example |
|---|---|
| JSON object | `'{"product_id": 1, "delta": 5}'` |
| JSON file | `@args.json` |
| Raw SQL, for `execute_query` | `"select * from customer"` |

### Environment variables

All optional.

| Variable | Purpose |
|---|---|
| `MCP_AUTH=oauth` | Do the OAuth browser login, for servers that require it. Without this the client sends no credentials. |
| `MCP_CA_CERT=<path>` | Server or CA certificate to trust, needed for a self-signed HTTPS server. It is added on top of the system certificates, so public certificates keep validating. If unset, the client looks for `server.crt` in the current directory and `server.crt` or `mcp-server.crt` in your home directory. |
| `MCP_SCOPES=<scopes>` | Space-separated OAuth scopes to request. Defaults to `openid email profile mcp:write`. A token carries `mcp:write` only if your user is granted it, so you can test the write-scope gate by logging in as users with and without it. |
| `MCP_APPROVAL_TIMEOUT_SECS=<n>` | How long to wait for your answer at the prompt, in seconds. Defaults to 60. On timeout the client declines, so the write fails closed. |

Against an OAuth server with a self-signed certificate:

```bash
export MCP_AUTH=oauth
export MCP_CA_CERT=/path/to/server.crt
python hitl_demo_client.py https://<mcp-server-host>:8000/mcp \
    execute_query "update products set stock_qty = 42 where product_id = 1"
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
