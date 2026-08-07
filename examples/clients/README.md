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

A single JSON object:

```bash
python hitl_demo_client.py http://localhost:8000/mcp execute_query '{"query": "select * from customer limit 1"}'
```

### Environment variables

All optional.

| Variable | Purpose |
|---|---|
| `MCP_AUTH=oauth` | Do the OAuth browser login, for servers that require it. Without this the client sends no credentials. |
| `MCP_CA_CERT=<path>` | Server certificate to trust, needed for a self-signed HTTPS server. |

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
