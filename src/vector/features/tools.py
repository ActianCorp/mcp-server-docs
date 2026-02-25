# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
from actian_mcp_server.server_interfaces import MCPTools
from .instructions import query_instructions
from typing import Annotated
from pydantic import Field
import toons

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
                On query success: results containing columns and rows in the toon (token-oriented object notation) format:

                    [row_count]{column_1,column_2,...}:
                        row_1_value_1,row_1_value_2,...
                        row_2_value_1,row_2_value_2,...
                        ...

                On query error: error message containing the pyodbc.Error
        """
        try:
            columns, rows = await asyncio.to_thread(self.actiandb.execute_query, query)
            ret = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(ret))
        except Exception as e:
            return f"Error: {str(e)}"

    async def list_tables(self) -> str:
        """
        List all tables available in the database.

        Obtains a database cursor, executes the SQL query to retrieve the table names
        and returns the list of tables.

        Returns
            str
                On query success: results containing columns and rows in toon (token-oriented object notation):

                    [row_count]{table_name}:
                        table_name_1
                        table_name_2
                        ...

                On query error: error message containing the pyodbc.Error
        """

        query = """
            SELECT trim(table_name) AS table_name
            FROM iitables
            WHERE system_use='U'
        """
        try:
            columns, rows = await asyncio.to_thread(self.actiandb.execute_query, query)
            ret = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(ret))
        except Exception as e:
            return f"Error: {str(e)}"

    async def describe_table(self, table_name: Annotated[str, Field(description="Name of the table to describe")]) -> str:
        """
        Retrieves the table schema from the database with information such as the column name, column datatype,
        column length and column scale.

        Obtains a database cursor, executes the SQL query to retrieve the table schema
        and returns all results.

        Parameters
            table_name: str
                Name of the table to describe

        Returns
            str
                On query success: results containing columns and rows in toon (token-oriented object notation):

                    [row_count]{column_name, column_datatype, column_length, column_scale}:
                        column_name_1,column_datatype_1,column_length_1,column_scale_1
                        column_name_2,column_datatype_2,column_length_2,column_scale_2
                        ...

                On query error: error message containing the pyodbc.Error
        """

        query = """
            SELECT trim(column_name) AS column_name,
                   trim(column_datatype) AS column_datatype,
                   trim(column_length) AS column_length,
                   trim(column_scale) AS column_scale
            FROM iitables T, iicolumns C
            WHERE T.table_name=C.table_name AND T.table_name=? AND system_use='U'
        """
        try:
            columns, rows = await asyncio.to_thread(self.actiandb.execute_query, query, params=(table_name,))
            ret = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(ret))
        except Exception as e:
            return f"Error: {str(e)}"

    async def list_functions(self) -> str:
        """
        List all User Defined Functions (UDFs) and procedures available in the database.

        Obtains a database cursor, executes the SQL query to retrieve the function names, the create SQL statements (DDL)
        and returns all results. The input and output information for using the functions should be inferred from the
        DDL statements.

        Returns
            str
                On query success: results containing columns and rows in toon (token-oriented object notation):

                    [row_count]{functions_name, function_ddl}:
                        functions_name_1,function_ddl_1
                        functions_name_2,function_ddl_2
                        ...

                On query error: error message containing the pyodbc.Error
        """

        query = """
            SELECT trim(proc_ext_name) AS function_name, trim(text_segment) as function_ddl
            FROM iiprocedures
            WHERE procedure_name NOT BEGINNING 'ii' AND is_model='N'
        """
        try:
            columns, rows = await asyncio.to_thread(self.actiandb.execute_query, query)
            ret = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(ret))
        except Exception as e:
            return f"Error: {str(e)}"

def initialize_vector_tools(server: FastMCP, actiandb):
    tools = VectorTools(actiandb)

    server.tool(name="execute_query")(tools.execute_query)
    server.tool(name="list_tables")(tools.list_tables)
    server.tool(name="describe_table")(tools.describe_table)
    server.tool(name="list_functions")(tools.list_functions)
