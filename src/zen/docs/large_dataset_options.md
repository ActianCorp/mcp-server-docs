# Large Dataset / Report Generation Options

## Background

`execute_query` and `orm_operation` both cap results at `max_rows=1000` to prevent
token overflow in the LLM context window. This is the right default for conversational
use, but breaks when a user needs a full-dataset report.

## Options

### 1. Server-side aggregation (recommended first)

Push the report logic into SQL. The DB aggregates over all rows; only the summary
comes back through MCP.

```sql
-- instead of fetching all rows and computing in the client:
SELECT region, SUM(revenue) AS total, COUNT(*) AS orders
FROM sales
GROUP BY region
ORDER BY total DESC
```

Works for most reporting scenarios. The LLM needs to understand the user's intent
well enough to write the right aggregation — which it generally can, given a good
schema summary in server instructions.

No code changes needed. Should be the default recommendation to the LLM via instructions.

### 2. Export tool — `export_query`

A dedicated tool that runs a query, writes all rows to a file (CSV or Excel),
and returns the file path. The LLM never sees the raw rows.

```
export_query(sql, format="csv", filename="report.csv")
→ {"file": "C:/exports/report.csv", "rows": 84321, "size_kb": 4200}
```

The user then downloads the file directly. Can be combined with `blob_operation`
for upload to a table or retrieval via MCP.

**Implementation:** new tool in `register.py`, wraps pyodbc cursor fetchall into
a csv.writer loop. Needs a configurable export directory in conf.json.

### 3. Pagination

The LLM calls `execute_query` in a loop using OFFSET/FETCH, assembling pages
until done. Each page fits in context; the LLM accumulates totals or passes
pages to a downstream tool.

```sql
SELECT * FROM sales ORDER BY id OFFSET 0 ROWS FETCH NEXT 1000 ROWS ONLY
SELECT * FROM sales ORDER BY id OFFSET 1000 ROWS FETCH NEXT 1000 ROWS ONLY
-- ...
```

Works in theory but is fragile in practice — the LLM loses track of state across
turns, and reassembling pages inside the context window still hits limits for large
datasets. Not recommended as a primary solution.

### 4. Configurable max_rows per call

Expose `max_rows` as an explicit parameter on `execute_query` so the caller can
raise the limit when needed.

```
execute_query(sql="SELECT ...", max_rows=10000)
```

Low effort to implement (parameter already exists internally). Risk: an LLM or
user requesting 50k rows will overflow the context and produce a truncated or
broken response with no clear error. Needs a hard ceiling and a warning in the
tool description.

## Recommendation

Implement **options 2 and 4** together, rely on **option 1** by default.

- Add guidance to `server.instructions` telling the LLM to prefer aggregation SQL
  for reports rather than fetching raw rows.
- Add `export_query` tool for cases where the user explicitly needs all raw data
  as a file.
- Expose `max_rows` parameter with a hard ceiling (e.g. 10000) and a warning in
  the tool description for edge cases where a larger result set is genuinely needed
  in context.

Pagination (option 3) is not worth implementing — the problem it solves is better
handled by the export tool.
