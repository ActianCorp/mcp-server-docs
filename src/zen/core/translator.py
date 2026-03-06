# -*- coding: utf-8 -*-
################################################################################
#
#  sqlalchemy-zen -- SQLAlchemy Dialect for Actian Zen
#  Copyright 2025 Actian Corporation
#  See LICENSE.txt
#
#  INFORMATION_SCHEMA Translator Module
#
#  Actian Zen doesn't implement standard INFORMATION_SCHEMA views.
#  This module intercepts and translates INFORMATION_SCHEMA queries to
#  Zen's proprietary dbo.fSQL*() catalog functions.
#
################################################################################

import re
from typing import Optional, Dict, List, Tuple


class InformationSchemaTranslator:
    """
    Translates standard SQL INFORMATION_SCHEMA queries to Zen catalog functions.

    Zen uses proprietary functions instead of INFORMATION_SCHEMA views:
    - INFORMATION_SCHEMA.TABLES -> dbo.fSQLTables()
    - INFORMATION_SCHEMA.COLUMNS -> dbo.fSQLColumns()
    - INFORMATION_SCHEMA.TABLE_CONSTRAINTS -> dbo.fSQLPrimaryKeys() + dbo.fSQLForeignKeys()
    - INFORMATION_SCHEMA.KEY_COLUMN_USAGE -> dbo.fSQLPrimaryKeys() + dbo.fSQLForeignKeys()

    Column Mappings:
    ┌──────────────────────────────┬────────────────────────┬───────────────────┐
    │ INFORMATION_SCHEMA           │ Zen Function Column    │ Transform         │
    ├──────────────────────────────┼────────────────────────┼───────────────────┤
    │ TABLE_CATALOG                │ TABLE_QUALIFIER        │ Rename            │
    │ TABLE_SCHEMA                 │ TABLE_OWNER            │ Rename (NULL)     │
    │ TABLE_NAME                   │ TABLE_NAME             │ Direct            │
    │ TABLE_TYPE                   │ TABLE_TYPE             │ Map TABLE→BASE    │
    │ COLUMN_NAME                  │ COLUMN_NAME            │ Direct            │
    │ DATA_TYPE                    │ TYPE_NAME              │ Rename            │
    │ CHARACTER_MAXIMUM_LENGTH     │ LENGTH                 │ Rename            │
    │ NUMERIC_PRECISION            │ PRECISION              │ Rename            │
    │ NUMERIC_SCALE                │ SCALE                  │ Rename            │
    │ IS_NULLABLE                  │ IS_NULLABLE            │ Direct            │
    │ ORDINAL_POSITION             │ ORDINAL_POSITION       │ Direct            │
    └──────────────────────────────┴────────────────────────┴───────────────────┘
    """

    # Pattern to detect INFORMATION_SCHEMA queries
    _info_schema_pattern = re.compile(
        r'\bINFORMATION_SCHEMA\s*\.\s*(\w+)',
        re.IGNORECASE
    )

    # Column mappings: standard name -> Zen function column name
    _tables_column_map = {
        'TABLE_CATALOG': 'TABLE_QUALIFIER',
        'TABLE_SCHEMA': 'TABLE_OWNER',
        'TABLE_NAME': 'TABLE_NAME',
        'TABLE_TYPE': 'TABLE_TYPE',
    }

    _columns_column_map = {
        'TABLE_CATALOG': 'TABLE_QUALIFIER',
        'TABLE_SCHEMA': 'TABLE_OWNER',
        'TABLE_NAME': 'TABLE_NAME',
        'COLUMN_NAME': 'COLUMN_NAME',
        'ORDINAL_POSITION': 'ORDINAL_POSITION',
        'COLUMN_DEFAULT': 'COLUMN_DEF',
        'IS_NULLABLE': 'IS_NULLABLE',
        'DATA_TYPE': 'TYPE_NAME',
        'CHARACTER_MAXIMUM_LENGTH': 'LENGTH',
        'CHARACTER_OCTET_LENGTH': 'LENGTH',
        'NUMERIC_PRECISION': 'PRECISION',
        'NUMERIC_SCALE': 'SCALE',
    }

    _constraints_column_map = {
        'CONSTRAINT_CATALOG': 'TABLE_QUALIFIER',
        'CONSTRAINT_SCHEMA': 'TABLE_OWNER',
        'CONSTRAINT_NAME': 'PK_NAME',
        'TABLE_CATALOG': 'TABLE_QUALIFIER',
        'TABLE_SCHEMA': 'TABLE_OWNER',
        'TABLE_NAME': 'TABLE_NAME',
        'CONSTRAINT_TYPE': None,  # Derived from function used
    }

    @classmethod
    def needs_translation(cls, sql: str) -> bool:
        """Check if SQL contains INFORMATION_SCHEMA references that need translation."""
        if not sql:
            return False
        return bool(cls._info_schema_pattern.search(sql))

    @classmethod
    def translate(cls, sql: str) -> str:
        """
        Translate INFORMATION_SCHEMA queries to Zen catalog function calls.

        Args:
            sql: The SQL statement potentially containing INFORMATION_SCHEMA references

        Returns:
            Translated SQL using Zen catalog functions, or original SQL if no translation needed
        """
        if not cls.needs_translation(sql):
            return sql

        # Detect which INFORMATION_SCHEMA view is being queried
        match = cls._info_schema_pattern.search(sql)
        if not match:
            return sql

        view_name = match.group(1).upper()

        if view_name == 'TABLES':
            return cls._translate_tables_query(sql)
        elif view_name == 'COLUMNS':
            return cls._translate_columns_query(sql)
        elif view_name == 'TABLE_CONSTRAINTS':
            return cls._translate_constraints_query(sql)
        elif view_name == 'KEY_COLUMN_USAGE':
            return cls._translate_key_column_usage_query(sql)
        elif view_name == 'SCHEMATA':
            return cls._translate_schemata_query(sql)
        else:
            # Unsupported INFORMATION_SCHEMA view - return original
            return sql

    @classmethod
    def _translate_tables_query(cls, sql: str) -> str:
        """
        Translate INFORMATION_SCHEMA.TABLES query to dbo.fSQLTables().

        Standard query:
            SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'

        Zen translation:
            SELECT TABLE_QUALIFIER AS TABLE_CATALOG, TABLE_OWNER AS TABLE_SCHEMA,
                   TABLE_NAME,
                   CASE WHEN TABLE_TYPE = 'TABLE' THEN 'BASE TABLE' ELSE TABLE_TYPE END AS TABLE_TYPE
            FROM dbo.fSQLTables(NULL, NULL, NULL)
            WHERE TABLE_TYPE <> 'SYSTEM TABLE'
        """
        # Extract SELECT columns (if specified)
        select_match = re.match(
            r'SELECT\s+(.+?)\s+FROM\s+INFORMATION_SCHEMA\s*\.\s*TABLES',
            sql, re.IGNORECASE | re.DOTALL
        )

        # Extract WHERE clause
        where_match = re.search(
            r'WHERE\s+(.+?)(?:ORDER\s+BY|GROUP\s+BY|LIMIT|$)',
            sql, re.IGNORECASE | re.DOTALL
        )

        # Build the translated query
        if select_match:
            columns = select_match.group(1).strip()
            if columns == '*':
                # Replace * with explicit column list
                columns = """TABLE_QUALIFIER AS TABLE_CATALOG,
                       TABLE_OWNER AS TABLE_SCHEMA,
                       TABLE_NAME,
                       CASE WHEN TABLE_TYPE = 'TABLE' THEN 'BASE TABLE' ELSE TABLE_TYPE END AS TABLE_TYPE"""
            else:
                # Map individual columns
                columns = cls._map_columns(columns, cls._tables_column_map)
        else:
            columns = """TABLE_QUALIFIER AS TABLE_CATALOG,
                   TABLE_OWNER AS TABLE_SCHEMA,
                   TABLE_NAME,
                   CASE WHEN TABLE_TYPE = 'TABLE' THEN 'BASE TABLE' ELSE TABLE_TYPE END AS TABLE_TYPE"""

        # Build WHERE clause
        where_clause = ""
        if where_match:
            where_conditions = where_match.group(1).strip()
            # Translate column names in WHERE clause
            where_conditions = cls._translate_where_clause(where_conditions, cls._tables_column_map)
            # Handle TABLE_TYPE = 'BASE TABLE' -> TABLE_TYPE = 'TABLE'
            where_conditions = re.sub(
                r"TABLE_TYPE\s*=\s*'BASE TABLE'",
                "TABLE_TYPE = 'TABLE'",
                where_conditions, flags=re.IGNORECASE
            )
            where_clause = f"WHERE {where_conditions}"

        # Build the final query
        translated = f"""SELECT {columns}
FROM dbo.fSQLTables(NULL, NULL, NULL)
{where_clause}""".strip()

        return translated

    @classmethod
    def _translate_columns_query(cls, sql: str) -> str:
        """
        Translate INFORMATION_SCHEMA.COLUMNS query to dbo.fSQLColumns().

        Standard query:
            SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'my_table'

        Zen translation:
            SELECT COLUMN_NAME, TYPE_NAME AS DATA_TYPE
            FROM dbo.fSQLColumns(NULL, NULL, 'my_table', NULL)
        """
        # Extract table name from WHERE clause for optimization
        table_name = None
        table_match = re.search(
            r"TABLE_NAME\s*=\s*'([^']+)'",
            sql, re.IGNORECASE
        )
        if table_match:
            table_name = table_match.group(1)

        # Extract SELECT columns
        select_match = re.match(
            r'SELECT\s+(.+?)\s+FROM\s+INFORMATION_SCHEMA\s*\.\s*COLUMNS',
            sql, re.IGNORECASE | re.DOTALL
        )

        # Extract WHERE clause
        where_match = re.search(
            r'WHERE\s+(.+?)(?:ORDER\s+BY|GROUP\s+BY|LIMIT|$)',
            sql, re.IGNORECASE | re.DOTALL
        )

        # Build column list
        if select_match:
            columns = select_match.group(1).strip()
            if columns == '*':
                columns = """TABLE_QUALIFIER AS TABLE_CATALOG,
                       TABLE_OWNER AS TABLE_SCHEMA,
                       TABLE_NAME,
                       COLUMN_NAME,
                       ORDINAL_POSITION,
                       COLUMN_DEF AS COLUMN_DEFAULT,
                       IS_NULLABLE,
                       TYPE_NAME AS DATA_TYPE,
                       LENGTH AS CHARACTER_MAXIMUM_LENGTH,
                       PRECISION AS NUMERIC_PRECISION,
                       SCALE AS NUMERIC_SCALE"""
            else:
                columns = cls._map_columns(columns, cls._columns_column_map)
        else:
            columns = """TABLE_QUALIFIER AS TABLE_CATALOG,
                   TABLE_OWNER AS TABLE_SCHEMA,
                   TABLE_NAME,
                   COLUMN_NAME,
                   ORDINAL_POSITION,
                   COLUMN_DEF AS COLUMN_DEFAULT,
                   IS_NULLABLE,
                   TYPE_NAME AS DATA_TYPE,
                   LENGTH AS CHARACTER_MAXIMUM_LENGTH,
                   PRECISION AS NUMERIC_PRECISION,
                   SCALE AS NUMERIC_SCALE"""

        # Build function call with table name parameter if available
        # Zen fSQLColumns uses 3 parameters: fSQLColumns(database, table_name, column_name)
        if table_name:
            func_call = f"dbo.fSQLColumns(NULL, '{table_name}', NULL)"
            # Remove TABLE_NAME condition from WHERE since it's in the function
            if where_match:
                where_conditions = where_match.group(1).strip()
                # Remove TABLE_NAME = 'xxx' condition
                where_conditions = re.sub(
                    r"TABLE_NAME\s*=\s*'[^']+'\s*(AND\s*)?",
                    '', where_conditions, flags=re.IGNORECASE
                ).strip()
                # Remove trailing AND
                where_conditions = re.sub(r'\s*AND\s*$', '', where_conditions).strip()
                if where_conditions:
                    where_conditions = cls._translate_where_clause(where_conditions, cls._columns_column_map)
                    where_clause = f"WHERE {where_conditions}"
                else:
                    where_clause = ""
            else:
                where_clause = ""
        else:
            func_call = "dbo.fSQLColumns(NULL, NULL, NULL)"
            if where_match:
                where_conditions = where_match.group(1).strip()
                where_conditions = cls._translate_where_clause(where_conditions, cls._columns_column_map)
                where_clause = f"WHERE {where_conditions}"
            else:
                where_clause = ""

        translated = f"""SELECT {columns}
FROM {func_call}
{where_clause}""".strip()

        return translated

    @classmethod
    def _translate_constraints_query(cls, sql: str) -> str:
        """
        Translate INFORMATION_SCHEMA.TABLE_CONSTRAINTS query.

        Zen doesn't have a direct equivalent, so we use a UNION of:
        - dbo.fSQLPrimaryKeys() for PRIMARY KEY constraints
        - dbo.fSQLForeignKeys() for FOREIGN KEY constraints
        """
        # Extract table name if specified
        table_name = None
        table_match = re.search(
            r"TABLE_NAME\s*=\s*'([^']+)'",
            sql, re.IGNORECASE
        )
        if table_match:
            table_name = table_match.group(1)

        if table_name:
            translated = f"""SELECT DISTINCT
    TABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    TABLE_OWNER AS CONSTRAINT_SCHEMA,
    PK_NAME AS CONSTRAINT_NAME,
    TABLE_QUALIFIER AS TABLE_CATALOG,
    TABLE_OWNER AS TABLE_SCHEMA,
    TABLE_NAME,
    'PRIMARY KEY' AS CONSTRAINT_TYPE
FROM dbo.fSQLPrimaryKeys(NULL, '{table_name}')
WHERE PK_NAME IS NOT NULL
UNION ALL
SELECT DISTINCT
    FKTABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    FKTABLE_OWNER AS CONSTRAINT_SCHEMA,
    FK_NAME AS CONSTRAINT_NAME,
    FKTABLE_QUALIFIER AS TABLE_CATALOG,
    FKTABLE_OWNER AS TABLE_SCHEMA,
    FKTABLE_NAME AS TABLE_NAME,
    'FOREIGN KEY' AS CONSTRAINT_TYPE
FROM dbo.fSQLForeignKeys(NULL, NULL, '{table_name}')
WHERE FK_NAME IS NOT NULL"""
        else:
            # Query all constraints - this could be expensive
            translated = """SELECT DISTINCT
    TABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    TABLE_OWNER AS CONSTRAINT_SCHEMA,
    PK_NAME AS CONSTRAINT_NAME,
    TABLE_QUALIFIER AS TABLE_CATALOG,
    TABLE_OWNER AS TABLE_SCHEMA,
    TABLE_NAME,
    'PRIMARY KEY' AS CONSTRAINT_TYPE
FROM dbo.fSQLPrimaryKeys(NULL, '%')
WHERE PK_NAME IS NOT NULL
UNION ALL
SELECT DISTINCT
    FKTABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    FKTABLE_OWNER AS CONSTRAINT_SCHEMA,
    FK_NAME AS CONSTRAINT_NAME,
    FKTABLE_QUALIFIER AS TABLE_CATALOG,
    FKTABLE_OWNER AS TABLE_SCHEMA,
    FKTABLE_NAME AS TABLE_NAME,
    'FOREIGN KEY' AS CONSTRAINT_TYPE
FROM dbo.fSQLForeignKeys(NULL, '%', '%')
WHERE FK_NAME IS NOT NULL"""

        return translated

    @classmethod
    def _translate_key_column_usage_query(cls, sql: str) -> str:
        """
        Translate INFORMATION_SCHEMA.KEY_COLUMN_USAGE query.

        Uses dbo.fSQLPrimaryKeys() + dbo.fSQLForeignKeys() to get
        column usage in both primary and foreign keys.
        """
        # Extract table name if specified
        table_name = None
        table_match = re.search(
            r"TABLE_NAME\s*=\s*'([^']+)'",
            sql, re.IGNORECASE
        )
        if table_match:
            table_name = table_match.group(1)

        if table_name:
            translated = f"""SELECT
    TABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    TABLE_OWNER AS CONSTRAINT_SCHEMA,
    PK_NAME AS CONSTRAINT_NAME,
    TABLE_QUALIFIER AS TABLE_CATALOG,
    TABLE_OWNER AS TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    KEY_SEQ AS ORDINAL_POSITION
FROM dbo.fSQLPrimaryKeys(NULL, '{table_name}')
WHERE PK_NAME IS NOT NULL
UNION ALL
SELECT
    FKTABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    FKTABLE_OWNER AS CONSTRAINT_SCHEMA,
    FK_NAME AS CONSTRAINT_NAME,
    FKTABLE_QUALIFIER AS TABLE_CATALOG,
    FKTABLE_OWNER AS TABLE_SCHEMA,
    FKTABLE_NAME AS TABLE_NAME,
    FKCOLUMN_NAME AS COLUMN_NAME,
    KEY_SEQ AS ORDINAL_POSITION
FROM dbo.fSQLForeignKeys(NULL, NULL, '{table_name}')
WHERE FK_NAME IS NOT NULL"""
        else:
            translated = """SELECT
    TABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    TABLE_OWNER AS CONSTRAINT_SCHEMA,
    PK_NAME AS CONSTRAINT_NAME,
    TABLE_QUALIFIER AS TABLE_CATALOG,
    TABLE_OWNER AS TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME,
    KEY_SEQ AS ORDINAL_POSITION
FROM dbo.fSQLPrimaryKeys(NULL, '%')
WHERE PK_NAME IS NOT NULL
UNION ALL
SELECT
    FKTABLE_QUALIFIER AS CONSTRAINT_CATALOG,
    FKTABLE_OWNER AS CONSTRAINT_SCHEMA,
    FK_NAME AS CONSTRAINT_NAME,
    FKTABLE_QUALIFIER AS TABLE_CATALOG,
    FKTABLE_OWNER AS TABLE_SCHEMA,
    FKTABLE_NAME AS TABLE_NAME,
    FKCOLUMN_NAME AS COLUMN_NAME,
    KEY_SEQ AS ORDINAL_POSITION
FROM dbo.fSQLForeignKeys(NULL, '%', '%')
WHERE FK_NAME IS NOT NULL"""

        return translated

    @classmethod
    def _translate_schemata_query(cls, sql: str) -> str:
        """
        Translate INFORMATION_SCHEMA.SCHEMATA query.

        Zen doesn't have schemas in the traditional sense.
        Returns a single row with database name as schema.
        """
        translated = """SELECT
    dbmsinfo('database') AS CATALOG_NAME,
    'dbo' AS SCHEMA_NAME,
    NULL AS SCHEMA_OWNER,
    NULL AS DEFAULT_CHARACTER_SET_CATALOG,
    NULL AS DEFAULT_CHARACTER_SET_SCHEMA,
    NULL AS DEFAULT_CHARACTER_SET_NAME"""

        return translated

    @classmethod
    def _map_columns(cls, columns: str, column_map: Dict[str, str]) -> str:
        """
        Map standard INFORMATION_SCHEMA column names to Zen equivalents.

        Args:
            columns: Comma-separated column list from SELECT
            column_map: Dictionary mapping standard names to Zen names

        Returns:
            Translated column list with AS aliases for renamed columns
        """
        result_columns = []

        # Split by comma, handling potential function calls with commas
        col_list = cls._split_columns(columns)

        for col in col_list:
            col = col.strip()
            # Check if column has an alias
            alias_match = re.match(r'(.+?)\s+AS\s+(\w+)', col, re.IGNORECASE)
            if alias_match:
                orig_col = alias_match.group(1).strip()
                alias = alias_match.group(2).strip()
                zen_col = column_map.get(orig_col.upper(), orig_col)
                if zen_col != orig_col:
                    result_columns.append(f"{zen_col} AS {alias}")
                else:
                    result_columns.append(col)
            else:
                # No alias - add one if mapping exists
                col_upper = col.upper()
                if col_upper in column_map:
                    zen_col = column_map[col_upper]
                    if zen_col != col_upper:
                        result_columns.append(f"{zen_col} AS {col}")
                    else:
                        result_columns.append(col)
                else:
                    result_columns.append(col)

        return ', '.join(result_columns)

    @classmethod
    def _translate_where_clause(cls, where_clause: str, column_map: Dict[str, str]) -> str:
        """
        Translate column names in WHERE clause.

        Args:
            where_clause: The WHERE clause conditions (without WHERE keyword)
            column_map: Dictionary mapping standard names to Zen names

        Returns:
            Translated WHERE clause
        """
        result = where_clause

        # Replace column names with Zen equivalents
        for std_col, zen_col in column_map.items():
            if zen_col and zen_col != std_col:
                # Use word boundary to avoid partial matches
                pattern = r'\b' + re.escape(std_col) + r'\b'
                result = re.sub(pattern, zen_col, result, flags=re.IGNORECASE)

        return result

    @classmethod
    def _split_columns(cls, columns: str) -> List[str]:
        """
        Split column list by commas, handling function calls that contain commas.

        Args:
            columns: Comma-separated column list

        Returns:
            List of individual columns
        """
        result = []
        depth = 0
        current = []

        for char in columns:
            if char == '(':
                depth += 1
                current.append(char)
            elif char == ')':
                depth -= 1
                current.append(char)
            elif char == ',' and depth == 0:
                result.append(''.join(current).strip())
                current = []
            else:
                current.append(char)

        if current:
            result.append(''.join(current).strip())

        return result


# Convenience function for direct use
def translate_information_schema(sql: str) -> str:
    """
    Convenience function to translate INFORMATION_SCHEMA queries.

    Args:
        sql: SQL statement to translate

    Returns:
        Translated SQL or original if no translation needed
    """
    return InformationSchemaTranslator.translate(sql)
