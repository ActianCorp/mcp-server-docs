---
title: Examples
description: Runnable example extensions for the Actian MCP Server, with the configuration and schema files for Actian Zen.
---

# Examples

Five runnable extensions are published in the documentation repository, ready to mount into a running server. They use only the public extension API.

| Example | What it shows |
|---------|---------------|
| [`catalog_insights.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/catalog_insights.py) | Read-only tools. Registers `low_stock_products` and `inventory_value`, and reads the authenticated identity. Works in the default read-only mode. |
| [`order_ops.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/order_ops.py) | Multi-table transactions. `place_order` writes four tables atomically, `cancel_order` restores stock and removes the order, and `order_summary` reads. Needs read-write mode. |
| [`approval_required.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/approval_required.py) | Human approval. `adjust_stock` asks for confirmation and writes only if you approve. Needs read-write mode and a client that can display the prompt. |
| [`catalog_resources.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/catalog_resources.py) | The rest of the surface: `setup()` and `teardown()` hooks, a static and a templated resource, and a prompt. Read-only. |
| [`revenue_extension.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/revenue_extension.py) | All three patterns in one reference example: a read tool, an approval-gated write, and a two-table transaction. |

All five share one database. The [examples README](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/README.md) has the full walkthrough.

## Configuration and Schema Files

Zen has a configuration template and a schema file.

| Database | Configuration template | Schema file |
|----------|------------------------|-------------|
| Zen | [`conf.example.zen.json`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/conf.example.zen.json) | [`schema.zen.sql`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/schema.zen.sql) |

The schema file creates seven tables with seed data, and enforces the rule that stock cannot go negative with a trigger. The schema file's header lists the grant statements to run afterwards for the account the server connects as.

## Running the Examples

!!! note "Read-write mode required"
    The two transaction examples and the approval example need `"query_mode": "read-write"`. See [Write support](../write-support.md).

Mount each file under `/app/extensions/`, mount your configuration at `/app/conf.json`, and list the modules by name:

```json
{
  "query_mode": "read-write",
  "extensions": [
    { "module": "revenue_extension",
      "config": { "default_region": "NA", "revenue_table": "customer_revenue" } }
  ]
}
```

```bash
docker run -d --rm -p 8000:8000 \
    -e DATABASE_USER=<user> -e DATABASE_PASSWORD=<password> \
    -v ./revenue_extension.py:/app/extensions/revenue_extension.py:ro \
    -v ./conf.json:/app/conf.json:ro \
    <actian-mcp-image>
```

The startup log shows a `Loaded extension` line for each module and one line per registered tool. Those tools then appear in your MCP client's tool list next to the built-in ones.

## Answering the Approval Prompt

Claude Desktop and GitHub Copilot cannot display the write-approval prompt, so writes through them fail closed. To test an approval-gated tool such as `adjust_stock`, use [`hitl_demo_client.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/clients/hitl_demo_client.py), which prints the request and asks you at the console:

```bash
pip install fastmcp
python hitl_demo_client.py http://localhost:8000/mcp \
    adjust_stock '{"product_id": 1, "delta": 5}'
```

In PowerShell, do not pass JSON arguments inline. Windows PowerShell 5.1 and
PowerShell 7 parse quoted JSON differently. Use a file instead, and quote
`"@args.json"` because a bare `@` is PowerShell's splatting operator:

```powershell
'{"product_id": 1, "delta": 5}' | Set-Content -Encoding utf8 args.json
python hitl_demo_client.py http://localhost:8000/mcp adjust_stock "@args.json"
```

See the [client README](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/clients/README.md) for the environment variables it accepts, and [Connecting MCP Clients](../../mcp-clients/index.md#elicitation-support-for-write-approval) for which clients support the prompt.
