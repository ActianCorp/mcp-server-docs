# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
from actian_mcp_server.server_interfaces import MCPResources
from typing import Dict, Any

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

                table_1:
                  columns:
                    col_1:
                      dtype: datatype
                      comment: column comment (or null)
                    col_2:
                      dtype: datatype
                      comment: column comment (or null)
                    ...
                  keys: list of table keys (or null)
                  comment: table comment (or null)
                table_2:
                  ...

                On query error: error message containing the pyodbc.Error
        """

        try:
            results = await asyncio.to_thread(self.actiandb.get_db_schema)
            return results
        except Exception as e:
            return f"The database schema could not be retrieved. Error: {str(e)}"
    
def initialize_vector_resources(server: FastMCP, actiandb):
    resources = VectorResources(actiandb)

    server.resource(uri="resource://database/schema")(resources.get_database_schema)
