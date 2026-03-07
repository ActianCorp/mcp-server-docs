# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from actian_mcp_server.plugin import MCPPlugin
from zen.core.connection import ZenConnection
from zen.core.orm_manager import ZenORMManager
from zen.core.ddl_manager import ZenDDLManager
from zen.core.file_operations import ZenFileManager

logger = get_logger("ZenPlugin")


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
