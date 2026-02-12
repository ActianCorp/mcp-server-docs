# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import pyodbc
import asyncio
from actian_mcp_server.server_interfaces import MCPResources
from typing import Dict, Any
import toons

class VectorResources(MCPResources):
    async def get_database_schema(self) -> str:
        """
        Retrieves the database schema with information such as the table name and for each table
        the column names and column datatypes respectively.

        Obtains a database cursor, executes the SQL query to retrieve the database schema
        and returns all results in a dictionary format.

        Returns
            str
                On query success: database schema in the toon (token-oriented object notation) format:

                table_1[column_count]:
                 - column_1: datatype_1
                 - column_2: datatype_2
                 - ...
                table_2[column_count]:
                 - column_1: datatype_1
                 - column_2: datatype_1
                 - ...
                ...

                On query error: error message containing the pyodbc.Error
        """

        query = """
            SELECT trim(T.table_name), trim(column_name), trim(column_datatype)
            FROM iitables T, iicolumns C
            WHERE T.table_name=C.table_name AND system_use='U'
        """
        try:
            _, rows = await asyncio.to_thread(self.actiandb.execute_query, query)
            schema: Dict[str, Any] = {}
            for table, column, dtype in rows:
                schema.setdefault(table, []).append({
                    column: dtype
                })
            return str(toons.dumps(schema))
        except Exception as e:
            return f"Error: {str(e)}"
    
def initialize_vector_resources(server: FastMCP, actiandb):
    resources = VectorResources(actiandb)

    server.resource(uri="resource://database/schema")(resources.get_database_schema)
