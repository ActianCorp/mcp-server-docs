---
title: Examples
description: Example extensions for the Actian MCP Server, written for the SQL plugins; templates for VectorAI DB extensions.
---

# Examples

Five runnable extensions are published in the documentation repository, ready to mount into a running server. They use only the public extension API.

| Example | What it shows |
|---------|---------------|
| [`catalog_insights.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/catalog_insights.py) | Read-only tools. Registers `low_stock_products` and `inventory_value`, and reads the authenticated identity. Works in the default read-only mode. |
| [`order_ops.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/order_ops.py) | Multi-table transactions. `place_order` writes four tables atomically, `cancel_order` restores stock and removes the order, and `order_summary` reads. Needs read-write mode. |
| [`approval_required.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/approval_required.py) | Human approval. `adjust_stock` asks for confirmation and writes only if you approve. Needs read-write mode and a client that can display the prompt. |
| [`catalog_resources.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/catalog_resources.py) | Other features: `setup()` and `teardown()` hooks, a static and a templated resource, and a prompt. Read-only. |
| [`revenue_extension.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/revenue_extension.py) | All three patterns in one reference example: a read tool, an approval-gated write, and a two-table transaction. |

All five share one database. The [examples README](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/README.md) has the full walkthrough.

## Configuration and Schema Files

The examples query SQL tables through `get_database()`, which does not work on a VectorAI DB server (see [Reaching the Engine](index.md#reaching-the-engine)), so they do not run against VectorAI DB as written. There is no VectorAI DB configuration template or schema file for them in this release. Use the examples for the shape of `register()`, the tool and resource definitions, the scope check, and the approval prompt. Replace the SQL calls with requests to the engine's REST API.

| Database | Configuration template | Schema file |
|----------|------------------------|-------------|
| Zen (for reference) | [`conf.example.zen.json`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/conf.example.zen.json) | [`schema.zen.sql`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/extensions/schema.zen.sql) |

The schema file creates seven tables with seed data. A trigger enforces the rule that stock cannot go negative. The header of the schema file lists the grant statements to run afterward for the account that the server connects as.

## Running Examples {#running-the-examples}

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

The startup log shows a `Loaded extension` line for each module and one line per registered tool. Those tools then appear in the MCP client's tool list next to the built-in ones.

## Answering Approval Prompt {#answering-the-approval-prompt}

Claude Desktop and GitHub Copilot cannot display the write-approval prompt, so writes through them are rejected. To test an approval-gated tool such as `adjust_stock`, use [`hitl_demo_client.py`](https://github.com/ActianCorp/mcp-server-docs/blob/main/examples/clients/hitl_demo_client.py), which prints the request and asks you at the console:

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
