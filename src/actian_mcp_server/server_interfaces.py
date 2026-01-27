# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from abc import ABC, abstractmethod
from typing import Any
import pyodbc

class MCPTools(ABC):
    actiandb: Any

    def __init__(self, actiandb):
        self.actiandb = actiandb

    @abstractmethod
    async def execute_query(self, query: str) -> str:
        ...

class MCPResources(ABC):
    actiandb: Any

    def __init__(self, actiandb):
        self.actiandb = actiandb

    @abstractmethod
    async def get_database_schema(self) -> str:
        ...
