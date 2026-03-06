# Copyright (C) 2026 Actian Corp.
# All Rights Reserved.
"""
MCP Integration Tests with LLM.

These tests verify MCP server functionality using real LLM interaction.
The LLM model is configured in conf.json.

Run with:
    pytest tests/test_mcp_integration.py -v

Requires:
    OPENROUTER_API_KEY environment variable
"""

import pytest
import json
from datetime import datetime
from pathlib import Path


# ════════════════════════════════════════════════════════════════════════════════
# Test Cases
# ════════════════════════════════════════════════════════════════════════════════

MCP_INTEGRATION_TESTS = [
    {
        "id": "list_databases",
        "name": "List All Databases",
        "prompt": "List all Zen databases (ODBC DSNs) available. Use database_manage with action='list_dsns'.",
        "success_keywords": ["dsn", "driver", "demodata"],
    },
    {
        "id": "cross_database",
        "name": "Cross-Database Query",
        "prompt": """Demonstrate cross-database capability:
1. Use database_manage with action='list' to show available databases
2. Return the list of available DSNs""",
        "success_keywords": ["available", "dsn", "demodata"],
    },
    {
        "id": "server_capabilities",
        "name": "Server Capabilities",
        "prompt": """Check database server capabilities:
1. Use database_manage with action='capabilities'
2. Print a summary of supported features""",
        "success_keywords": ["capabilities", "supported", "features"],
    },
    {
        "id": "lock_recovery",
        "name": "Lock Recovery",
        "prompt": """Demonstrate lock recovery:
1. Explain when Btrieve Error 85 occurs
2. Call database_manage with action='release_locks'""",
        "success_keywords": ["lock", "release", "error"],
    },
    {
        "id": "simple_query",
        "name": "Simple Query",
        "prompt": "Get the first 3 employees from the employees table using orm_operation or execute_query.",
        "success_keywords": ["employee", "result", "name"],
    },
    {
        "id": "table_creation",
        "name": "Create Table",
        "prompt": """Create a test table using execute_query:
- Table name: mcp_test_table
- Columns: id IDENTITY, name NVARCHAR(100), created_at DATETIME
Use mode='ddl_create_table'.""",
        "success_keywords": ["created", "table", "success"],
    },
    {
        "id": "transaction_flow",
        "name": "Transaction Flow",
        "prompt": """Execute a transaction:
1. Use transaction with action='begin'
2. Insert a row into mcp_test_table with name='Test Entry'
3. Use transaction with action='commit'""",
        "success_keywords": ["begin", "commit", "insert"],
    },
    {
        "id": "relationship_query",
        "name": "Relationship Navigation",
        "prompt": """Navigate table relationships:
1. Get customer with customer_id = 1 using orm_operation
2. Get invoices for that customer using a JOIN query""",
        "success_keywords": ["customer", "invoice", "join"],
    },
]


# ════════════════════════════════════════════════════════════════════════════════
# Trace Logging
# ════════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def trace_log_path():
    """Session-scoped JSONL log file for LLM trace records."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = Path(__file__).parent.parent / "results" / f"llm_trace_{ts}.jsonl"
    path.parent.mkdir(exist_ok=True)
    return path


# ════════════════════════════════════════════════════════════════════════════════
# Parametrized Tests
# ════════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize(
    "test_case",
    MCP_INTEGRATION_TESTS,
    ids=[t["id"] for t in MCP_INTEGRATION_TESTS]
)
async def test_mcp_integration(llm_client, test_case, trace_log_path):
    """
    Run MCP integration test with LLM.

    Each test sends a prompt to the LLM, which uses MCP tools to complete the task.
    Success is determined by presence of expected keywords in the response.
    Trace records are saved to a JSONL file for analysis.
    """
    prompt = test_case["prompt"]
    success_keywords = test_case["success_keywords"]

    # Execute via LLM
    response = await llm_client.chat(prompt)

    # Check for success indicators
    response_lower = response.lower()
    found_keywords = [kw for kw in success_keywords if kw in response_lower]
    success = len(found_keywords) > 0

    # Save trace record
    trace = llm_client.get_trace_record(test_case["id"], prompt, success)
    with open(trace_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace, ensure_ascii=False) + "\n")

    # At least one keyword should be present
    assert success, (
        f"Test '{test_case['name']}' failed.\n"
        f"Expected keywords: {success_keywords}\n"
        f"Response: {response[:500]}"
    )


