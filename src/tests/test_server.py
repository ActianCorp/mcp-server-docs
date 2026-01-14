# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio
from fastmcp import Client
from actian_mcp_server.server import server
from actian_mcp_server.server import (
    initialize_tools, 
    initialize_resources, 
    initialize_prompts
)
from tests.test_utils import (
    test_server_reachability,
    test_tools_list,
    test_resources_list,
    test_prompts_list,
    test_tool__print_text,
    test_resource__read_text,
    test_prompt__ask_question
)

async def main():
    client = Client(server)
    async with client:
        assert client.is_connected()

        # Test server
        await test_server_reachability(client)

        # Test tools
        initialize_tools(server)
        await test_tools_list(client)
        await test_tool__print_text(client)

        # Test resources
        initialize_resources(server)
        await test_resources_list(client)
        await test_resource__read_text(client)

        # Test prompts
        initialize_prompts(server)
        await test_prompts_list(client)
        await test_prompt__ask_question(client)

    assert not client.is_connected()

if __name__ == "__main__":
    asyncio.run(main())
