# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio
import pyodbc
import json
from contextlib import asynccontextmanager, contextmanager
from collections.abc import AsyncIterator
from dbutils.pooled_db import PooledDB
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from actian_mcp_server.plugin import MCPPlugin
from actian_mcp_server.oauth import get_current_username
from vector.features.tools import initialize_vector_tools
from vector.features.resources import initialize_vector_resources
from vector.features.prompts import initialize_vector_prompts
from typing import Dict, Any

logger = get_logger("VectorPlugin")


class VectorPlugin(MCPPlugin):
    """
    Actian Vector DBMS plugin.

    Manages a pyodbc connection pool and registers the standard
    SQL tools (execute_query, list_tables, describe_table),
    resources (database schema), and prompts.

    Required config keys:
        driver, database, max_connections, username, password
    Optional config keys:
        server (ODBC server string)
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.pool = None
        self._validate_config()

    def _validate_config(self):
        required = {"driver": str, "database": str, "max_connections": int, "max_rows": int, "username": str, "password": str}
        missing = []
        wrong_type = {}

        if not self.config.get("max_rows"):
            self.config["max_rows"] = 1000

        for name, dtype in required.items():
            if not self.config.get(name):
                missing.append(name)
            elif not isinstance(self.config[name], dtype):
                wrong_type.update({name: dtype})

        if missing:
            raise ValueError(f"Vector MCP Server requires config keys: {', '.join(missing)}")

        if wrong_type:
            raise ValueError(f"Vector MCP Server requires the following config value types: {wrong_type}")
        
        if self.config["max_rows"] <= 0 or self.config["max_connections"] <= 0:
            raise ValueError("Vector MCP Server config options 'max_rows' and 'max_connections' cannot be zero or negative")

    def _create_pool(self):
        logger.info("Initializing Vector database connection pool")
        try:
            pool = PooledDB(
                creator=pyodbc,
                mincached=2,
                maxcached=5,
                maxconnections=int(self.config["max_connections"]),
                blocking=True,
                driver=self.config["driver"],
                server=self.config.get("server", ""),
                uid=self.config["username"],
                pwd=self.config["password"],
                database=self.config["database"],
                readonly=True
            )
            logger.info("Vector database connection established successfully")
            return pool
        except Exception as e:
            logger.critical(f"Failed to create connection pool: {type(e).__name__}: {e}", exc_info=True)
            raise RuntimeError("Failed to establish Vector database connection pool") from e

    @contextmanager
    def get_cursor(self):
        connection = None
        cursor = None
        try:
            connection = self.pool.connection()
            cursor = connection.cursor()
        except Exception as e:
            logger.critical(f"Failed to acquire database connection or cursor: {type(e).__name__}: {e}", exc_info=True)
            raise RuntimeError("Failed to get database connection or cursor") from e
        try:
            yield cursor
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()

    def execute_query(self, query: str, params=None):
        impersonate = self.config.get("oauth", {}).get("user_impersonation", True)
        db_user = get_current_username() if impersonate else None

        try:
            with self.get_cursor() as cur:
                if db_user:
                    logger.info(f"Impersonating user: {db_user}")
                    cur.connection.commit()
                    cur.execute(f'SET SESSION AUTHORIZATION "{db_user}"')

                query_succeeded = False
                try:
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)

                    if cur.description:
                        columns = [col[0] for col in cur.description]
                        rows = [list(row) for row in cur.fetchmany(self.config["max_rows"] + 1)]
                        trunc = len(rows) > self.config["max_rows"]
                        if trunc:
                            del rows[-1]
                        result: dict[str, Any] = {
                            "success": True,
                            "columns": columns,
                            "rows": rows,
                            "row_count": len(rows),
                        }
                        if trunc:
                            result["truncated"] = True
                            result["warning"] = f"Results were truncated to {self.config['max_rows']} rows."
                        query_succeeded = True
                        return json.dumps(result, default=str)
                    query_succeeded = True
                    return json.dumps({"success": True, "columns": [], "rows": [], "row_count": 0})
                finally:
                    if db_user:
                        try:
                            if query_succeeded:
                                cur.connection.commit()
                            else:
                                cur.connection.rollback()
                            cur.execute("SET SESSION AUTHORIZATION INITIAL_USER")
                        except Exception:
                            logger.warning("Failed to reset session authorization after error")
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)}, default=str)

    def get_db_schema(self):
        query = """
            SELECT trim(C.table_name),
                   trim(C.column_name),
                   trim(C.column_datatype),
                   trim(SCO.long_remark),
                   trim(K.text_segment),
                   trim(CO.long_remark)
            FROM iicolumns C
            LEFT JOIN iidb_subcomments SCO
                ON  SCO.object_name=C.table_name
                AND SCO.subobject_name=C.column_name
            LEFT JOIN iiconstraints K
                ON  K.table_name=C.table_name
            LEFT JOIN iidb_comments CO
                ON  CO.object_name=C.table_name
            WHERE C.table_name NOT BEGINNING 'ii'
        """
        try:
            with self.get_cursor() as cur:
                cur.execute(query)

                rows = cur.fetchall()
                schema: Dict[str, Any] = {}
                for table, column, dtype, col_comm, keys, tbl_comm in rows:
                    table_entry = schema.setdefault(table, {"columns": {}, "keys": [], "comment": tbl_comm})

                    if column not in table_entry["columns"]:
                        table_entry["columns"][column] = {"dtype": dtype, "comment": col_comm}

                    if keys is not None and keys not in table_entry["keys"]:
                        table_entry["keys"].append(keys)
                return json.dumps(schema, default=str)
        except Exception as e:
            return f"The database schema could not be retrieved. Error: {str(e)}"

    def register_tools(self, server: FastMCP):
        initialize_vector_tools(server, self)

    def register_resources(self, server: FastMCP):
        initialize_vector_resources(server, self)

    def register_prompts(self, server: FastMCP):
        initialize_vector_prompts(server)

    @asynccontextmanager
    async def lifespan(self, server: FastMCP) -> AsyncIterator[None]:
        self.pool = await asyncio.to_thread(self._create_pool)
        try:
            yield
        finally:
            if self.pool:
                logger.info("Closing Vector database connection pool")
                try:
                    await asyncio.to_thread(self.pool.close)
                except Exception:
                    logger.warning("Error closing Vector connection pool", exc_info=True)
