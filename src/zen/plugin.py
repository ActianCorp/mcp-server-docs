# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from actian_mcp_server.plugin import MCPPlugin
from zen.core import ZenConnection, ZenConfiguration, parse_args
from zen.core.orm_manager import ZenORMManager
from zen.core.ddl_manager import ZenDDLManager
from zen.core.file_operations import ZenFileManager

SERVER_NAME = "Actian Zen MCP Server"
logger = get_logger(SERVER_NAME)

SERVER_INSTRUCTIONS = """Zen database server with 9 tools.

MANDATORY RULE — NEVER GUESS TABLE OR COLUMN NAMES:
Before writing ANY SQL query, verify table and column names against the
DATABASE SCHEMA section below. If a table or column is not listed there,
call describe_table(table) to get full details. NEVER fabricate names.

TOOL SELECTION GUIDE:
- Simple CRUD (one table) -> orm_operation
- Complex queries (JOINs, subqueries, aggregations, UNION) -> execute_query
- Schema changes (CREATE/DROP/ALTER) -> ddl_operation
- Bulk data (multi-row insert/update/delete, count) -> batch_operation
- Schema discovery -> list_tables + describe_table
- Transactions -> transaction
- File storage -> blob_operation
- Admin (DSN switch, capabilities) -> database_manage

TOOLS:
1. execute_query(sql, params, mode) - Raw SQL with auto-translation
2. ddl_operation(mode, table, ...) - DDL: CREATE/DROP/ALTER tables, columns, indexes, views, procedures, triggers
3. batch_operation(mode, table, ...) - Bulk: batch_insert, batch_update, batch_delete, count
4. list_tables() - List all user tables
5. describe_table(table) - Get table schema (columns, types, keys)
6. orm_operation(operation, table, ...) - Single-table SELECT/INSERT/UPDATE/DELETE with validation
7. transaction(action) - begin/commit/rollback
8. blob_operation(action, table_name, ...) - upload/download/list/delete files
9. database_manage(action) - list DSNs, switch database, capabilities

ZEN SQL SYNTAX (Important!):
* RENAME TABLE: ddl_operation(mode="ddl_rename_table", ...) or 'ALTER TABLE RENAME old TO new'
* CHECK constraints: NOT supported - use triggers
* SEQUENCES: NOT supported - use IDENTITY columns
* CTEs (WITH clause): NOT supported
* Table/Constraint names: 20 character limit
* LEN() -> use CHAR_LENGTH() (auto-translated)
* EXTRACT() -> use DATEPART()

CATALOG FUNCTIONS (always 3 params — NEVER call with 0 or 2 args):
* dbo.fSQLTables(NULL, NULL, NULL)           -- all tables; filter with WHERE TABLE_TYPE='TABLE'
* dbo.fSQLColumns(NULL, 'TableName', NULL)   -- columns for a table
* dbo.fSQLForeignKeys(NULL, NULL, 'Child')   -- FKs where Child is the FK table
* dbo.fSQLForeignKeys(NULL, 'Parent', NULL)  -- FKs where Parent is the PK table
* dbo.fSQLStatistics(NULL, 'TableName', 0)   -- indexes; 0=all, 1=unique only
* dbo.fSQLPrimaryKeys(NULL, 'Table')         -- PKs for a table (2 params only)

SCHEMA DISCOVERY:
Use list_tables and describe_table for schema exploration.
MCP resources available (client must request): schema, query-patterns

SQL ERROR RECOVERY:
When SQL fails, read error -> fix query -> retry. Check resource://database/query-patterns.
"""

SERVER_INSTRUCTIONS_READONLY = """Zen database server (read-only mode) with 6 tools.

MANDATORY RULE — NEVER GUESS TABLE OR COLUMN NAMES:
Before writing ANY SQL query, verify table and column names against the
DATABASE SCHEMA section below. If a table or column is not listed there,
call describe_table(table) to get full details. NEVER fabricate names.

READ-ONLY MODE — connected with OPENMODE=1. MANDATORY RULES:
- NEVER generate INSERT, UPDATE, DELETE, MERGE, or TRUNCATE
- NEVER generate CREATE, DROP, or ALTER (DDL)
- NEVER call ddl_operation, batch_operation, or transaction tools
- If the user requests a write operation, explain read-only mode is active
  and suggest reconnecting with a read-write DSN
- If a tool returns {"readonly": true}, do NOT retry

TOOL SELECTION GUIDE:
- SELECT queries -> execute_query (SELECT only)
- Single-table SELECT -> orm_operation (select only)
- Schema discovery -> list_tables + describe_table
- File download/list -> blob_operation (download + list only)
- Admin (DSN switch, capabilities) -> database_manage

TOOLS:
1. execute_query(sql, params, mode) - SELECT queries with auto-translation
2. list_tables() - List all user tables
3. describe_table(table) - Get table schema (columns, types, keys)
4. orm_operation(operation, table, ...) - Single-table SELECT with validation
5. blob_operation(action, table_name, ...) - download/list files
6. database_manage(action) - list DSNs, switch database, capabilities

ZEN SQL SYNTAX (Important!):
* CTEs (WITH clause): NOT supported
* Table/Constraint names: 20 character limit
* LEN() -> use CHAR_LENGTH() (auto-translated)
* EXTRACT() -> use DATEPART()

CATALOG FUNCTIONS (always 3 params — NEVER call with 0 or 2 args):
* dbo.fSQLTables(NULL, NULL, NULL)           -- all tables; filter with WHERE TABLE_TYPE='TABLE'
* dbo.fSQLColumns(NULL, 'TableName', NULL)   -- columns for a table
* dbo.fSQLForeignKeys(NULL, NULL, 'Child')   -- FKs where Child is the FK table
* dbo.fSQLForeignKeys(NULL, 'Parent', NULL)  -- FKs where Parent is the PK table
* dbo.fSQLStatistics(NULL, 'TableName', 0)   -- indexes; 0=all, 1=unique only
* dbo.fSQLPrimaryKeys(NULL, 'Table')         -- PKs for a table (2 params only)

SCHEMA DISCOVERY:
Use list_tables and describe_table for schema exploration.
MCP resources available (client must request): schema, query-patterns

SQL ERROR RECOVERY:
When SQL fails, read error -> fix query -> retry. Check resource://database/query-patterns.
"""


def _build_schema_summary(connection: ZenConnection) -> str:
    """Compact schema for server.instructions (~200-500 tokens). Called once at startup."""
    try:
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(connection.get_engine())
        tables = inspector.get_table_names()
        if not tables:
            return ""
        lines = ["\nDATABASE SCHEMA (verify names here before writing SQL):"]
        for tbl in tables:
            try:
                cols = inspector.get_columns(tbl)
                pk = {c for c in (inspector.get_pk_constraint(tbl) or {}).get("constrained_columns", [])}
                col_names = [f"{c['name']}*" if c['name'] in pk else c['name'] for c in cols]
                lines.append(f"- {tbl} ({', '.join(col_names)})")
            except Exception:
                lines.append(f"- {tbl}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning("Could not build schema summary: %s", e)
        return ""


class ZenPlugin(MCPPlugin):
    """Zen DBMS plugin."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.database = config.get("database", "")
        # Phase 1: readonly hardcoded regardless of config; revert in Phase 2
        self.readonly = True
        self.max_rows = int(config.get("max_rows", 1000))
        self._conn: ZenConnection | None = None
        self._orm: ZenORMManager | None = None
        self._ddl: ZenDDLManager | None = None
        self._file_mgr: ZenFileManager | None = None
        if not self.database:
            raise ValueError("ZenPlugin requires 'database' (DSN name)")

    def _init_connection(self):
        conn_str = f"DSN={self.database}"
        if self.readonly:
            # OPENMODE=1 enforces read-only at Zen engine level — rejects DDL/DML
            conn_str += ";OPENMODE=1"
        self._conn = ZenConnection(conn_str)
        self._orm = ZenORMManager(self._conn)
        self._ddl = ZenDDLManager(self._conn)
        self._file_mgr = ZenFileManager(self._conn)

    def register_tools(self, server: FastMCP):
        from zen.features.tools import register_zen_tools
        register_zen_tools(server, self._conn, self._orm, self._ddl, self._file_mgr,
                           readonly=self.readonly, max_rows=self.max_rows)

    def register_resources(self, server: FastMCP):
        from zen.features.resources import initialize_zen_resources
        initialize_zen_resources(server, self._conn, readonly=self.readonly)

    def register_prompts(self, server: FastMCP):
        from zen.features.prompts import initialize_zen_prompts
        initialize_zen_prompts(server)

    @asynccontextmanager
    async def lifespan(self, server: FastMCP) -> AsyncIterator[None]:
        import asyncio
        from zen.features.instructions import query_instructions, readonly_instructions
        await asyncio.to_thread(self._init_connection)

        base = query_instructions
        if self.readonly:
            base += readonly_instructions
        schema = await asyncio.to_thread(_build_schema_summary, self._conn)
        server.instructions = base + (schema or "")
        if schema:
            logger.info("Schema summary injected into server instructions")
        logger.info("Zen plugin started (DSN=%s, readonly=%s)", self.database, self.readonly)
        try:
            yield
        finally:
            if self._conn:
                try:
                    self._conn.close_odbc_connection()
                except Exception:
                    pass
            logger.info("Zen plugin stopped")


def create_lifespan(config: ZenConfiguration, readonly: bool = False):
    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[ZenConnection]:
        connection = None
        try:
            args = parse_args()
            conn_config = config.load_from_cli(args)
            logger.info(f"Connecting to {conn_config.dsn_name or 'custom string'} (source: {conn_config.source})")

            cs = conn_config.conn_string
            if readonly:
                cs += ";OPENMODE=1"
            connection = ZenConnection(cs)

            orm = ZenORMManager(connection)
            ddl = ZenDDLManager(connection)
            file_mgr = ZenFileManager(connection)

            from zen.features.tools import register_zen_tools
            from zen.features.resources import initialize_zen_resources
            from zen.features.prompts import initialize_zen_prompts

            register_zen_tools(server, connection, orm, ddl, file_mgr, readonly=readonly)
            initialize_zen_resources(server, connection, readonly=readonly)
            initialize_zen_prompts(server)

            base_instructions = SERVER_INSTRUCTIONS_READONLY if readonly else SERVER_INSTRUCTIONS
            schema_summary = await asyncio.to_thread(_build_schema_summary, connection)
            if schema_summary:
                server.instructions = base_instructions + schema_summary
            else:
                server.instructions = base_instructions

            mode_label = "readonly" if readonly else "full"
            logger.info(f"Server initialized (mode: {mode_label})")
            yield connection

        except Exception as e:
            logger.critical(f"Server initialization failed: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize server: {e}") from e
        finally:
            if connection:
                if connection.is_transaction_active():
                    logger.warning("Rolling back active transaction on shutdown")
                    connection.rollback_transaction()
                await connection.cleanup()

    return lifespan
