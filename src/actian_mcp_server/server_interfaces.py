# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from abc import ABC, abstractmethod
from actian_mcp_server.server import ActianDB

class MCPTools(ABC):
    actiandb: ActianDB

    def __init__(self, actiandb):
        self.actiandb = actiandb

    @abstractmethod
    async def execute_query(self, query: str) -> str:
        ...

class MCPResources(ABC):
    actiandb: ActianDB

    def __init__(self, actiandb):
        self.actiandb = actiandb

    @abstractmethod
    async def get_database_schema(self) -> str:
        ...
