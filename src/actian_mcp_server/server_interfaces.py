# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from abc import ABC, abstractmethod
from typing import Any

class MCPTools(ABC):
    actiandb: Any

    def __init__(self, actiandb):
        self.actiandb = actiandb

    @abstractmethod
    async def execute_query(self, query: str) -> str:
        ...

    @abstractmethod
    async def list_tables(self) -> str:
        ...

    @abstractmethod
    async def describe_table(self, table: str) -> str:
        ...

class MCPResources(ABC):
    actiandb: Any

    def __init__(self, actiandb):
        self.actiandb = actiandb

    @abstractmethod
    async def get_database_schema(self) -> str:
        ...
