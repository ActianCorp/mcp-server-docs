# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from fastmcp import FastMCP


class MCPPlugin(ABC):
    """
    Base class for Actian DBMS plugins.

    Each database implements this to provide its own connection management,
    tools, resources, and prompts. The framework handles lifecycle
    (startup/shutdown), transport, and CLI parsing.

    To add a new database:
    1. Create a package under src/<dbms>/
    2. Subclass MCPPlugin and implement all abstract methods
    3. Register the plugin in PLUGINS in server.py
    """

    def __init__(self, config: dict):
        """
        Args:
            config: Merged dict of CLI args + conf.json values.
                    Each plugin reads what it needs, ignores the rest.
        """
        self.config = config

    @abstractmethod
    async def lifespan(self, server: FastMCP) -> AsyncIterator[None]:
        """
        Manage the database connection lifecycle.

        Subclasses MUST decorate their override with @asynccontextmanager
        and use a try/finally to guarantee teardown:

            from contextlib import asynccontextmanager

            @asynccontextmanager
            async def lifespan(self, server):
                self.pool = await create_pool(self.config)
                try:
                    yield
                finally:
                    await self.pool.close()

        Tools, resources, and prompts are already registered by the
        framework before this method is entered, so they are safe to
        use during teardown if needed.
        """
        ...

    @abstractmethod
    def register_tools(self, server: FastMCP):
        """Register MCP tools on the server."""
        ...

    @abstractmethod
    def register_resources(self, server: FastMCP):
        """Register MCP resources on the server."""
        ...

    @abstractmethod
    def register_prompts(self, server: FastMCP):
        """Register MCP prompts on the server."""
        ...
