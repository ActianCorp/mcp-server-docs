**1. Verify the container status**

```bash
docker ps --filter "name=actian-mcp"
```

Confirm that the container status is `Up`.

**2. Verify the endpoint**

Ping the server to confirm that it is listening for requests:

```bash
curl -i http://localhost:8000/mcp
```

If the server is ready, it returns a `200` or `307` status code instead of a
`connection refused` error.

**3. Test the client integration**

Open the configured MCP client. It automatically detects the Actian MCP Server and
displays its available tools. Prompt the AI with a standard database request, such as:

> "List all tables in the database"

The client invokes the server's `list_tables` tool. If it returns a list of the
database tables, the end-to-end connection is working.
