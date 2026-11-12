---
title: Vector Search
description: Find the rows most similar to a query vector in an Actian Analytics Engine VECTOR column with the vector_search tool, and read vector column details from describe_table and the schema resource.
---

# Vector Search

Actian Analytics Engine stores embeddings and other numeric vectors in `VECTOR` columns. The Actian MCP Server shows an AI agent which columns are vectors and how they are declared, and it provides a `vector_search` tool that returns the rows nearest to a query vector.

Use vector search when the question is about similarity rather than exact matches. Examples include finding the documents closest to a question embedding, the products most like a given product, or the records nearest to a reference point.

!!! note "Requirements"
    `VECTOR` columns require Analytics Engine 8.0 or later. When the server connects to an earlier release, such as 7.0, `describe_table` and the schema resource report columns without vector details. `vector_search` returns an error saying the server does not support it.

## How Vector Columns Appear

Each `VECTOR` column has a dimension, which is the number of coordinates, and an element type, which is the numeric type of each coordinate. The server reports both through `describe_table` and through the schema resource.

### In describe_table

For a table that has at least one `VECTOR` column, `describe_table` adds four fields to every row:

| Field | Description |
|-------|-------------|
| `vector_dimensions` | Number of coordinates in the vector, such as `4`. |
| `vector_element_type` | Coordinate type: `SMALLINT`, `INTEGER`, `BIGINT`, `FLOAT4`, `FLOAT8`, or `DECIMAL(p,s)`, such as `DECIMAL(5,2)`. |
| `vector_index_name` | Name of the index that covers this column, or `null` when there is none. |
| `vector_index_status` | `indexed` when an index covers the column. Otherwise `no index; queries scan the table`. |

For a vector column, `column_datatype` is `VECTOR`. For the other columns in the same table, the four vector fields are `null`. A table with no `VECTOR` column returns the standard six fields only.

**Example response (illustrative)**

```json
{
  "success": true,
  "columns": [
    "table_owner", "column_name", "column_datatype", "column_length",
    "column_scale", "column_comment",
    "vector_dimensions", "vector_element_type", "vector_index_name", "vector_index_status"
  ],
  "rows": [
    ["<owner>", "doc_id",    "INTEGER", "4",  "0", null, null, null,     null, null],
    ["<owner>", "title",     "VARCHAR", "200", "0", null, null, null,     null, null],
    ["<owner>", "embedding", "VECTOR",  "<storage_length>", "0", null, 4, "FLOAT4", null, "no index; queries scan the table"]
  ],
  "row_count": 3
}
```

`column_length` and `column_scale` for a vector column come from the database catalog and describe how the column is stored. Use `vector_dimensions` and `vector_element_type` for the vector's shape.

### In the Schema Resource

The schema resource reports a vector column's `dtype` as the full declaration, for example `VECTOR(4, FLOAT4)` or `VECTOR(3, DECIMAL(5,2))`. See [Resources](resources/index.md#vector-columns).

## The vector_search Tool

`vector_search` computes the distance between a query vector and the vector column in every candidate row, and returns the nearest rows in ascending order of distance. The first row is always the closest match, whichever metric you choose.

The tool is read-only. It is available in both `read-only` and `read-write` query modes.

### Parameters

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `table` | `string` | ✓ | | Table that contains the vector column. Accepts a plain name, such as `documents`, or an owner-qualified name, such as `actian.documents`. |
| `column` | `string` | ✓ | | The `VECTOR` column to search. Must be unqualified, for example `embedding`, not `documents.embedding`. |
| `find_like` | `array of number` | ✓ | | The query vector. Its length must equal the column's dimension, and every value must be a finite number. |
| `metric` | `string` | | `EUCLIDEAN_SQUARED` | Distance metric. One of `EUCLIDEAN_SQUARED`, `EUCLIDEAN`, `COSINE`, `DOT`, `MANHATTAN`, `HAMMING`. See [Metrics](#metrics). |
| `limit` | `integer` | | `10` | Maximum number of rows to return, from `1` to `200`. |
| `also_return` | `array of string` | | `[]` | Other columns of the same table to return with each row, for example `["doc_id", "title"]`. |

!!! note "Row cap"
    If `limit` is greater than the `max_rows` value in the server configuration, the server lowers it to `max_rows` and adds a `warning` to the response.

Given a plain table name, the server searches the table you own if one exists with that name. Otherwise it selects one belonging to another owner. Pass `owner.table` to search a specific one.

### Output Schema

**On Success**

```json
{
  "success": true,
  "columns": ["<also_return_columns>", "distance"],
  "rows": [["<also_return_values>", "<distance>"]],
  "row_count": "<num_rows>",
  "table": "<owner>.<table>",
  "column": "<vector_column>",
  "metric": "<metric>",
  "dimensions": "<dimensions>",
  "element_type": "<element_type>",
  "index_name": "<index_name or null>",
  "index_status": "<index_status>",
  "scan_mode": "<exact or approximate>",
  "rows_scanned": "<num_rows_in_table or null>",
  "truncated": true,
  "warning": "<warning_message>"
}
```

| Field | Description |
|-------|-------------|
| `columns` | The `also_return` columns, in the order requested, followed by `distance`. |
| `rows` | One row per match, nearest first. The last value in each row is the distance, as a number. |
| `row_count` | Number of rows returned. |
| `table` | The table searched, owner-qualified. |
| `column` | The vector column searched. |
| `metric` | The metric used. |
| `dimensions` | The column's dimension. |
| `element_type` | The column's coordinate type, such as `INTEGER`, `FLOAT4`, or `DECIMAL(5,2)`. |
| `index_name` | Name of the index that covers the column, or `null`. |
| `index_status` | `indexed`, or `no index; queries scan the table`. |
| `scan_mode` | `approximate` when the search used approximate nearest-neighbor retrieval. `exact` when it compared every row. See [Vector Indexes](#vector-indexes). |
| `rows_scanned` | Number of rows in the table, taken from the table's statistics. `null` when statistics are not available. This is not a count of rows the search examined. |
| `truncated` | Present and `true` only when the result was cut to the configured row limit. |
| `warning` | Present only when there is something to report, for example a lowered `limit`, an index that this search cannot use, or truncated results. |

**On Error**

```json
{
  "success": false,
  "error": "<error_message>"
}
```

The server checks the request before it searches. The error message names the problem, for example:

- `find_like` is empty or contains a value that is not a finite number.
- `find_like` has a different number of values than the column's dimension. The message reports both counts.
- The table does not exist or is not accessible, or it has no column with that name. The message lists the available columns.
- The column is not a `VECTOR` column.
- An `also_return` entry names a column that does not exist, is listed twice, or is `distance`, which is always returned.
- The metric is `COSINE` and `find_like` is all zeros. See [Zero Vectors](#zero-vectors).

### Example

The data in this example is illustrative.

**Request**

```
Find the three documents most similar to this embedding: [0.12, 0.85, 0.31, 0.40]
```

```json
{
  "table": "documents",
  "column": "embedding",
  "find_like": [0.12, 0.85, 0.31, 0.40],
  "limit": 3,
  "also_return": ["doc_id", "title"]
}
```

**Response**

```json
{
  "success": true,
  "columns": ["doc_id", "title", "distance"],
  "rows": [
    [42, "Returns policy", 0.0213],
    [17, "Shipping times", 0.1874],
    [88, "Warranty claims", 0.2506]
  ],
  "row_count": 3,
  "table": "<owner>.documents",
  "column": "embedding",
  "metric": "EUCLIDEAN_SQUARED",
  "dimensions": 4,
  "element_type": "FLOAT4",
  "index_name": null,
  "index_status": "no index; queries scan the table",
  "scan_mode": "exact",
  "rows_scanned": 1250
}
```

## Metrics

Every metric returns a smaller number for a more similar vector, so results are always ordered nearest first.

| Metric | What it measures | Can use a vector index |
|--------|------------------|:----------------------:|
| `EUCLIDEAN_SQUARED` | Squared straight-line distance. Ranks rows the same way as `EUCLIDEAN`. This is the default. | Yes |
| `DOT` | Dot product, negated so that a smaller value means more similar. | Yes |
| `EUCLIDEAN` | Straight-line distance. Use it when you need the actual distance value. | No |
| `COSINE` | 1 minus the cosine similarity, from 0 to 2. Undefined for an all-zero vector. | No |
| `MANHATTAN` | Sum of the absolute differences between coordinates. | No |
| `HAMMING` | Number of coordinates that differ. A whole number, intended for integer coordinates. | No |

## Vector Indexes

A vector index lets Analytics Engine run an approximate nearest-neighbor search instead of comparing the query vector with every row. The server uses approximate search only when all of the following are true:

- A single-column index covers the vector column.
- The column's element type is `FLOAT4`.
- The metric is `EUCLIDEAN_SQUARED` or `DOT`.

In that case `scan_mode` is `approximate`. In every other case it is `exact`. If an index covers the column but the metric or element type rules it out, the response includes a `warning` saying that the search is exact.

Analytics Engine also requires the table to have a single-column integer primary key before a vector index can be created on it. See the Analytics Engine documentation for how to create vector indexes.

!!! note "What indexed means"
    The database catalog does not record which metric an index was built with. `indexed` means an index covers the column. It does not confirm that the database used the index for a particular query.

    For an exact search on an indexed column, use `EUCLIDEAN`. It ranks rows the same way as `EUCLIDEAN_SQUARED` but never uses the index, so `scan_mode` is `exact`.

## Practical Guidance

### Cosine Ranking with an Index

`COSINE` is a common choice for text embeddings, but it cannot use a vector index. If your vectors are normalized to unit length, `COSINE`, `DOT`, and `EUCLIDEAN_SQUARED` rank results identically. Normalize vectors when you write them, normalize the query vector the same way, and search with `DOT`. You get cosine ranking with index support on a `FLOAT4` column.

To check whether stored vectors are normalized, run a query through `execute_query` that uses `VECTOR_NORM(<column>, EUCLIDEAN)`. A normalized vector has a norm of 1.

### Decimal Coordinates

Analytics Engine rounds `DECIMAL` coordinates to the column's declared scale. For example, a `VECTOR(3, DECIMAL(5,2))` column stores `[1.11, 1.112, 1.113]` as `[1.11, 1.11, 1.11]`. Distances are calculated on the rounded values, so embeddings that differ only beyond the declared scale compare as equal. Check `element_type` in the response, or `vector_element_type` in `describe_table`, when results look tied.

### Zero Vectors

`COSINE` distance is undefined for a vector whose values are all zero, so the server rejects that request:

```json
{
  "success": false,
  "error": "COSINE distance is undefined for an all-zero vector"
}
```

An all-zero query vector usually means the embedding step failed. Check how it was produced before you try another metric.

### Filtering and Joins

`vector_search` searches a single table and does not take a filter. To combine similarity with conditions on other columns, or with a join, use `execute_query` with the `VECTOR_DISTANCE` function. For example:

```sql
SELECT doc_id, title,
       VECTOR_DISTANCE(embedding, VECTOR('[0.12, 0.85, 0.31, 0.40]', 4, FLOAT4), EUCLIDEAN_SQUARED) AS distance
FROM documents
WHERE category = 'support'
ORDER BY distance
FETCH FIRST 10 ROWS ONLY
```

## What Vector Search Does Not Do

- **It does not generate embeddings.** You, or the AI agent, supply the query vector in `find_like`. The server does not call an embedding model. The query vector must be produced by the same model, with the same dimension, as the stored vectors.
- **It does not create or manage indexes.** The server reports whether an index exists. Create and maintain vector indexes with Analytics Engine tooling.
- **It does not write data.** Storing or updating vectors is done with SQL. See [Write Support](write-support.md).

---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Full reference for the Analytics Engine tools, including `describe_table`.

- :material-folder-open: **[Resources](resources/index.md)**  
  See how vector columns appear in the schema resource.

- :material-pencil: **[Write Support](write-support.md)**  
  Enable `INSERT`, `UPDATE`, and `MERGE` to store vectors through the server.

</div>
