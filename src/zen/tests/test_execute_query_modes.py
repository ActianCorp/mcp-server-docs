# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""
Tests for execute_query, ddl_operation, and batch_operation tools.

Phase 24: Split from monolithic execute_query into 3 focused tools.
"""

import json
import pytest


# ════════════════════════════════════════════════════════════════════════════════
# select_only mode (execute_query)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_select_allows_select(stdio_client):
    """execute_query accepts SELECT queries."""
    result = await stdio_client.call_tool(
        "execute_query",
        {"sql": "SELECT 1 AS val"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data
    assert data["results"][0]["val"] == 1


# ════════════════════════════════════════════════════════════════════════════════
# count mode (batch_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_count_mode(stdio_client):
    """count mode returns row count for a table."""
    result = await stdio_client.call_tool(
        "batch_operation",
        {"mode": "count", "table": "employees"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"count failed: {data.get('error')}"
    assert "row_count" in data
    assert data["row_count"] > 0


@pytest.mark.asyncio
async def test_count_mode_with_where(stdio_client):
    """count mode with where_clause."""
    result = await stdio_client.call_tool(
        "batch_operation",
        {"mode": "count", "table": "employees", "where_clause": "employee_id > 0"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"count failed: {data.get('error')}"
    assert "row_count" in data


@pytest.mark.asyncio
async def test_count_mode_requires_table(stdio_client):
    """count mode returns error without table."""
    result = await stdio_client.call_tool(
        "batch_operation",
        {"mode": "count", "table": ""}
    )
    data = json.loads(result.content[0].text)
    assert "error" in data


# ════════════════════════════════════════════════════════════════════════════════
# SQL translation (execute_query)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_translation_len_to_char_length(stdio_client):
    """LEN() is translated to CHAR_LENGTH()."""
    result = await stdio_client.call_tool(
        "execute_query",
        {"sql": "SELECT LEN('hello') AS len_val"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Translation failed: {data.get('error')}"
    assert data["results"][0]["len_val"] == 5
    assert data.get("translated") is True
    assert "CHAR_LENGTH" in data.get("translation_note", "")


@pytest.mark.asyncio
async def test_translation_information_schema(stdio_client):
    """INFORMATION_SCHEMA.TABLES is translated to dbo.fSQLTables()."""
    result = await stdio_client.call_tool(
        "execute_query",
        {"sql": "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'TABLE'"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Translation failed: {data.get('error')}"
    assert data.get("translated") is True
    assert len(data["results"]) > 0


@pytest.mark.asyncio
async def test_translation_constraint_truncation():
    """Constraint names > 20 chars are truncated."""
    from zen.features.tools import _truncate_constraint_names_in_sql
    sql = 'ALTER TABLE t ADD CONSTRAINT very_long_constraint_name_here FOREIGN KEY (id) REFERENCES t2(id)'
    result = _truncate_constraint_names_in_sql(sql)
    assert "very_long_constraint" in result
    # Original 30-char name should be truncated to 20
    assert "very_long_constraint_name_here" not in result


@pytest.mark.asyncio
async def test_translation_rename_column_rejected(stdio_client):
    """RENAME COLUMN raises error (Zen doesn't support it)."""
    result = await stdio_client.call_tool(
        "execute_query",
        {"sql": "ALTER TABLE employees RENAME COLUMN first_name TO fname"}
    )
    data = json.loads(result.content[0].text)
    assert "error" in data
    assert "RENAME COLUMN" in data["error"]


@pytest.mark.asyncio
async def test_translation_key_column_usage_fk(stdio_client):
    """KEY_COLUMN_USAGE translation returns PK+FK columns via fSQLPrimaryKeys()+fSQLForeignKeys()."""
    result = await stdio_client.call_tool(
        "execute_query",
        {"sql": "SELECT CONSTRAINT_NAME, TABLE_NAME, COLUMN_NAME, ORDINAL_POSITION FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE WHERE TABLE_NAME = 'Invoices'"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Translation failed: {data.get('error')}"
    assert data.get("translated") is True
    assert len(data["results"]) > 0
    # Verify expected columns are present in result rows
    first_row = data["results"][0]
    assert "CONSTRAINT_NAME" in first_row
    assert "COLUMN_NAME" in first_row


# ════════════════════════════════════════════════════════════════════════════════
# DDL TABLE operations (ddl_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_ddl_create_and_drop_table(stdio_client):
    """Create table then drop it."""
    # Drop first in case leftover from previous run
    await stdio_client.call_tool(
        "ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_ddl_ph19"}
    )

    # Create
    result = await stdio_client.call_tool(
        "ddl_operation",
        {
            "mode": "ddl_create_table",
            "table": "test_ddl_ph19",
            "columns": [
                {"name": "id", "type": "IDENTITY"},
                {"name": "name", "type": "NVARCHAR", "length": 50},
                {"name": "value", "type": "INTEGER"}
            ]
        }
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Create failed: {data.get('error')}"

    # Verify table exists via list_tables
    lt = await stdio_client.call_tool("list_tables", {})
    lt_data = json.loads(lt.content[0].text)
    assert "test_ddl_ph19" in lt_data["tables"]

    # Drop
    result = await stdio_client.call_tool(
        "ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_ddl_ph19"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Drop failed: {data.get('error')}"


@pytest.mark.asyncio
async def test_ddl_create_table_requires_columns(stdio_client):
    """ddl_create_table requires table and columns."""
    result = await stdio_client.call_tool(
        "ddl_operation",
        {"mode": "ddl_create_table", "table": "x"}
    )
    data = json.loads(result.content[0].text)
    assert "error" in data


@pytest.mark.asyncio
async def test_ddl_rename_table(stdio_client):
    """Rename table then clean up."""
    # Setup
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_ren_src"})
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_ren_dst"})

    await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_table",
        "table": "test_ren_src",
        "columns": [{"name": "id", "type": "IDENTITY"}]
    })

    # Rename
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_rename_table",
        "table": "test_ren_src",
        "new_name": "test_ren_dst"
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Rename failed: {data.get('error')}"

    # Verify new name exists
    lt = await stdio_client.call_tool("list_tables", {})
    lt_data = json.loads(lt.content[0].text)
    assert "test_ren_dst" in lt_data["tables"]

    # Cleanup
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_ren_dst"})


# ════════════════════════════════════════════════════════════════════════════════
# DDL COLUMN operations (ddl_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
async def ddl_column_table(stdio_client):
    """Create a table for column DDL tests, drop after."""
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_col_ph19"})
    await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_table",
        "table": "test_col_ph19",
        "columns": [
            {"name": "id", "type": "IDENTITY"},
            {"name": "name", "type": "NVARCHAR", "length": 50}
        ]
    })
    yield "test_col_ph19"
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_col_ph19"})


@pytest.mark.asyncio
async def test_ddl_add_column(stdio_client, ddl_column_table):
    """Add a column to existing table."""
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_add_column",
        "table": ddl_column_table,
        "column_name": "email",
        "column_type": "NVARCHAR",
        "length": 100
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Add column failed: {data.get('error')}"

    # Verify column exists via describe_table
    desc = await stdio_client.call_tool("describe_table", {"table": ddl_column_table})
    desc_data = json.loads(desc.content[0].text)
    col_names = [c["name"] for c in desc_data["columns"]]
    assert "email" in col_names


@pytest.mark.asyncio
async def test_ddl_drop_column(stdio_client, ddl_column_table):
    """Drop a column from existing table."""
    # Add then drop
    await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_add_column",
        "table": ddl_column_table,
        "column_name": "temp_col",
        "column_type": "INTEGER"
    })

    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_drop_column",
        "table": ddl_column_table,
        "column_name": "temp_col"
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Drop column failed: {data.get('error')}"


@pytest.mark.asyncio
async def test_ddl_add_column_requires_params(stdio_client):
    """ddl_add_column requires table, column_name, column_type."""
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_add_column",
        "table": "x"
    })
    data = json.loads(result.content[0].text)
    assert "error" in data


# ════════════════════════════════════════════════════════════════════════════════
# DDL INDEX operations (ddl_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
async def ddl_index_table(stdio_client):
    """Create a table for index DDL tests, drop after."""
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_idx_ph19"})
    await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_table",
        "table": "test_idx_ph19",
        "columns": [
            {"name": "id", "type": "IDENTITY"},
            {"name": "name", "type": "NVARCHAR", "length": 50},
            {"name": "salary", "type": "INTEGER"}
        ]
    })
    yield "test_idx_ph19"
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_idx_ph19"})


@pytest.mark.asyncio
async def test_ddl_create_and_drop_index(stdio_client, ddl_index_table):
    """Create then drop an index."""
    # Create index
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_index",
        "table": ddl_index_table,
        "index_name": "idx_sal_ph19",
        "index_columns": ["salary"]
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Create index failed: {data.get('error')}"

    # Drop index
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_drop_index",
        "table": ddl_index_table,
        "index_name": "idx_sal_ph19",
        "index_columns": ["salary"]
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Drop index failed: {data.get('error')}"


# ════════════════════════════════════════════════════════════════════════════════
# DDL VIEW operations (ddl_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_ddl_create_and_drop_view(stdio_client):
    """Create then drop a view."""
    # Drop in case leftover
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_view", "name": "vw_test_ph19"})

    # Create view
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_view",
        "name": "vw_test_ph19",
        "select_clause": "SELECT employee_id, first_name FROM employees"
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Create view failed: {data.get('error')}"

    # Query through the view
    q = await stdio_client.call_tool("execute_query",
        {"sql": "SELECT * FROM vw_test_ph19"})
    q_data = json.loads(q.content[0].text)
    assert "error" not in q_data
    assert len(q_data["results"]) > 0

    # Drop view
    result = await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_view", "name": "vw_test_ph19"})
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Drop view failed: {data.get('error')}"


@pytest.mark.asyncio
async def test_ddl_create_view_requires_params(stdio_client):
    """ddl_create_view requires name and select_clause."""
    result = await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_create_view", "name": "x"})
    data = json.loads(result.content[0].text)
    assert "error" in data


# ════════════════════════════════════════════════════════════════════════════════
# DDL PROCEDURE operations (ddl_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_ddl_create_and_drop_procedure(stdio_client):
    """Create then drop a stored procedure."""
    # Drop in case leftover
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_procedure", "name": "sp_test_ph19"})

    # Create procedure — no parameters to avoid SQLAlchemy bind-param issue
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_procedure",
        "name": "sp_test_ph19",
        "parameters": [],
        "body": "SELECT * FROM employees;"
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Create procedure failed: {data.get('error')}"

    # Drop procedure
    result = await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_procedure", "name": "sp_test_ph19"})
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Drop procedure failed: {data.get('error')}"


# ════════════════════════════════════════════════════════════════════════════════
# DDL FUNCTION operations (ddl_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_ddl_create_and_drop_function(stdio_client):
    """Create then drop a user-defined function."""
    # Drop in case leftover
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_function", "name": "fn_test_ph19"})

    # Create function — no parameters to avoid SQLAlchemy bind-param issue
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_function",
        "name": "fn_test_ph19",
        "parameters": [],
        "returns": "INTEGER",
        "body": "RETURN 42;"
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Create function failed: {data.get('error')}"

    # Drop function
    result = await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_function", "name": "fn_test_ph19"})
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Drop function failed: {data.get('error')}"


# ════════════════════════════════════════════════════════════════════════════════
# DDL TRIGGER operations (ddl_operation)
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
async def ddl_trigger_table(stdio_client):
    """Create a table for trigger DDL tests, drop after."""
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_trg_ph19"})
    await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_table",
        "table": "test_trg_ph19",
        "columns": [
            {"name": "id", "type": "IDENTITY"},
            {"name": "val", "type": "INTEGER"}
        ]
    })
    yield "test_trg_ph19"
    # Drop trigger first (may fail if already dropped), then table
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_trigger", "name": "trg_test_ph19"})
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_trg_ph19"})


@pytest.mark.asyncio
async def test_ddl_create_and_drop_trigger(stdio_client, ddl_trigger_table):
    """Create then drop a trigger."""
    # Create trigger — AFTER INSERT with a simple valid SQL body
    result = await stdio_client.call_tool("ddl_operation", {
        "mode": "ddl_create_trigger",
        "name": "trg_test_ph19",
        "table": ddl_trigger_table,
        "timing": "AFTER",
        "event": "INSERT",
        "body": "SELECT 1;"
    })
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Create trigger failed: {data.get('error')}"

    # Drop trigger
    result = await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_trigger", "name": "trg_test_ph19"})
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Drop trigger failed: {data.get('error')}"


# ════════════════════════════════════════════════════════════════════════════════
# database_manage additional actions
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_database_manage_list(stdio_client):
    """database_manage list action returns DSNs."""
    result = await stdio_client.call_tool(
        "database_manage", {"action": "list"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"list failed: {data.get('error')}"
    assert "available_dsns" in data
    assert "current_dsn" in data


@pytest.mark.asyncio
async def test_database_manage_list_dsns(stdio_client):
    """database_manage list_dsns action returns detailed DSN info."""
    result = await stdio_client.call_tool(
        "database_manage", {"action": "list_dsns"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"list_dsns failed: {data.get('error')}"
    assert "dsns" in data
    assert "count" in data


@pytest.mark.asyncio
async def test_database_manage_release_locks(stdio_client):
    """database_manage release_locks action succeeds."""
    result = await stdio_client.call_tool(
        "database_manage", {"action": "release_locks"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, f"release_locks failed: {data.get('error')}"


@pytest.mark.asyncio
async def test_database_manage_unknown_action(stdio_client):
    """database_manage with unknown action returns error."""
    result = await stdio_client.call_tool(
        "database_manage", {"action": "nonexistent"}
    )
    data = json.loads(result.content[0].text)
    assert "error" in data


# ════════════════════════════════════════════════════════════════════════════════
# describe_table edge cases
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_describe_table_shows_primary_key(stdio_client):
    """describe_table marks primary key columns on a table with explicit PK."""
    # Create a table with an explicit primary key
    await stdio_client.call_tool("ddl_operation",
        {"mode": "ddl_drop_table", "table": "test_pk_ph19"})
    await stdio_client.call_tool("execute_query",
        {"sql": "CREATE TABLE test_pk_ph19 (id INTEGER NOT NULL, name NVARCHAR(50), PRIMARY KEY (id))"})

    try:
        result = await stdio_client.call_tool(
            "describe_table", {"table": "test_pk_ph19"}
        )
        data = json.loads(result.content[0].text)
        assert "error" not in data
        assert len(data["primary_keys"]) > 0
        # The 'id' column should have primary_key=True
        pk_cols = [c for c in data["columns"] if c["primary_key"]]
        assert len(pk_cols) > 0
        assert pk_cols[0]["name"] == "id"
    finally:
        await stdio_client.call_tool("ddl_operation",
            {"mode": "ddl_drop_table", "table": "test_pk_ph19"})


@pytest.mark.asyncio
async def test_describe_nonexistent_table(stdio_client):
    """describe_table on nonexistent table returns empty or error."""
    result = await stdio_client.call_tool(
        "describe_table", {"table": "nonexistent_table_xyz"}
    )
    data = json.loads(result.content[0].text)
    # Either error or empty columns
    if "error" not in data:
        assert len(data["columns"]) == 0


# ════════════════════════════════════════════════════════════════════════════════
# list_tables validation
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_list_tables_contains_employees(stdio_client):
    """list_tables includes known table 'employees'."""
    result = await stdio_client.call_tool("list_tables", {})
    data = json.loads(result.content[0].text)
    assert "error" not in data
    assert "employees" in data["tables"]
