# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import pyodbc
import asyncio
from actian_mcp_server.server_interfaces import MCPTools
from typing import List, Dict, Any
import toons

def _execute_query(query: str, actiandb: Any) -> str:
    try:
        with actiandb.get_cursor() as cur:
            cur.execute(query)
            results: List[Dict[str, Any]] = []
            if cur.description:
                columns = [column[0] for column in cur.description]
                rows = cur.fetchall()
                results = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(results))
    except pyodbc.Error as e:
        return f"Error: {str(e)}"

class VectorTools(MCPTools):
    async def execute_query(self, query: str) -> str:
        """
        Execute an SQL query and fetch all the results.

        Obtains a database cursor, executes the SQL query
        and returns all results as a string.

        Parameters
            query: str
                SQL query to execute

        Returns
            str
                Query results containing columns and rows, or query error containing the pyodbc.Error message
        """
        try:
            ret = await asyncio.to_thread(_execute_query, query, self.actiandb)
            return ret
        except Exception as e:
            return f"Error: {str(e)}"

def initialize_vector_tools(server: FastMCP, actiandb):
    tools = VectorTools(actiandb)

    server.tool(name="execute_query")(tools.execute_query)
