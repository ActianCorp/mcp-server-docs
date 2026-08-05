### Example: Writing a Row

This example needs `query_mode` set to `read-write`.

**User Request**

```
Add a customer named Contoso Supply
```

**Input**

```json
{
  "query": "INSERT INTO customers (customer_id, customer_name) VALUES (103, 'Contoso Supply')"
}
```

Before running the statement, the server asks you to approve it in your client. The response depends on your answer.

**Response, when you approve**

```json
{
  "success": true,
  "columns": [],
  "rows": [],
  "row_count": 1
}
```

**Response, when you decline, do not answer, or the client cannot show the prompt**

```json
{
  "success": false,
  "error": "Write operation was not approved by the user."
}
```

### Write Errors

These apply when `query_mode` is `read-write`.

**The token lacks the `mcp:write` scope**

The server checks the scope before it asks anyone to approve the statement, so no prompt appears.

```json
{
  "success": false,
  "error": "write operations require the 'mcp:write' scope, which the access token does not carry"
}
```

**The statement is DDL or administrative**

```json
{
  "success": false,
  "error": "DDL and administrative statements (CREATE/ALTER/DROP/GRANT/SET/ENABLE/...) are not permitted."
}
```
