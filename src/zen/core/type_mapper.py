"""
Zen Type Mapper - Convert between Python, SQLAlchemy, and Zen types
"""

from sqlalchemy_zen.types import (
    ZenBit, ZenTinyInt, ZenSmallIdentity, ZenIdentity, ZenBigIdentity,
    ZenMoney, ZenCurrency, ZenBFloat, ZenBFloat8,
    ZenDate, ZenDateTime, ZenTime, ZenAutoTimestamp,
    ZenNVarchar, ZenNLongVarchar, ZenBinary,
    ZenUTinyInt, ZenUSmallInt, ZenUInteger, ZenUBigInt,
    ZenLegacyNumeric
)
from sqlalchemy import types as sa_types

class ZenTypeMapper:
    """Map between different type representations"""

    # Python type → SQLAlchemy Zen type
    PYTHON_TO_ZEN = {
        bool: ZenBit,
        int: sa_types.Integer,
        float: sa_types.Float,
        str: sa_types.String,
        bytes: ZenBinary,
    }

    # String type name → SQLAlchemy Zen type class
    STRING_TO_ZEN = {
        # Boolean/Bit
        'BIT': ZenBit,
        'BOOLEAN': ZenBit,

        # Signed integers
        'TINYINT': ZenTinyInt,
        'SMALLINT': sa_types.SmallInteger,
        'INTEGER': sa_types.Integer,
        'INT': sa_types.Integer,
        'BIGINT': sa_types.BigInteger,

        # Unsigned integers
        'UTINYINT': ZenUTinyInt,
        'USMALLINT': ZenUSmallInt,
        'UINTEGER': ZenUInteger,
        'UBIGINT': ZenUBigInt,

        # Identity (auto-increment)
        'SMALLIDENTITY': ZenSmallIdentity,
        'IDENTITY': ZenIdentity,
        'BIGIDENTITY': ZenBigIdentity,

        # Financial
        'MONEY': ZenMoney,
        'CURRENCY': ZenCurrency,

        # Floating point
        'FLOAT': sa_types.Float,
        'REAL': sa_types.Float,
        'DOUBLE': sa_types.Double,
        'BFLOAT4': ZenBFloat,
        'BFLOAT8': ZenBFloat8,

        # Date/Time
        'DATE': ZenDate,
        'TIME': ZenTime,
        'DATETIME': ZenDateTime,
        'TIMESTAMP': ZenDateTime,
        'AUTOTIMESTAMP': ZenAutoTimestamp,

        # String (ASCII)
        'CHAR': sa_types.CHAR,
        'VARCHAR': sa_types.VARCHAR,
        'TEXT': sa_types.TEXT,
        'LONGVARCHAR': sa_types.TEXT,

        # String (Unicode)
        'NCHAR': sa_types.NCHAR,
        'NVARCHAR': ZenNVarchar,
        'NTEXT': ZenNLongVarchar,
        'NLONGVARCHAR': ZenNLongVarchar,

        # Binary
        'BINARY': sa_types.BINARY,
        'VARBINARY': sa_types.VARBINARY,
        'LONGVARBINARY': ZenBinary,
        'BLOB': ZenBinary,

        # Numeric
        'NUMERIC': sa_types.Numeric,
        'DECIMAL': sa_types.Numeric,
    }

    @classmethod
    def from_string(cls, type_string, **params):
        """
        Convert string type name to SQLAlchemy Zen type.

        Args:
            type_string: Type name (e.g., "VARCHAR", "INTEGER", "MONEY")
            **params: Type parameters (length, precision, scale)

        Returns:
            SQLAlchemy type instance
        """
        type_upper = type_string.upper().split('(')[0].strip()

        if type_upper not in cls.STRING_TO_ZEN:
            # Unknown type, default to VARCHAR
            return sa_types.VARCHAR(params.get('length', 255))

        type_class = cls.STRING_TO_ZEN[type_upper]

        # Handle types with parameters
        if 'VARCHAR' in type_upper or 'CHAR' in type_upper:
            length = params.get('length', 255)
            return type_class(length) if type_class != sa_types.CHAR else sa_types.CHAR(length)
        elif type_upper in ('NUMERIC', 'DECIMAL'):
            precision = params.get('precision', 18)
            scale = params.get('scale', 2)
            return type_class(precision, scale)
        else:
            # Types without parameters
            return type_class()

    @classmethod
    def from_python_type(cls, python_type):
        """Convert Python type to SQLAlchemy Zen type"""
        if python_type in cls.PYTHON_TO_ZEN:
            return cls.PYTHON_TO_ZEN[python_type]()
        return sa_types.String()

    @classmethod
    def get_zen_sql_type(cls, sqlalchemy_type):
        """Get Zen SQL type string from SQLAlchemy type"""
        from sqlalchemy_zen.dialect import ZenTypeCompiler
        from sqlalchemy_zen.base import ZenDialect

        dialect = ZenDialect()
        compiler = ZenTypeCompiler(dialect)
        return compiler.process(sqlalchemy_type)

    @classmethod
    def get_type_info(cls, type_obj):
        """Get detailed information about a type"""
        return {
            'python_type': type_obj.python_type.__name__ if hasattr(type_obj, 'python_type') else None,
            'sql_type': cls.get_zen_sql_type(type_obj),
            'nullable': getattr(type_obj, 'nullable', True),
            'length': getattr(type_obj, 'length', None),
            'precision': getattr(type_obj, 'precision', None),
            'scale': getattr(type_obj, 'scale', None),
        }
