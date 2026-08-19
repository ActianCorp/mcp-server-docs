# Actian NoSQL Examples

Runnable examples for the Actian MCP Server for Actian NoSQL, which accompany the
[Actian NoSQL documentation](https://docs.actian.com/mcp-server/nosql/index.html).

| File | Purpose |
|---|---|
| [`nosql_hitl_client.py`](nosql_hitl_client.py) | A console client that answers the server's write-confirmation prompt, so you can create, update, and delete objects from a client that cannot display the prompt itself. |

## `nosql_hitl_client.py`, write-confirmation tester

The server asks a person to approve every write, and it sends that request using the MCP
**elicitation** capability. Write tools are registered only for clients that advertise the
capability, so a client that cannot prompt is never offered them. This client supplies an
elicitation handler, which means the write tools appear and it can answer the prompt.

```bash
pip install fastmcp
python nosql_hitl_client.py http://localhost:8080/mcp create_objects \
    '{"className": "Employee", "objects": [{"name": "Ada Lovelace"}]}'
# -> prints the confirmation request, you type y/n, then shows the result
```

Approve and the write runs. Decline, cancel, or say nothing until the timeout, and the write
is refused with nothing written.

The client also reports which tools the server registered for the connection, and says so
explicitly when the write tools are absent — the usual sign that writes are disabled
server-side or that the server did not see an elicitation capability.

### Passing tool arguments

Arguments are a single JSON object. Tools that take none can be called without it. The client
hardcodes no class or field, so it runs against any database — replace `Employee`, the field
names, and the LOIDs below with values from your own schema:

```bash
python nosql_hitl_client.py http://localhost:8080/mcp list_classes
python nosql_hitl_client.py http://localhost:8080/mcp execute_query '{"jpql": "select e from Employee e"}'
python nosql_hitl_client.py http://localhost:8080/mcp delete_objects '{"loids": ["15.0.2085"]}'
python nosql_hitl_client.py http://localhost:8080/mcp update_objects \
    '{"updates": [{"loid": "15.0.2085", "expectedVersion": "1", "fields": {"name": "Ada"}}]}'
```

### Authentication

This client sends no credentials, so point it at a server running with authentication
disabled. On a server with OAuth enabled every call is rejected before it reaches a tool.
For the authenticated case, see the OAuth client example under
[Connect Using a Python Client](https://docs.actian.com/mcp-server/nosql/index.html#connect-using-a-python-client),
and add the elicitation handler from this client to it.

### Answering in time

The client waits at the prompt for as long as you need, but the server does not: it rejects
the write once `nsql.writes.confirmation-timeout-seconds` (60 by default) has passed, and
answering after that returns

```text
Create not performed: no confirmation was received within the timeout.
```

That is the only clock involved. The client sets no timeout of its own.

### Running it

The only prerequisite on the server is `nsql.writes.enabled=true`. The write tools are
built in, so no extension and no particular schema are needed.

Run the client from anywhere that can reach the server's HTTP endpoint. To reach a server on
a remote host, tunnel first with `ssh -L 8080:localhost:8080 <host>`, then connect to
`http://localhost:8080/mcp`.

## See also

- [Write support](https://docs.actian.com/mcp-server/nosql/write-support.html) — how a write is authorized, and why the write tools may not appear.
- [Tools](https://docs.actian.com/mcp-server/nosql/tools/index.html) — every tool's arguments, and the confirmation wording for each write tool.
- [Connecting MCP Clients](https://docs.actian.com/mcp-server/mcp-clients/index.html#elicitation-support-for-write-approval) — which everyday clients can display the prompt.
