# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from actian_mcp_server.tools import initialize_tools
from actian_mcp_server.resources import initialize_resources
from actian_mcp_server.prompts import initialize_prompts

server_name = "Actian MCP Server"
logger = get_logger(server_name)

server = FastMCP(server_name)

def main():

    logger.info(f"Starting {server_name}")
    server.run(transport="stdio")

    logger.info(f"Initializing tools for {server_name}")
    initialize_tools(server)

    logger.info(f"Initializing resources for {server_name}")
    initialize_resources(server)

    logger.info(f"Initializing prompts for {server_name}")
    initialize_prompts(server)

if __name__ == "__main__":
    main()
