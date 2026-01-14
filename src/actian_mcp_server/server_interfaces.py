# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from abc import ABC, abstractmethod
import pyodbc

class MCPTools(ABC):
    def __init__(self, connection: pyodbc.Connection):
        self._connection = connection

    @abstractmethod
    def print_text(self, text: str) -> str:
        ...

    @abstractmethod
    async def execute_query_tool(self, query: str) -> str:
        ...
