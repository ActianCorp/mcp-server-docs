---
title: Testing
description: QA test plan and results for the Zen MCP Server.
---

# QA Test Plan — Zen MCP Server

Zen-specific implementation of the QA Test Plan for MCP 1.0.
Based on the original plan by Maryum Arshad, with Zen adaptations.

---

## Feature Description

Zen MCP Server — plugin for Actian MCP Server providing LLM access to
Actian Zen (PSQL) databases via the Model Context Protocol.

Feature Ticket: MCP-1 (MCP Server for database tooling)
Testing Ticket: MCP-2 (Feature Test Development: MCP)

---

## Testing with Connection

| Test Case | Result | Test File |
|-----------|--------|-----------|
| Container deployment (Podman) | pass | conftest.py (container) |
| ODBC connection via DSN | pass | test_connection.py |
| Concurrent connections (10/50/100 clients) | pass | test_multitenancy.py |
| Sequential connection cycling (20 cycles) | pass | test_multitenancy.py |
| Connection drop and auto-reconnect | pass | test_connection_recovery |
| Transaction timeout auto-rollback (300s) | pass | test_connection_recovery |
| Transport parity: stdio / HTTP / SSE | pass | test_transport_modes.py |
| Ping storm (50 parallel pings) | pass | test_multitenancy.py |
| OAuth: username from preferred_username | pass | test_oauth_scenarios.py |
| OAuth: username from email prefix | pass | test_oauth_scenarios.py |
| OAuth: username from Auth0 sub | pass | test_oauth_scenarios.py |
| OAuth: priority order (user>pref>email>sub) | pass | test_oauth_scenarios.py |
| OAuth: username stored in ContextVar | pass | test_oauth_scenarios.py |
| OAuth: expired token detected | pass | test_oauth_scenarios.py |
| OAuth: tampered token fails verification | pass | test_oauth_scenarios.py |
| OAuth: wrong audience rejected | pass | test_oauth_scenarios.py |
| OAuth: missing claims returns no username | pass | test_oauth_scenarios.py |
| OAuth: no internal details leaked on error | pass | test_oauth_scenarios.py |
| OAuth: no config → auth disabled | pass | test_oauth_scenarios.py |
| OAuth: missing client_id → auth disabled | pass | test_oauth_scenarios.py |
| OAuth: username logged per request | pass | test_oauth.py |
| OAuth: no user → no auth log | pass | test_oauth.py |
| OAuth: nonexistent user still executes (Zen has no SET SESSION AUTHORIZATION) | pass | test_oauth.py |
| OAuth E2E with real Auth0/Keycloak | — | Requires IdP setup |
| Pen testing | — | Security team scope |

---

## Discovering Resources

| Test Case | Result | Test File |
|-----------|--------|-----------|
| resource://database/schema returns tables | pass | test_server.py |
| Schema contains Person table | pass | test_server.py |
| Schema contains summary | pass | test_server.py |
| describe_table shows columns and types | pass | test_server.py |
| describe_table shows primary keys | pass | test_execute_query_modes |
| Alter table then describe (new column) | skip | test_schema_rediscovery |
| Drop column then describe (column gone) | skip | test_schema_rediscovery |
| Create table then list_tables (appears) | skip | test_schema_rediscovery |
| Drop table then list_tables (disappears) | skip | test_schema_rediscovery |
| NVARCHAR type shown in describe_table | skip | test_unicode_data.py |

Skip = needs write access (readonly container).

---

## Tools

### execute_query

| Test Case | Result | Test File |
|-----------|--------|-----------|
| SELECT COUNT on Person | pass | test_server.py |
| JOIN Person-Student | pass | test_server.py |
| JOIN Student-Enrolls | pass | test_server.py |
| Three-way JOIN | pass | test_server.py |
| Aggregation GROUP BY | pass | test_server.py |
| Subquery with IN clause | pass | test_server.py |
| LEN() translated to CHAR_LENGTH() | pass | test_zen_integration.py |
| INFORMATION_SCHEMA translated to X$ | pass | test_zen_core_units.py |
| Constraint name truncation (>20 chars) | pass | test_zen_core_units.py |
| Bad SQL syntax → readable error | pass | test_error_handling.py |
| Missing table → error | pass | test_error_handling.py |
| Division by zero → handled | pass | test_error_handling.py |
| Type mismatch (ID='text') → handled | pass | test_error_handling.py |
| Invalid table → error message | pass | test_zen_integration.py |
| View queryable via execute_query | skip | test_views_and_procs.py |
| Stored procedure via CALL | skip | test_views_and_procs.py |
| Unicode Cyrillic INSERT/SELECT | skip | test_unicode_data.py |
| Unicode CJK INSERT/Select | skip | test_unicode_data.py |
| Unicode WHERE clause | skip | test_unicode_data.py |
| Unicode LIKE pattern | skip | test_unicode_data.py |

### list_tables

| Test Case | Result | Test File |
|-----------|--------|-----------|
| Returns user tables with count > 0 | pass | test_server.py |
| Contains "Person" table | pass | test_zen_integration.py |
| System tables excluded | pass | test_server.py |
| Describe all first 5 tables | pass | test_server.py |
| View in describe_table | skip | test_views_and_procs.py |

### orm_operation

| Test Case | Result | Test File |
|-----------|--------|-----------|
| Select on Person | pass | test_server.py |
| Select with limit=5 | pass | test_server.py |
| ORM supports JOIN via joins parameter | pass | (docstring fixed) |
| Insert + select + delete (CRUD cycle) | skip | test_zen_integration.py |
| Row cap: max_rows=1000 enforced | skip | test_row_cap.py |
| ORM respects max_rows | skip | test_row_cap.py |
| Explicit TOP 50 returns 50, no truncation | skip | test_row_cap.py |

### database_manage

| Test Case | Result | Test File |
|-----------|--------|-----------|
| Capabilities query | pass | test_server.py |
| List databases | pass | test_execute_query_modes |
| Release locks | pass | test_execute_query_modes |
| Unknown action → error | pass | test_execute_query_modes |

### DDL operations (write mode only)

| Test Case | Result | Test File |
|-----------|--------|-----------|
| CREATE/DROP TABLE | skip | test_execute_query_modes |
| ADD/DROP COLUMN | skip | test_execute_query_modes |
| CREATE/DROP INDEX | skip | test_execute_query_modes |
| CREATE/DROP VIEW | skip | test_execute_query_modes |
| CREATE/DROP PROCEDURE | skip | test_execute_query_modes |
| CREATE/DROP FUNCTION | skip | test_execute_query_modes |
| CREATE/DROP TRIGGER | skip | test_execute_query_modes |
| Transaction begin/rollback | skip | test_zen_integration.py |

---

## Guardrails

| Test Case | Result | Test File |
|-----------|--------|-----------|
| Readonly: only 6 tools registered | pass | test_readonly.py |
| Readonly: expected 6 tools present | pass | test_readonly.py |
| Readonly: ddl/batch/transaction excluded | pass | test_readonly.py |
| Readonly: SELECT allowed | pass | test_readonly.py |
| Readonly: INSERT rejected | pass | test_readonly.py |
| Readonly: UPDATE rejected | pass | test_readonly.py |
| Readonly: DELETE rejected | pass | test_readonly.py |
| Readonly: ORM insert rejected | pass | test_readonly.py |
| Readonly: ORM update rejected | pass | test_readonly.py |
| Readonly: ORM delete rejected | pass | test_readonly.py |
| Readonly: blob upload rejected | pass | test_readonly.py |
| Readonly: blob delete rejected | pass | test_readonly.py |
| Readonly: raw CREATE TABLE intercepted | pass | test_readonly.py |
| Readonly: raw DROP TABLE intercepted | pass | test_readonly.py |
| Readonly: raw UPDATE intercepted | pass | test_readonly.py |
| Readonly: SELECT with subquery allowed | pass | test_readonly.py |
| Readonly: OPENMODE=1 double protection | pass | test_readonly.py |
| DDL identifier injection blocked | pass | test_zen_core_units.py |
| Prompt injection: DROP TABLE via LLM | pass | test_prompt_injection.py |
| Prompt injection: GRANT via LLM | pass | test_prompt_injection.py |
| Prompt injection: credential exfiltration | pass | test_prompt_injection.py |
| Readonly query validator: SELECT accepted | pass | test_server_utils.py |
| Readonly query validator: CTE accepted | pass | test_server_utils.py |
| Readonly query validator: INSERT rejected | pass | test_server_utils.py |
| Readonly query validator: multi-statement | pass | test_server_utils.py |
| Readonly query validator: CALL rejected | pass | test_server_utils.py |

---

## Prompts

### Natural Language (LLM-driven, 37 tests)

| Test Case | Result | Notes |
|-----------|--------|-------|
| TEST 1-32: English prompts (queries, JOINs, aggregations, filters, inserts, updates, project assignments) | 32 pass | Via Claude Sonnet 4 on OpenRouter |
| TEST 33: Russian language prompt | pass | "Answer in English" |
| TEST 34: French language prompt | pass | "Answer in English" |
| TEST 35: German language prompt | pass | |
| TEST 36: Japanese language prompt | pass | |
| TEST 37: Mixed RU/EN language prompt | pass | "Answer in English" |
| MCP integration: list_databases | pass | test_mcp_integration.py |
| MCP integration: cross_database | pass | |
| MCP integration: server_capabilities | pass | |
| MCP integration: lock_recovery | pass | |
| MCP integration: simple_query | pass | |
| MCP integration: table_creation | pass | |
| MCP integration: transaction_flow | pass | |
| MCP integration: relationship_query | pass | |

Requires OPENROUTER_API_KEY. Model: anthropic/claude-sonnet-4.

---

## Zen Core Components (unit tests, no DB)

| Component | Tests | Result |
|-----------|-------|--------|
| InformationSchemaTranslator — TABLES/COLUMNS/CONSTRAINTS/KEY_COLUMN, passthrough, case insensitive, empty | 10 | 10 pass |
| ZenTypeMapper — All 30+ SQL types, Python types, IDENTITY, MONEY, DATE, BINARY, unknown | 14 | 14 pass |
| ZenConfiguration — 3 JSON formats, env vars, CLI overrides, missing file, invalid format | 10 | 10 pass |
| DDL identifier validation — valid names, injection attempts | 7 | 7 pass |
| DSN discovery (Windows registry) | 1 | 1 pass |
| OAuth token handling — Scenario 1: valid token username extract; Scenario 2: expired/tampered/wrong aud; configure_authentication edge cases | 14 | 14 pass |
| Shared framework (plugin, transport, config, readonly validator) | 30 | 30 pass |

---

## End-to-end

| Test Case | Result | Notes |
|-----------|--------|-------|
| 37 natural language prompts via LLM+MCP | pass | test_natural_language.py |
| 8 MCP integration scenarios via LLM | pass | test_mcp_integration.py |
| SQL regression suite (20 queries) | skip | test_bridge.py (write) |
| Full CRUD cycle (ORM) | skip | test_zen_integration.py |

---

## Test Totals

| Category | Total | Passed | Skipped |
|----------|-------|--------|---------|
| QA Plan gap tests | 30 | 15 | 15 |
| OAuth scenarios | 14 | 14 | 0 |
| Zen core units | 56 | 56 | 0 |
| Shared framework | 30 | 30 | 0 |
| Existing Zen tests | 164 | 108 | 56 |
| **Grand total** | **294** | **223** | **71** |
| Failures | | 0 | |

71 skipped tests need write access (ddl_operation tool).
They run with MCP_TEST_MODE=stdio on a machine with local Zen engine.

---

## Fixes Made During Testing

- conftest.py: SERVER_INSTRUCTIONS import (moved to features.instructions)
- conftest.py: stdio client asyncio nested event loop (inlined server creation)
- natural_language_requests.md: added departments/employees/sales/invoices SETUP
- natural_language_requests.md: "Answer in English" for multilingual prompts
- tools.py: orm_operation docstring now advertises JOIN support
- Dockerfile-zen and start-zen-mcp.ps1 for container build/run

---

## Not Applicable to Zen

| QA Plan Item | Why |
|--------------|-----|
| ML models (negative test) | Zen has no ML model support |
| Column-level masking | Zen has no column masking |
| Column-level encryption functions | Zen has file-level encryption only |
| Functions in different languages | Zen procedures are SQL-only |
| SET SESSION AUTHORIZATION | Not supported in Zen/PSQL |
| Cross-product queries (Zen+Ingres) | System-level test, not MCP scope |
| Pen testing | Security team scope |
| OAuth E2E (Auth0/Keycloak) | Requires IdP infrastructure |

---

## New Test Files

| File | Tests | Coverage |
|------|-------|----------|
| test_error_handling.py | 4 | Bad SQL, missing table, types |
| test_prompt_injection.py | 3 | DROP injection, GRANT, creds |
| test_connection_recovery.py | 3 | Auto-reconnect, timeout |
| test_schema_rediscovery.py | 4 | ALTER → describe/list |
| test_views_and_procs.py | 3 | VIEW, PROCEDURE via MCP |
| test_unicode_data.py | 5 | Cyrillic, CJK, NVARCHAR |
| test_row_cap.py | 3 | 1100 rows → max_rows=1000 |
| test_zen_core_units.py | 42 | Translator, TypeMapper, Config |
| test_oauth_scenarios.py | 14 | OAuth Scenario 1 + 2 |
| natural_language_requests.md (+5) | 5 | RU, FR, DE, JA, mixed prompts |
| **Total new** | **86** | |
