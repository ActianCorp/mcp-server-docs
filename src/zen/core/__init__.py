"""
Core infrastructure for Actian Zen MCP Server.

Modules:
- connection: ZenConnection class with thread-local ODBC and QueuePool
- config: ZenConfiguration with hybrid config loading
- dsn_discovery: Windows-specific ODBC DSN discovery
- orm_manager: ORM-based entity management
- ddl_manager: DDL operations (procedures, triggers, functions)
- file_operations: BLOB file upload/download
- type_mapper: Zen type conversions
- translator: INFORMATION_SCHEMA and SQL translation
"""

from .connection import ZenConnection
from .config import ZenConfiguration, ConnectionConfig, parse_args
from .orm_manager import ZenORMManager
from .ddl_manager import ZenDDLManager
from .file_operations import ZenFileManager
from .type_mapper import ZenTypeMapper
from .translator import InformationSchemaTranslator, translate_information_schema

__all__ = [
    # Connection & Config
    "ZenConnection",
    "ZenConfiguration",
    "ConnectionConfig",
    "parse_args",
    # Managers
    "ZenORMManager",
    "ZenDDLManager",
    "ZenFileManager",
    "ZenTypeMapper",
    # Translation
    "InformationSchemaTranslator",
    "translate_information_schema",
]
