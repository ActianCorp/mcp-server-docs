# Test Coverage Evaluation

Legend: ✅ covered  ⚠ partial  ❌ not covered

---

## Connection

| Item | Status | Notes |
|------|--------|-------|
| ODBC connection | ✅ | All tests run over pyodbc/SQLAlchemy |
| Concurrent connections | ✅ | test_multitenancy.py — 10/50/100 parallel clients |
| Auth with correct credentials | ⚠ | OAuth token logging tested; ODBC credential tests absent |
| Auth with incorrect credentials (negative) | ⚠ | test_oauth.py covers JWT context vars, not bad-password rejection |
| Container deployment (MCP + auth container) | ❌ | No container-based test environment |
| Client ↔ DBMS: Vector, Ingres | ❌ | Zen only |
| OAuth — Auth0 / Keycloak | ⚠ | Middleware unit-tested; no end-to-end with real IdP |

---

## Tools — execute_query

| Item | Status | Notes |
|------|--------|-------|
| Read tables, views | ✅ | Covered in integration and LLM tests |
| Read procedures, functions, models | ❌ | Not tested |
| Update via terminal monitor + re-check (with/without committed txn) | ❌ | No external-change scenarios |
| Different data types (single/multibyte, charsets) | ❌ | Test data uses simple ASCII strings only |
| Masked data with/without unmasking privilege | ❌ | |
| Encrypted columns | ❌ | |
| Error handling — bad SQL syntax | ⚠ | Some cases in test_execute_query_modes.py |
| Error handling — missing table | ⚠ | Implicit in some tests, not explicit |
| Error handling — connection drop | ❌ | |
| Interpret DBMS errors (not return literal error codes) | ❌ | Raw error strings returned as-is |
| Row count cap (max_rows=1000) | ✅ | Implemented and guarded |

---

## Tools — list_tables

| Item | Status | Notes |
|------|--------|-------|
| User tables only (system tables excluded) | ✅ | Catalog function filters to TABLE_TYPE='TABLE' |
| Views, procedures, functions, models | ❌ | list_tables returns user tables only; no separate listing for other objects |
| Tables in encrypted/locked database | ❌ | |
| Multiple databases, same table names | ❌ | Single DSN per server instance |

---

## Tools — describe_table

| Item | Status | Notes |
|------|--------|-------|
| Column metadata (types, nullability, PK, FK) | ✅ | Covered including FK discovery |
| Column metadata with/without privileges | ❌ | |
| System tables (ii*) explicitly rejected | ❌ | Not tested |
| After ALTER TABLE/COLUMN — with/without committed txn | ❌ | |
| Views, procedures, functions, models | ❌ | describe_table is table-only |

---

## Tools — get_db_schema / list_tables / schema injection

| Item | Status | Notes |
|------|--------|-------|
| Schema in server instructions (live injection at startup) | ✅ | _build_schema_summary() runs at startup |
| Datatypes and lengths in schema | ⚠ | Column names included; type/length detail limited |
| Schema after column rename or type change | ❌ | Static snapshot at startup only |
| Objects owned by different users | ❌ | |
| PK/FK/Unique constraints in schema | ⚠ | PK markers present; FK in describe_table only |

---

## Guardrails

| Item | Status | Notes |
|------|--------|-------|
| Readonly mode — write tools not registered | ✅ | test_readonly.py |
| Readonly mode — SQL guards (INSERT/UPDATE/DELETE/DDL blocked) | ✅ | Python guard + OPENMODE=1 engine backstop |
| LLM instruction compliance (readonly rules) | ✅ | LLM harness breaking tests |
| Prompt injection / tool misuse | ⚠ | Breaking tests cover some cases; no systematic injection test suite |
| Row count cap to prevent OOM/token overflow | ✅ | max_rows=1000 enforced |
| Rate limiting / cost explosion | ❌ | |
| MCP user vs DBMS user separation | ❌ | |
| Grants on database objects | ❌ | |

---

## Stress

| Item | Status | Notes |
|------|--------|-------|
| Concurrent queries | ✅ | test_multitenancy.py |
| Large dataset without pagination | ✅ | Row cap tested |
| Large dataset with pagination | ❌ | Pagination not implemented (see large_dataset_options.md) |

---

## LLM / Prompts

| Item | Status | Notes |
|------|--------|-------|
| Multiple LLM backends (OpenRouter, Ollama) | ✅ | Both supported in harness |
| Readonly prompt compliance | ✅ | |
| Write operations blocked (negative) | ✅ | |
| Adversarial / breaking prompts | ✅ | run_breaking_tests_llm.py |
| Prompts in multiple languages | ❌ | |
| Pre-defined prompt library | ❌ | Ad-hoc prompts only |
| End-to-end automation | ⚠ | LLM harness automates execution; result evaluation still manual |

---

## Not in scope (noted for completeness)

- Pen testing — Security Team
- Actian Vector / Ingres client testing — separate product scope
- Container deployment CI — infrastructure work, not test code

---

## Summary

| Layer | Coverage |
|-------|----------|
| Core tool functionality | ✅ Good |
| Concurrent / stress | ✅ Good |
| Readonly / guardrails | ✅ Good |
| OAuth middleware | ⚠ Unit level only |
| Advanced data types, privileges, encryption | ❌ Not started |
| Multi-database, multi-user scenarios | ❌ Not started |
| Error interpretation (vs raw DBMS errors) | ❌ Not started |
| Other DB objects (views, procedures, functions, models) | ❌ Not started |
| Pagination | ❌ Not implemented |
| Container / CI environment | ❌ Not started |
