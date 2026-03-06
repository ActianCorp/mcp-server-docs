# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

# SQL translation and edge cases through full ActianMCP → actian_zen bridge.

import json


async def test_len_to_char_length(stdio_client):
    result = await stdio_client.call_tool(
        "execute_query", {"sql": "SELECT LEN('hello') AS len_result"}
    )
    data = json.loads(result.content[0].text)
    results = data.get("results", [data] if isinstance(data, dict) else data)
    assert any(
        r.get("len_result") == 5 or r.get("len_result") == "5"
        for r in results
    )


async def test_constraint_name_truncation(stdio_client):
    result = await stdio_client.call_tool(
        "execute_query",
        {
            "sql": "CREATE TABLE test_trunc_combined (id INTEGER NOT NULL, "
            "CONSTRAINT this_is_a_very_long_constraint_name_that_exceeds_twenty PRIMARY KEY (id))"
        },
    )
    text = result.content[0].text
    assert "error" not in text.lower() or "already exists" in text.lower()

    # Cleanup
    await stdio_client.call_tool(
        "execute_query", {"sql": "DROP TABLE test_trunc_combined"}
    )


async def test_catalog_list_tables(stdio_client):
    result = await stdio_client.call_tool("list_tables", {})
    text = result.content[0].text
    assert "person" in text.lower()


async def test_catalog_describe_table_columns(stdio_client):
    result = await stdio_client.call_tool(
        "describe_table", {"table": "Person"}
    )
    text = result.content[0].text
    assert "last_name" in text.lower() or "first_name" in text.lower() or "id" in text.lower()


async def test_orm_insert_and_delete(stdio_client):
    # Create test table
    await stdio_client.call_tool(
        "execute_query",
        {"sql": "CREATE TABLE test_crud_combined (id INTEGER NOT NULL, name VARCHAR(50), PRIMARY KEY (id))"},
    )

    try:
        # Insert via ORM
        result = await stdio_client.call_tool(
            "orm_operation",
            {
                "operation": "insert",
                "table": "test_crud_combined",
                "data": {"id": 1, "name": "test_row"},
            },
        )
        text = result.content[0].text
        assert "error" not in text.lower()

        # Select to verify
        result = await stdio_client.call_tool(
            "orm_operation",
            {
                "operation": "select",
                "table": "test_crud_combined",
                "where": {"id": 1},
            },
        )
        data = json.loads(result.content[0].text)
        results = data.get("results", data.get("rows", [data] if isinstance(data, dict) else data))
        assert len(results) >= 1

        # Delete via SQL (ORM delete requires entity_id from insert)
        result = await stdio_client.call_tool(
            "execute_query",
            {"sql": "DELETE FROM test_crud_combined WHERE id = 1"},
        )
        text = result.content[0].text
        assert "error" not in text.lower()
    finally:
        # Cleanup
        await stdio_client.call_tool(
            "execute_query", {"sql": "DROP TABLE test_crud_combined"}
        )


async def test_invalid_table_error(stdio_client):
    result = await stdio_client.call_tool(
        "execute_query",
        {"sql": "SELECT * FROM nonexistent_table_xyz_12345"},
    )
    text = result.content[0].text
    assert "error" in text.lower() or "not found" in text.lower() or "does not exist" in text.lower()


async def test_transaction_begin_rollback(stdio_client):
    # Begin
    result = await stdio_client.call_tool(
        "transaction", {"action": "begin"}
    )
    text = result.content[0].text
    assert "error" not in text.lower()

    # Rollback
    result = await stdio_client.call_tool(
        "transaction", {"action": "rollback"}
    )
    text = result.content[0].text
    assert "error" not in text.lower()


