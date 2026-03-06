# Testing Layers — Actian Zen MCP Server

## Layer 1 — Unit / Tool Tests
`tests/test_server.py`, `test_execute_query_modes.py`, `test_bridge.py`, `test_oauth.py`, `test_readonly.py`

Individual tools and features tested in isolation via in-process stdio client.

Covers:
- Server startup and tool registration (full mode: 9 tools, readonly mode: 6 tools)
- SQL execution modes and auto-translation (LEN→CHAR_LENGTH, INFORMATION_SCHEMA→catalog functions)
- Catalog function bridge (fSQLTables, fSQLColumns, fSQLPrimaryKeys, fSQLForeignKeys)
- OAuth/OIDC middleware (JWT validation, Keycloak, Auth0)
- Readonly protection: write tool exclusion, Python SQL guards, OPENMODE=1 backstop

Run: `pytest tests/`

---

## Layer 2 — Integration Tests
`tests/test_mcp_integration.py`

Full MCP protocol round-trips over stdio transport. No LLM involved.

Covers:
- Client ↔ server handshake and tool discovery
- Tool call serialization and response parsing
- Multi-tool sequences (e.g. list_tables → describe_table → execute_query)
- Error propagation from DB to MCP response

Run: `pytest tests/test_mcp_integration.py`

---

## Layer 3 — Stress / Concurrency Tests
`tests/test_multitenancy.py` (marked `@pytest.mark.slow`)

Real server process started on a free port; clients connect over HTTP or SSE.

Covers:
- 10 / 50 / 100 parallel HTTP clients (`asyncio.gather`)
- 10 / 50 parallel SSE clients
- 20 sequential connect/disconnect cycles (connection pool stability)
- 50-client ping storm (rapid connect/ping/disconnect)
- Pass threshold: 90% success required

Run: `pytest tests/test_multitenancy.py -m slow`

---

## Layer 4 — LLM End-to-End Tests
`llm_test_harness/test_natural_language.py`, `run_breaking_tests_llm.py`, `run_regression_tests.py`

Real LLM (Ollama local or OpenRouter cloud) drives tool calls against a live database.

Covers:
- Natural language → SQL generation → execution → result interpretation
- LLM instruction compliance (readonly rules, schema grounding, dialect rules)
- Adversarial / breaking prompts (injection attempts, ambiguous requests, schema hallucination)
- Multi-turn conversations with tool call chains
- Model comparison across backends (Claude, Llama, Mistral)

Run: `pytest llm_test_harness/test_natural_language.py` (requires `OPENROUTER_API_KEY` or Ollama)
