# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio
import pyodbc
from contextlib import asynccontextmanager, contextmanager
from collections.abc import AsyncIterator
from dbutils.pooled_db import PooledDB
from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from actian_mcp_server.plugin import MCPPlugin
from vector.features.tools import initialize_vector_tools
from vector.features.resources import initialize_vector_resources
from vector.features.prompts import initialize_vector_prompts

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
        required = ("driver", "database", "max_connections")
        missing = [k for k in required if not self.config.get(k)]
        if missing:
            raise ValueError(f"VectorPlugin requires config keys: {', '.join(missing)}")
        if not self.config.get("username") or not self.config.get("password"):
            raise ValueError("VectorPlugin requires 'username' and 'password'")

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
        try:
            with self.get_cursor() as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                if cur.description:
                    columns = [col[0] for col in cur.description]
                    rows = cur.fetchall()
                    return columns, rows
                return [], []
        except pyodbc.Error as e:
            return f"Error: {str(e)}"

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
