# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

query_instructions = """
SQL queries and operations against Actian Zen (PSQL) database.

**Tool Selection**:
- Use execute_query for: JOINs, subqueries, aggregations, UNION, raw DML, complex WHERE clauses
- Use orm_operation for: simple single-table SELECT/INSERT/UPDATE/DELETE
- Use ddl_operation for: CREATE/DROP/ALTER tables, columns, indexes, procedures, triggers, views
- Use batch_operation for: bulk INSERT/UPDATE/DELETE, row counts
- Use transaction for: explicit BEGIN/COMMIT/ROLLBACK control

**Zen SQL Dialect**:
- Use CHAR_LENGTH() not LEN() for string length
- No CTEs (WITH clause) — rewrite as subqueries or temp tables
- No window functions in raw SQL — use orm_operation with group_by/having instead
- Temporary tables use # prefix: CREATE TABLE #tmp (...)
- IDENTITY columns: IDENTITY, SMALLIDENTITY, BIGIDENTITY (not SERIAL/AUTO_INCREMENT)
- String literals: single quotes only
- Date literals: {d 'YYYY-MM-DD'} or standard DATE 'YYYY-MM-DD'

**Identifier Rules**:
- Table and constraint names max 20 characters
- Temporary table prefix (#) counts toward the 20-char limit
- Quote identifiers with double quotes if they contain spaces or reserved words

**NULL Handling**:
- Use COALESCE(expr, default) for NULL substitution
- IS NULL / IS NOT NULL for null checks

**Auto-translations** (handled automatically by execute_query):
- LEN() → CHAR_LENGTH()
- INFORMATION_SCHEMA queries → dbo.fSQL*() catalog functions
- ALTER TABLE x RENAME TO y → Zen syntax
- Constraint names longer than 20 chars are truncated automatically

**Catalog Functions** (use exact param counts below):
- dbo.fSQLTables(NULL, NULL, NULL)           -- all tables; filter with WHERE TABLE_TYPE='TABLE'
- dbo.fSQLColumns(NULL, 'TableName', NULL)   -- columns for a table
- dbo.fSQLForeignKeys(NULL, NULL, 'Child')   -- FKs where Child is the FK table
- dbo.fSQLForeignKeys(NULL, 'Parent', NULL)  -- FKs where Parent is the PK table
- dbo.fSQLStatistics(NULL, 'TableName', 0)   -- indexes; 0=all, 1=unique only
- dbo.fSQLPrimaryKeys(NULL, 'Table')         -- PKs for a table (2 params only)
"""

readonly_instructions = """
READ-ONLY MODE — this server is connected with OPENMODE=1. MANDATORY RULES:
- NEVER generate INSERT, UPDATE, DELETE, MERGE, or TRUNCATE
- NEVER generate CREATE, DROP, or ALTER (DDL)
- NEVER call ddl_operation, batch_operation, or transaction tools
- Allowed tools: execute_query (SELECT only), orm_operation (select),
  list_tables, describe_table, blob_operation (download/list), database_manage
- If the user requests a write operation, explain that read-only mode is active
  and suggest reconnecting with a read-write DSN
- If a tool returns {"readonly": true}, do NOT retry — tell the user the operation
  is not permitted in this mode
"""
