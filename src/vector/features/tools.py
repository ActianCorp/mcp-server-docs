# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
from actian_mcp_server.server_interfaces import MCPTools
from actian_mcp_server.server_utils import validate_readonly_query
from .instructions import query_instructions
from typing import Annotated
from pydantic import Field
import json

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
            is_valid, error = validate_readonly_query(query)
            if is_valid:
                result = await asyncio.to_thread(self.actiandb.execute_query, query)
            else:
                raise Exception(error)
            return result
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
