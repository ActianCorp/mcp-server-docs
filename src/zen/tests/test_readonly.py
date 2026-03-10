# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""Tests for readonly mode: 6 tools registered, write guards active."""

import json
import sys
import pytest

from fastmcp import Client, FastMCP


EXPECTED_READONLY_TOOLS = [
    "execute_query",
    "list_tables",
    "describe_table",
    "orm_operation",
    "blob_operation",
    "database_manage"
]

EXCLUDED_TOOLS = ["ddl_operation", "batch_operation", "transaction"]


@pytest.fixture()
def server_readonly():
    """Readonly server — OPENMODE=1 connection, 6 tools."""
    from zen.plugin import SERVER_NAME, create_lifespan, SERVER_INSTRUCTIONS_READONLY
    from zen.core import ZenConfiguration

    config = ZenConfiguration()
    server = FastMCP(
        SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS_READONLY,
        lifespan=create_lifespan(config, readonly=True)
    )
    return server


@pytest.fixture()
async def readonly_client(server_readonly):
    original_argv = sys.argv
    sys.argv = ['actian-zen', '--transport', 'stdio']
    try:
        async with Client(server_readonly) as client:
            yield client
    finally:
        sys.argv = original_argv


# --- tool registration

@pytest.mark.asyncio
async def test_readonly_tool_count(readonly_client):
    tools = await readonly_client.list_tools()
    names = [t.name for t in tools]
    assert len(names) == 6, f"Expected 6, got {len(names)}: {names}"


@pytest.mark.asyncio
async def test_readonly_expected_tools(readonly_client):
    names = [t.name for t in await readonly_client.list_tools()]
    for t in EXPECTED_READONLY_TOOLS:
        assert t in names, f"Missing: {t}"


@pytest.mark.asyncio
async def test_readonly_excluded_tools(readonly_client):
    names = [t.name for t in await readonly_client.list_tools()]
    for t in EXCLUDED_TOOLS:
        assert t not in names, f"Should not be registered: {t}"


# --- read operations

@pytest.mark.asyncio
async def test_readonly_select_query(readonly_client):
    result = await readonly_client.call_tool(
        "execute_query",
        {"sql": "SELECT COUNT(*) AS cnt FROM Dept"}
    )
    data = json.loads(result.content[0].text)
    assert "error" not in data, data.get("error")
    assert "results" in data


@pytest.mark.asyncio
async def test_readonly_list_tables(readonly_client):
    data = json.loads((await readonly_client.call_tool("list_tables", {})).content[0].text)
    assert "tables" in data


@pytest.mark.asyncio
async def test_readonly_describe_table(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool("describe_table", {"table": "Dept"})).content[0].text
    )
    assert "columns" in data


@pytest.mark.asyncio
async def test_readonly_orm_select(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "orm_operation",
            {"operation": "select", "table": "employees", "limit": 3}
        )).content[0].text
    )
    assert "error" not in data


@pytest.mark.asyncio
async def test_readonly_blob_list(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "blob_operation",
            {"action": "list", "table_name": "Dept"}
        )).content[0].text
    )
    # table may have no blob columns, but should never get a readonly rejection
    if "error" in data:
        assert "readonly" not in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_database_manage(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool("database_manage", {"action": "capabilities"})).content[0].text
    )
    assert data["database"] == "Actian Zen"


# --- write guards

@pytest.mark.asyncio
async def test_readonly_execute_query_rejects_insert(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "INSERT INTO Dept (Name) VALUES ('test')"}
        )).content[0].text
    )
    assert "error" in data
    assert "select" in data["error"].lower() or "readonly" in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_execute_query_rejects_update(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "UPDATE Dept SET Name = 'x' WHERE 1=0"}
        )).content[0].text
    )
    assert "error" in data
    assert "select" in data["error"].lower() or "readonly" in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_execute_query_rejects_delete(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "DELETE FROM Dept WHERE 1=0"}
        )).content[0].text
    )
    assert "error" in data
    assert "select" in data["error"].lower() or "readonly" in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_orm_rejects_insert(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "orm_operation",
            {"operation": "insert", "table": "Dept", "data": {"Name": "test"}}
        )).content[0].text
    )
    assert "error" in data
    assert "readonly" in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_orm_rejects_update(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "orm_operation",
            {"operation": "update", "table": "Dept", "entity_id": 1, "data": {"Name": "x"}}
        )).content[0].text
    )
    assert "error" in data
    assert "readonly" in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_orm_rejects_delete(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "orm_operation",
            {"operation": "delete", "table": "Dept", "entity_id": 1}
        )).content[0].text
    )
    assert "error" in data
    assert "readonly" in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_blob_rejects_upload(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "blob_operation",
            {"action": "upload", "table_name": "Dept", "file_path": "test.txt"}
        )).content[0].text
    )
    assert "error" in data
    assert "readonly" in data["error"].lower()


@pytest.mark.asyncio
async def test_readonly_blob_rejects_delete(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "blob_operation",
            {"action": "delete", "table_name": "Dept", "file_id": 1}
        )).content[0].text
    )
    assert "error" in data
    assert "readonly" in data["error"].lower()



# --- second defense layer: LLM bypassing DDL tools via raw execute_query

@pytest.mark.asyncio
async def test_readonly_raw_create_table_intercepted(readonly_client):
    # ddl_operation is gone, but LLM could try raw CREATE via execute_query
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "CREATE TABLE bypass_test (id INTEGER)"}
        )).content[0].text
    )
    assert "error" in data
    assert "readonly" in data["error"].lower() or "SELECT" in data["error"]


@pytest.mark.asyncio
async def test_readonly_raw_drop_table_intercepted(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "DROP TABLE Dept"}
        )).content[0].text
    )
    assert "error" in data


@pytest.mark.asyncio
async def test_readonly_raw_update_intercepted(readonly_client):
    # WHERE 1=0 touches no rows but should still be blocked before execution
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "UPDATE Dept SET Name = 'x' WHERE 1=0"}
        )).content[0].text
    )
    assert "error" in data


@pytest.mark.asyncio
async def test_readonly_select_with_subquery_allowed(readonly_client):
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "SELECT Name FROM Dept WHERE Name IN (SELECT Name FROM Dept WHERE Room_Number > 0)"}
        )).content[0].text
    )
    assert "error" not in data
    assert "results" in data


@pytest.mark.asyncio
async def test_readonly_openmode_double_protection(readonly_client):
    # Python guard fires first; OPENMODE=1 on the Zen engine is a backup
    # if the guard were ever bypassed
    data = json.loads(
        (await readonly_client.call_tool(
            "execute_query",
            {"sql": "INSERT INTO Dept (Name) VALUES ('openmode_test')"}
        )).content[0].text
    )
    assert "results" not in data
    assert "error" in data
