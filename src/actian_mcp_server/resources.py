# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP

def initialize_resources(server: FastMCP):
    @server.resource("read://text")
    def read_text() -> str:
        return "hello world"
