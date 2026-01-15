# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import pyodbc

def initialize_vector_resources(server: FastMCP, connection: pyodbc.Connection):
    @server.resource("read://text")
    def read_text() -> str:
        return "hello world"
