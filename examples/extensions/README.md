# Example External Extensions

Five runnable, custom-style extensions that are **mounted into a running
container as a volume** — the way an end user adds their own tools without
rebuilding the image. They use only the public `actian_mcp_server.extension_api`.

| File | What it shows |
|---|---|
| [`order_ops.py`](order_ops.py) | Multi-table **transactions**. `place_order` writes four tables atomically in one transaction (INSERT order + INSERT line item + UPDATE stock + DELETE cart); `cancel_order` restores stock and deletes the order in one read-then-write transaction; `order_summary` returns an order header and its line items (read-only). Requires read-write mode. |
| [`catalog_insights.py`](catalog_insights.py) | Read-only analytics via `get_database().query()`, scoped config, and `get_current_user()`. Works in default read-only mode. |
| [`approval_required.py`](approval_required.py) | **Human-in-the-loop**: `adjust_stock` calls `request_write_confirmation()` and writes only if the user approves over MCP elicitation. Requires read-write mode + an MCP client that handles elicitation. |
| [`catalog_resources.py`](catalog_resources.py) | The rest of the surface: **`setup()`/`teardown()`** lifecycle hooks, two **`@server.resource`** endpoints (static + templated), and a **`@server.prompt`**. Read-only. |
| [`revenue_extension.py`](revenue_extension.py) | **All three patterns in one** reference extension: a read tool (`top_customers_by_revenue`), an approval-gated write (`tag_vip_customer`), and a two-table transaction (`record_customer_sale`). Table names are configurable so it shares the same database as the others. |

All examples share **one database** — provision every table at once with the
schema file for your engine (see below). The authoring contract is documented in the
[Extensions guide](https://docs.actian.com/mcp-server/latest/ingres/extensions/index.html).

## Database compatibility — the code runs unmodified on all four engines

These examples run **unmodified** on Analytics Engine, Ingres, Informix, and Zen —
no per-engine edits to the extension `.py` files or their SQL. The extension
**API** (`query()`, `transaction()` / `tx.write()`, `request_write_confirmation()`,
`get_current_user()`) is identical across engines, and the example **SQL is
deliberately plain ANSI** — standard `INSERT`/`UPDATE`/`DELETE`/`SELECT` with no
dialect-specific syntax and no per-engine branching.

Setup isn't entirely zero-touch, though: after loading the schema file, you must
`GRANT` each table to the user the MCP server connects as (see the comment at the
top of each `schema.<engine>.sql`) — the schema is created as whichever user runs
the file, which usually isn't the MCP server's own database user.

The one operation whose syntax differs across engines — top-N row limiting
(`FETCH FIRST n ROWS ONLY` on Ingres/Analytics Engine (AE) vs `SELECT FIRST n` on Informix vs
`TOP n`/`LIMIT` on Zen) — is handled by ordering in SQL and taking the first *n*
rows **in Python** (`revenue_extension.py`), so no engine-specific clause is used.
For large tables in production you may prefer your engine's native top-N to limit
at the database.

What you supply per deployment is only the **connection settings** (a ready-to-edit
template per engine) and the **schema file** (same tables and seed data; they differ
only in statement terminator, and Zen's swaps one constraint for a trigger — see below):

| Engine | Conf template | Schema file |
|---|---|---|
| Analytics Engine | [`conf.example.analytics_engine.json`](conf.example.analytics_engine.json) | [`schema.analytics_engine.sql`](schema.analytics_engine.sql) (`\g`) |
| Ingres | [`conf.example.ingres.json`](conf.example.ingres.json) | [`schema.ingres.sql`](schema.ingres.sql) (`\g`) |
| Informix | [`conf.example.informix.json`](conf.example.informix.json) | [`schema.informix.sql`](schema.informix.sql) (`;`) |
| Zen | [`conf.example.zen.json`](conf.example.zen.json) | [`schema.zen.sql`](schema.zen.sql) (`;` + trigger) |

`stock_qty >= 0` is enforced differently per engine: a `CHECK` constraint on
Ingres/Informix, a `BEFORE UPDATE` trigger on Zen (`SIGNAL`s a custom SQLSTATE to
abort an oversell), and neither on Analytics Engine — X100 tables support neither
`CHECK` nor triggers, so there it relies only on `order_ops.py`'s own stock check
before writing. Zen's trigger body has semicolons of its
own, so load `schema.zen.sql` with a tool that runs each statement as a whole (e.g. Zen
Control Center's SQL Data Manager), not one that naively splits the file on `;`.

## Expected schema

Seven tables, all in one database — run the schema file for your engine (see the
compatibility table above) to create and seed them. Tables and seed data are the
same across all four; they differ only in statement terminator and how (if at
all) the stock-quantity rule is enforced (see the compatibility table above).
Tables 1–4 back the e-commerce examples; 5–7 back the revenue example (`sales`
is named separately so nothing clashes).

```sql
-- e-commerce (order_ops, catalog_insights, approval_required)
CREATE TABLE products (
    product_id INTEGER NOT NULL PRIMARY KEY,
    name       VARCHAR(50) NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,                   -- place_order looks this up
    stock_qty  INTEGER NOT NULL                          -- enforced per engine, see notes above
);
CREATE TABLE orders (
    order_id    INTEGER NOT NULL PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    status      VARCHAR(20),
    total       DECIMAL(12,2)
);
CREATE TABLE order_items (
    order_id   INTEGER NOT NULL, product_id INTEGER NOT NULL,
    qty        INTEGER NOT NULL, line_total DECIMAL(12,2),
    PRIMARY KEY (order_id, product_id)
);
CREATE TABLE cart (
    customer_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
    qty INTEGER NOT NULL, PRIMARY KEY (customer_id, product_id)
);

-- revenue (revenue_extension)
CREATE TABLE customer_revenue (
    customer_id INTEGER NOT NULL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL, region VARCHAR(10) NOT NULL,
    total_revenue DECIMAL(12,2) NOT NULL
);
CREATE TABLE customers (customer_id INTEGER NOT NULL PRIMARY KEY, vip INTEGER NOT NULL);
CREATE TABLE sales (customer_id INTEGER NOT NULL, amount DECIMAL(12,2) NOT NULL);
```

## Run it

Mount each extension under `/app/extensions/` and your config at `/app/conf.json`.
Copy the conf template for your engine (from the compatibility table above) to
`conf.json` and fill in your database/host — the example `.py` files themselves
need no edits. Credentials are passed as env vars, as in the shipped compose
file. Use your engine's MCP image with an explicit version tag, e.g.
`<actian-mcp-image-for-your-engine>:1.1.0` — omitting the tag pulls `:latest`,
which isn't guaranteed to match what these examples were verified against.

```bash
docker run -d --name my-mcp -p 8000:8000 \
  -e DATABASE_USER=<user> -e DATABASE_PASSWORD=<pw> \
  -v "$PWD/order_ops.py:/app/extensions/order_ops.py:ro" \
  -v "$PWD/catalog_insights.py:/app/extensions/catalog_insights.py:ro" \
  -v "$PWD/approval_required.py:/app/extensions/approval_required.py:ro" \
  -v "$PWD/catalog_resources.py:/app/extensions/catalog_resources.py:ro" \
  -v "$PWD/revenue_extension.py:/app/extensions/revenue_extension.py:ro" \
  -v "$PWD/conf.json:/app/conf.json:ro" \
  <actian-mcp-image-for-your-engine>:1.1.0
```

All nine extension tools — `place_order`, `cancel_order`, `order_summary`,
`inventory_value`, `low_stock_products`, `adjust_stock`, `top_customers_by_revenue`,
`tag_vip_customer`, `record_customer_sale` — then appear in your MCP client's tool
list next to the built-in `execute_query`, `list_tables`, etc.

### Placing an order

`place_order` writes four tables atomically — INSERT order + INSERT line item +
UPDATE stock + DELETE cart entry all commit together, or none do. An oversell
(`quantity` greater than `stock_qty`) is caught by a check in Python before any
write is attempted, so no order is written in that case. Where the target engine
supports a `CHECK` constraint on `stock_qty`, that constraint is a second,
schema-level backstop for a concurrent oversell race the Python check alone
can't catch — not something this walkthrough triggers.
