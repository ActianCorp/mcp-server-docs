"""
Tests for zen.features.tools.register_zen_tools — tool registration.

Tests verify that register_zen_tools():
1. Registers all 9 tools
2. SQL regression suite passes through server-registered tools
"""

import re
import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock


class TestInitializeZenTools:
    """Test register_zen_tools function."""

    def _make_mock_server(self):
        registered_tools = {}

        class MockServer:
            def tool(self, name):
                def decorator(func):
                    registered_tools[name] = func
                    return func
                return decorator

            def remove_tool(self, name):
                registered_tools.pop(name, None)

        return MockServer(), registered_tools

    def test_initialize_registers_tools(self):
        """Test that register_zen_tools registers all 9 tools."""
        from zen.features.tools import register_zen_tools

        server, registered_tools = self._make_mock_server()
        conn = MagicMock()
        orm = MagicMock()
        ddl = MagicMock()
        file_mgr = MagicMock()

        register_zen_tools(server, conn, orm, ddl, file_mgr)

        expected = [
            "execute_query", "ddl_operation", "batch_operation",
            "list_tables", "describe_table", "orm_operation",
            "transaction", "blob_operation", "database_manage"
        ]
        for name in expected:
            assert name in registered_tools, f"Tool {name} not registered"
        assert len(registered_tools) == 9

    def test_bridge_execute_query(self):
        """Test execute_query tool is callable after registration."""
        from zen.features.tools import register_zen_tools

        server, registered_tools = self._make_mock_server()
        register_zen_tools(server, MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert "execute_query" in registered_tools
        assert callable(registered_tools["execute_query"])

    def test_bridge_list_tables(self):
        """Test list_tables tool is callable after registration."""
        from zen.features.tools import register_zen_tools

        server, registered_tools = self._make_mock_server()
        register_zen_tools(server, MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert "list_tables" in registered_tools
        assert callable(registered_tools["list_tables"])

    def test_bridge_describe_table(self):
        """Test describe_table tool is callable after registration."""
        from zen.features.tools import register_zen_tools

        server, registered_tools = self._make_mock_server()
        register_zen_tools(server, MagicMock(), MagicMock(), MagicMock(), MagicMock())

        assert "describe_table" in registered_tools
        assert callable(registered_tools["describe_table"])


# ---
# SQL Regression — same queries from sql_requests.md via MCP server

def _parse_sql_tests(md_path: str) -> list[tuple[str, str]]:
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    tests = []
    blocks = re.split(r'(?=^## TEST )', content, flags=re.MULTILINE)
    for block in blocks:
        id_match = re.match(r'^## TEST\s+(\S+)', block)
        if not id_match:
            continue
        sql_match = re.search(r'```sql\s*\n(.*?)```', block, re.DOTALL)
        if sql_match:
            tests.append((id_match.group(1), sql_match.group(1).strip()))
    return tests


_MD_PATH = Path(__file__).parent.parent / "llm_test_harness" / "model_dialogs" / "sql_requests.md"
_BRIDGE_SQL_TESTS = _parse_sql_tests(str(_MD_PATH)) if _MD_PATH.exists() else []


@pytest.mark.bridge_regression
class TestBridgeSQLRegression:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_id,sql", _BRIDGE_SQL_TESTS,
                             ids=[t[0] for t in _BRIDGE_SQL_TESTS])
    async def test_bridge_sql(self, stdio_client, test_id, sql):
        result = await stdio_client.call_tool("execute_query", {"sql": sql})
        data = json.loads(result.content[0].text)

        assert "error" not in data, f"SQL error on {test_id}: {data.get('error')}"
        assert "results" in data, f"No results key in response for {test_id}"
        assert len(data["results"]) > 0, f"Expected rows > 0 for {test_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
