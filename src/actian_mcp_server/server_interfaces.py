# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from abc import ABC, abstractmethod
import pyodbc

class MCPTools(ABC):
    _connection: pyodbc.Connection

    def __init__(self, connection: pyodbc.Connection):
        self._connection = connection

    @abstractmethod
    async def execute_query(self, query: str) -> str:
        ...

class MCPResources(ABC):
    _connection: pyodbc.Connection

    def __init__(self, connection: pyodbc.Connection):
        self._connection = connection

    @abstractmethod
    async def get_database_schema(self) -> str:
        ...
