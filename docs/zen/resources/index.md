---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Actian Zen.
---

# Resources

The Actian MCP Server for **Actian Zen** exposes a built-in resource for database schema discovery.

## Available resources

The Zen integration provides the following resource:

| Resource URI | Purpose |
|-----|-------------|
| `resource://database/schema` | Returns the full database schema summary for the connected database. |

## resource://database/schema

### Description

Returns the complete database schema as JSON, including tables, columns, types, nullability, primary keys, foreign keys, indexes, and row counts. This resource is injected into the LLM system prompt so the model has full awareness of the database structure.

The schema is built using SQLAlchemy introspection over the Zen ODBC connection, with Zen-specific type mapping applied to each column.

### Input parameters

This resource doesn't require any input parameters.

### Output schema

```json
{
	"database": "demodata",
	"tables": {
		"<table_name>": {
			"columns": [
				{
					"name": "<column_name>",
					"type": "<sqlalchemy_type>",
					"zen_type": "<zen_native_type>",
					"nullable": true,
					"autoincrement": false,
					"length": 100
				}
			],
			"primary_key": ["<pk_column>"],
			"foreign_keys": [
				{
					"columns": ["<fk_column>"],
					"references_table": "<referenced_table>",
					"references_columns": ["<referenced_column>"]
				}
			],
			"indexes": [
				{
					"name": "<index_name>",
					"columns": ["<indexed_column>"],
					"unique": false
				}
			],
			"row_count": 42
		}
	},
	"summary": {
		"total_tables": 7,
		"total_columns": 35,
		"timestamp": "2026-03-27T10:00:00.000000"
	}
}
```

On error:

```json
{
	"error": "<error_message>"
}
```

### Example

```text
resource://database/schema
```

### Success response example

```json
{
	"database": "demodata",
	"tables": {
		"Person": {
			"columns": [
				{"name": "ID", "type": "BIGINT", "zen_type": "BIGIDENTITY", "nullable": false, "autoincrement": true},
				{"name": "First_Name", "type": "VARCHAR(30)", "zen_type": "VARCHAR", "nullable": true, "autoincrement": false, "length": 30},
				{"name": "Last_Name", "type": "VARCHAR(30)", "zen_type": "VARCHAR", "nullable": true, "autoincrement": false, "length": 30}
			],
			"primary_key": ["ID"],
			"foreign_keys": [],
			"indexes": [{"name": "Person_PK", "columns": ["ID"], "unique": true}],
			"row_count": 14
		},
		"Department": {
			"columns": [
				{"name": "ID", "type": "BIGINT", "zen_type": "BIGIDENTITY", "nullable": false, "autoincrement": true},
				{"name": "Name", "type": "VARCHAR(30)", "zen_type": "VARCHAR", "nullable": true, "autoincrement": false, "length": 30}
			],
			"primary_key": ["ID"],
			"foreign_keys": [],
			"indexes": [{"name": "Department_PK", "columns": ["ID"], "unique": true}],
			"row_count": 5
		}
	},
	"summary": {
		"total_tables": 2,
		"total_columns": 5,
		"timestamp": "2026-03-27T10:00:00.000000"
	}
}
```

## Next steps

- [Tools](../tools/index.md) — Learn about Zen tools
- [Prompts](../prompts/index.md) — Learn about Zen prompts
