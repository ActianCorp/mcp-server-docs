# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import pyodbc
import asyncio
from typing import List, Dict, Any
from actian_mcp_server.server_interfaces import MCPTools

def _execute_query(query: str, connection: pyodbc.Connection) -> Dict[str, Any]:
    try:
        with connection.cursor() as cur:
            cur.execute(query)
            results: List[Dict[str, Any]] = []
            if cur.description:
                columns = [column[0] for column in cur.description]
                rows = cur.fetchall()
                results = [dict(zip(columns, row)) for row in rows]
            return {
                "success": True, 
                "results": results, 
                "rowCount": len(results)
            }
    except pyodbc.Error as e:
        return {
            "success": False,
            "error": str(e)
        }

class VectorTools(MCPTools):
    def print_text(self, text: str) -> str:
        return f"{text}"

    async def execute_query_tool(self, query: str) -> str:
        """
        Execute an SQL query and fetch all the results.

        Obtains a database cursor, executes the SQL query
        and returns all results in a dictionary format.

        Parameters
            query: str
                SQL query to execute
            connection: pyodbc.Connection
                The database connection object

        Returns
            str
                Query results containing columns and rows, or query error containing pyodbc.Error message
        """
        try:
            result = await asyncio.to_thread(_execute_query, query, self._connection)
            if result.get("success"):
                return f"Query results: {result['results']}"
            return f"Query error: {result.get('error')}"
        except Exception as e:
            return f"Error: {str(e)}"

def initialize_vector_tools(server: FastMCP, actianmcp):
    tools = VectorTools(actianmcp.connection)

    server.tool(name="print_text")(tools.print_text)
    server.tool(name="execute_query_tool")(tools.execute_query_tool)
