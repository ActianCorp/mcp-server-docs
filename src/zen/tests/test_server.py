# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""
Server tests for actian-zen MCP server.

Tests tool registration, resource availability, and basic operations.
"""

import json
import pytest

# Expected tools (9-tool Phase 24 version)
EXPECTED_TOOLS = [
    "execute_query",
    "ddl_operation",
    "batch_operation",
    "list_tables",
    "describe_table",
    "orm_operation",
    "transaction",
    "blob_operation",
    "database_manage"
]

# Expected resources
EXPECTED_RESOURCES = [
    "schema",
]


# ════════════════════════════════════════════════════════════════════════════════
# Server Reachability Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_server_ping(stdio_client):
    """Test that server responds to ping."""
    response = await stdio_client.ping()
    assert response is not None


@pytest.mark.asyncio
async def test_server_connected(stdio_client):
    """Test that client is connected."""
    assert stdio_client is not None


# ════════════════════════════════════════════════════════════════════════════════
# Tool Registration Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tools_list(stdio_client):
    """Verify all 9 tools are registered."""
    tools = await stdio_client.list_tools()
    tool_names = [t.name for t in tools]

    assert len(tool_names) == 9, f"Expected 9 tools, got {len(tool_names)}: {tool_names}"

    for expected_tool in EXPECTED_TOOLS:
        assert expected_tool in tool_names, f"Missing tool: {expected_tool}"


@pytest.mark.asyncio
async def test_tools_have_descriptions(stdio_client):
    """Verify all tools have descriptions."""
    tools = await stdio_client.list_tools()

    for tool in tools:
        assert tool.description, f"Tool {tool.name} has no description"
        assert len(tool.description) > 20, f"Tool {tool.name} description too short"


# ════════════════════════════════════════════════════════════════════════════════
# Resource Registration Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_resources_list(stdio_client):
    """Verify schema resource is registered."""
    resources = await stdio_client.list_resources()

    assert len(resources) == 1, f"Expected 1 resource, got {len(resources)}"

    resource_names = [str(r.uri).split("/")[-1] for r in resources]
    for expected_resource in EXPECTED_RESOURCES:
        assert expected_resource in resource_names, f"Missing resource: {expected_resource}"


# ════════════════════════════════════════════════════════════════════════════════
# Tool Execution Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_tool_execute_query_select(stdio_client):
    """Test execute_query tool with SELECT query."""
    result = await stdio_client.call_tool(
        "execute_query",
        {"sql": "SELECT COUNT(*) AS cnt FROM employees"}
    )

    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Query failed: {data.get('error')}"
    assert "results" in data or "row_count" in data


@pytest.mark.asyncio
async def test_tool_list_tables(stdio_client):
    """Test list_tables tool returns table list."""
    result = await stdio_client.call_tool("list_tables", {})

    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Failed: {data.get('error')}"
    assert "tables" in data
    assert "count" in data
    assert data["count"] > 0


@pytest.mark.asyncio
async def test_tool_describe_table(stdio_client):
    """Test describe_table tool returns schema info."""
    result = await stdio_client.call_tool(
        "describe_table",
        {"table": "employees"}
    )

    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Failed: {data.get('error')}"
    assert "table_name" in data
    assert data["table_name"] == "employees"
    assert "columns" in data
    assert len(data["columns"]) > 0
    assert "primary_keys" in data


@pytest.mark.asyncio
async def test_tool_orm_operation_select(stdio_client):
    """Test orm_operation select."""
    result = await stdio_client.call_tool(
        "orm_operation",
        {
            "operation": "select",
            "table": "employees",
            "columns": ["employee_id", "first_name"],
            "limit": 5
        }
    )

    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Query failed: {data.get('error')}"


@pytest.mark.asyncio
async def test_tool_database_manage_capabilities(stdio_client):
    """Test database_manage capabilities action."""
    result = await stdio_client.call_tool(
        "database_manage",
        {"action": "capabilities"}
    )

    data = json.loads(result.content[0].text)
    assert "error" not in data, f"Failed: {data.get('error')}"
    assert "database" in data
    assert data["database"] == "Actian Zen"


@pytest.mark.asyncio
async def test_tool_transaction_operations(stdio_client):
    """Test transaction begin/rollback."""
    # Begin transaction
    result = await stdio_client.call_tool("transaction", {"action": "begin"})
    data = json.loads(result.content[0].text)
    assert data.get("success") or "active" in str(data).lower()

    # Rollback (don't commit test changes)
    result = await stdio_client.call_tool("transaction", {"action": "rollback"})
    data = json.loads(result.content[0].text)
    assert "error" not in data or data.get("success")


# ════════════════════════════════════════════════════════════════════════════════
# Resource Access Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_resource_schema(stdio_client):
    """Test schema resource contains expected structure."""
    result = await stdio_client.read_resource("resource://database/schema")
    schema = json.loads(result[0].text)

    assert "tables" in schema, "Schema missing 'tables' key"
    assert "employees" in schema["tables"], "Schema missing 'employees' table"
    assert "summary" in schema, "Schema missing 'summary'"


