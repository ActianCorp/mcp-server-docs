# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
from actian_mcp_server.server_interfaces import MCPResources
from typing import Dict, Any

class VectorResources(MCPResources):
    async def get_database_schema(self) -> str:
        """
        Retrieves the database schema with information such as the table name, keys, comments
        and for each table the column name, column datatype, and column comment.

        Obtains a database cursor, executes the SQL query to retrieve the database schema
        and returns all results in a dictionary format.

        Returns
            str
                On query success: JSON object where each key is a table name, with value:
                    columns (dict): maps column_name -> {dtype (str), comment (str | null)}
                    keys (list[str] | null): constraint definitions for the table
                    comment (str | null): table-level comment

                On query error: str:
                    The database schema could not be retrieved. Error: (error)
        """

        try:
            results = await asyncio.to_thread(self.actiandb.get_db_schema)
            return results
        except Exception as e:
            return f"The database schema could not be retrieved. Error: {str(e)}"
    
def initialize_vector_resources(server: FastMCP, actiandb):
    resources = VectorResources(actiandb)

    server.resource(uri="resource://database/schema")(resources.get_database_schema)
