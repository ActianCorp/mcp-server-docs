# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP

def initialize_tools(server: FastMCP):
    @server.tool
    def print_text(text: str) -> str:
        return f"{text}"
