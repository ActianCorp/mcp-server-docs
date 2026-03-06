# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import logging
import pyodbc
from fastmcp import FastMCP
import asyncio
from actian_mcp_server.server_interfaces import MCPTools
from actian_mcp_server.oauth import get_current_username
from .instructions import query_instructions
from typing import Annotated, Any, List, Dict
from pydantic import Field
import json

logger = logging.getLogger(__name__)


def _execute_as_user(query: str, actiandb: Any) -> str:
    """Execute a query with SET SESSION AUTHORIZATION for the authenticated user.

    If an OAuth token was verified upstream, impersonates that database user
    for the duration of the query, then resets to the initial user.
    Falls back to the pool's default credentials when no user is in context.
    """
    cur = None
    db_user = None
    try:
        db_user = get_current_username()
        with actiandb.get_cursor() as cur:
            if db_user:
                logger.info(f"Impersonating user: {db_user}")
                cur.connection.commit()  # Ensure no active transaction before SET SESSION AUTHORIZATION
                cur.execute(f'SET SESSION AUTHORIZATION "{db_user}"')

            cur.execute(query)
            results: List[Dict[str, Any]] = []
            if cur.description:
                columns = [column[0] for column in cur.description]
                rows = cur.fetchall()
                results = [dict(zip(columns, map(str, row))) for row in rows]

            cur.connection.commit()  # Commit transaction before resetting session authorization

            if db_user:
                cur.execute("SET SESSION AUTHORIZATION INITIAL_USER")

            return str(toons.dumps(results))
    except pyodbc.Error as e:
        if cur and db_user:
            try:
                cur.connection.rollback()
                cur.execute("SET SESSION AUTHORIZATION INITIAL_USER")
            except Exception:
                logger.warning("Failed to reset session authorization after error")
        return f"Error: {str(e)}"


class VectorTools(MCPTools):
    async def execute_query(self, query: Annotated[str, Field(description=query_instructions)]) -> str:
        """
        Execute an SQL query (read query parameter description) and fetch all the results.

        Obtains a database cursor, executes the SQL query
        and returns all results.

        Parameters
            query: str
                SQL query to execute

        Returns
            str
                On query success: JSON object with keys:
                    success (bool), columns (list[str]), rows (list[list]),
                    row_count (int), and optionally truncated (bool) and
                    warning (str) when results exceed the configured row limit.

                On query error: JSON object with keys:
                    success (false), error (str)
        """
        try:
            return await asyncio.to_thread(_execute_as_user, query, self.actiandb)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, default=str)

    async def list_tables(self) -> str:
        """
        List all tables and views available in the database.

        Obtains a database cursor, executes the SQL query to retrieve the table names
        and returns the list of tables.

        Returns
            str
                On query success: JSON object with keys:
                    success (bool), columns (["table_name"]), rows (list[list[str]]),
                    row_count (int).

                On query error: JSON object with keys:
                    success (false), error (str)
        """

        query = """
            SELECT trim(table_name) AS table_name
            FROM iitables
            WHERE system_use='U'
            UNION
            SELECT trim(table_name) AS table_name
            FROM iiviews
            WHERE table_name NOT BEGINNING 'ii'
        """
        try:
            result = await asyncio.to_thread(self.actiandb.execute_query, query)
            return result
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, default=str)

    async def describe_table(self, table_name: Annotated[str, Field(description="Name of the table to describe")]) -> str:
        """
        Retrieves the table schema from the database with information such as the column name, column datatype,
        column length, column scale and column comment.

        Obtains a database cursor, executes the SQL query to retrieve the table schema
        and returns all results.

        Parameters
            table_name: str
                Name of the table to describe

        Returns
            str
                On query success: JSON object with keys:
                    success (bool), columns (["column_name", "column_datatype",
                    "column_length", "column_scale", "column_comment"]),
                    rows (list[list]), row_count (int).

                On query error: JSON object with keys:
                    success (false), error (str)
        """

        query = """
            SELECT trim(column_name) AS column_name,
                   trim(column_datatype) AS column_datatype,
                   trim(column_length) AS column_length,
                   trim(column_scale) AS column_scale,
                   trim(long_remark) AS column_comment
            FROM iicolumns C
            LEFT JOIN iidb_subcomments SCO
                ON  SCO.object_name=C.table_name
                AND SCO.subobject_name=C.column_name
            WHERE C.table_name=?
        """

        try:
            if table_name.lower().startswith("ii"):
                raise ValueError(f"No permission to access table '{table_name}'")
            result = await asyncio.to_thread(self.actiandb.execute_query, query, params=(table_name,))
            return result
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, default=str)

    async def list_functions(self) -> str:
        """
        List all User Defined Functions (UDFs) and procedures available in the database.

        Obtains a database cursor, executes the SQL query to retrieve the function names,
        the create SQL statements (DDL) and returns all results.
        The input and output information for using the functions should be inferred from the
        DDL statements.

        Returns
            str
                On query success: JSON object with keys:
                    success (bool), columns (["function_name", "function_ddl"]),
                    rows (list[list[str]]), row_count (int).

                On query error: JSON object with keys:
                    success (false), error (str)
        """

        query = """
            SELECT trim(proc_ext_name) AS function_name, trim(text_segment) as function_ddl
            FROM iiprocedures
            WHERE procedure_name NOT BEGINNING 'ii' AND is_model='N'
        """
        try:
            result = await asyncio.to_thread(self.actiandb.execute_query, query)
            return result
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, default=str)

def initialize_vector_tools(server: FastMCP, actiandb):
    tools = VectorTools(actiandb)

    server.tool(name="execute_query")(tools.execute_query)
    server.tool(name="list_tables")(tools.list_tables)
    server.tool(name="describe_table")(tools.describe_table)
    server.tool(name="list_functions")(tools.list_functions)
