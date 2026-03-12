"""
Zen DDL Manager - High-level DDL operations using SQLAlchemy Zen dialect

Modified for actian-zen: Uses ZenConnection for connection string,
but creates separate NullPool engine for DDL safety.
"""

import re

from sqlalchemy import create_engine, MetaData, Table, Column, text
from sqlalchemy.pool import NullPool
from sqlalchemy_zen.ddl_elements import (
    CreateProcedure, DropProcedure,
    CreateTrigger, DropTrigger,
    CreateFunction, DropFunction
)
from .type_mapper import ZenTypeMapper

_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_#]*$')

def _validate_identifier(name, kind="identifier"):
    if not name or not _IDENT_RE.match(name):
        raise ValueError(f"Invalid {kind}: {name!r}")

class ZenDDLManager:
    """Manage DDL operations for Zen database"""

    def __init__(self, connection):
        """
        Initialize DDL manager.

        DDL operations require special handling:
        - NullPool: Don't hold connections between operations (prevents Error 85)
        - autocommit=True: DDL statements auto-commit immediately

        Args:
            connection: ZenConnection instance (preferred) or connection string (legacy)
        """
        # Import here to avoid circular import
        from .connection import ZenConnection

        if isinstance(connection, ZenConnection):
            # Get connection string from ZenConnection
            conn_string = connection.conn_string
            self._zen_connection = connection
        else:
            # Legacy: use provided string
            conn_string = connection
            self._zen_connection = None

        if not conn_string.startswith('zen://'):
            conn_string = f"zen://?odbc_connect={conn_string}"

        # DDL always uses NullPool to avoid holding connections
        # This prevents Btrieve Error 85 (file locked) during ALTER/DROP TABLE
        self.engine = create_engine(conn_string, echo=False, poolclass=NullPool)

        # Set autocommit on pyodbc connections to prevent DDL transaction locks
        from sqlalchemy import event
        @event.listens_for(self.engine, "connect")
        def set_autocommit(dbapi_connection, connection_record):
            dbapi_connection.autocommit = True

        self.metadata = MetaData()
        self.type_mapper = ZenTypeMapper()

    def create_procedure(self, name, parameters, body, atomic=True):
        """
        Create a stored procedure.

        Args:
            name: Procedure name
            parameters: List of (param_name, param_type) tuples
            body: Procedure body SQL
            atomic: Whether procedure should be ATOMIC

        Returns:
            Dict with procedure info and generated DDL
        """
        proc = CreateProcedure(name, parameters, body, atomic)

        with self.engine.connect() as conn:
            # Compile and execute
            compiled = str(proc.compile(dialect=self.engine.dialect))
            conn.execute(text(compiled))
            conn.commit()

        return {
            'name': name,
            'type': 'procedure',
            'created': True,
            'parameters': parameters,
            'atomic': atomic,
            'ddl': compiled
        }

    def drop_procedure(self, name):
        """Drop a stored procedure"""
        drop = DropProcedure(name)

        with self.engine.connect() as conn:
            compiled = str(drop.compile(dialect=self.engine.dialect))
            conn.execute(text(compiled))
            conn.commit()

        return {
            'name': name,
            'type': 'procedure',
            'dropped': True
        }

    def create_trigger(self, name, table, timing, event, body, **options):
        """
        Create a trigger.

        Args:
            name: Trigger name
            table: Table name
            timing: 'BEFORE' or 'AFTER'
            event: 'INSERT', 'UPDATE', or 'DELETE'
            body: Trigger body SQL
            **options: referencing, when

        Returns:
            Dict with trigger info and generated DDL
        """
        trigger = CreateTrigger(
            name=name,
            table=table,
            timing=timing,
            event=event,
            body=body,
            referencing=options.get('referencing'),
            when=options.get('when')
        )

        with self.engine.connect() as conn:
            compiled = str(trigger.compile(dialect=self.engine.dialect))
            conn.execute(text(compiled))
            conn.commit()

        return {
            'name': name,
            'type': 'trigger',
            'table': table,
            'timing': timing,
            'event': event,
            'created': True,
            'ddl': compiled
        }

    def drop_trigger(self, name):
        """Drop a trigger"""
        drop = DropTrigger(name)

        with self.engine.connect() as conn:
            compiled = str(drop.compile(dialect=self.engine.dialect))
            conn.execute(text(compiled))
            conn.commit()

        return {
            'name': name,
            'type': 'trigger',
            'dropped': True
        }

    def create_function(self, name, parameters, returns, body):
        """
        Create a user-defined function.

        Args:
            name: Function name
            parameters: List of (param_name, param_type) tuples
            returns: Return type
            body: Function body SQL

        Returns:
            Dict with function info and generated DDL
        """
        func = CreateFunction(name, parameters, returns, body)

        with self.engine.connect() as conn:
            compiled = str(func.compile(dialect=self.engine.dialect))
            conn.execute(text(compiled))
            conn.commit()

        return {
            'name': name,
            'type': 'function',
            'returns': returns,
            'parameters': parameters,
            'created': True,
            'ddl': compiled
        }

    def drop_function(self, name):
        """Drop a user-defined function"""
        drop = DropFunction(name)

        with self.engine.connect() as conn:
            compiled = str(drop.compile(dialect=self.engine.dialect))
            conn.execute(text(compiled))
            conn.commit()

        return {
            'name': name,
            'type': 'function',
            'dropped': True
        }

    def create_table_with_zen_options(self, table_name, columns, **zen_options):
        """
        Create table with Zen-specific options.

        Args:
            table_name: Table name
            columns: List of column definitions
            **zen_options: Zen-specific options (compression, linkdup, etc.)

        Returns:
            Dict with table info and generated DDL
        """
        # Build columns with Zen types
        table_columns = []
        for col_def in columns:
            col_type = self.type_mapper.from_string(
                col_def['type'],
                length=col_def.get('length'),
                precision=col_def.get('precision'),
                scale=col_def.get('scale')
            )

            column = Column(
                col_def['name'],
                col_type,
                nullable=col_def.get('nullable', True),
                primary_key=col_def.get('primary_key', False),
                autoincrement=col_def.get('autoincrement', False)
            )

            # Add case sensitivity info
            if not col_def.get('case_sensitive', True):
                column.info['case_sensitive'] = False

            # Add collation info
            if col_def.get('collation'):
                column.info['collation'] = col_def['collation']

            table_columns.append(column)

        # Create table object
        table = Table(table_name, self.metadata, *table_columns)

        # Add Zen options
        if zen_options:
            table.dialect_options['zen'] = zen_options

        # Generate and execute DDL
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        generator = DDLGenerator(table, self.engine.dialect)
        ddl = generator.create_table()

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'created': True,
            'columns': len(columns),
            'zen_options': zen_options,
            'ddl': ddl
        }

    def create_index(self, table_name, index_name, columns):
        """
        Create an index on a table.

        Args:
            table_name: Table name
            index_name: Index name
            columns: List of column names

        Returns:
            Dict with index info and generated DDL
        """
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        from sqlalchemy import Table, Column, String, MetaData

        # Create a minimal table object for the generator with fresh metadata
        temp_metadata = MetaData()
        table_columns = [Column(col, String) for col in columns]
        table = Table(table_name, temp_metadata, *table_columns)

        generator = DDLGenerator(table, self.engine.dialect)
        ddl = generator.create_index(index_name, *[table.c[col] for col in columns])

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'index_name': index_name,
            'columns': columns,
            'created': True,
            'ddl': ddl
        }

    def drop_index(self, table_name, index_name, columns):
        """
        Drop an index from a table.

        Args:
            table_name: Table name
            index_name: Index name
            columns: List of column names

        Returns:
            Dict with index info and generated DDL
        """
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        from sqlalchemy import Table, Column, String, MetaData

        # Create a minimal table object for the generator with fresh metadata
        temp_metadata = MetaData()
        table_columns = [Column(col, String) for col in columns]
        table = Table(table_name, temp_metadata, *table_columns)

        generator = DDLGenerator(table, self.engine.dialect)
        ddl = generator.drop_index(index_name, *[table.c[col] for col in columns])

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'index_name': index_name,
            'columns': columns,
            'dropped': True,
            'ddl': ddl
        }

    def drop_foreign_key(self, table_name, constraint_name):
        """
        Drop a foreign key constraint from a table.

        Args:
            table_name: Table name
            constraint_name: Foreign key constraint name

        Returns:
            Dict with constraint info and generated DDL
        """
        _validate_identifier(table_name, "table name")
        _validate_identifier(constraint_name, "constraint name")
        # Zen syntax: ALTER TABLE table_name DROP CONSTRAINT constraint_name
        ddl = f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
        
        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'constraint_name': constraint_name,
            'dropped': True,
            'ddl': ddl
        }

    def add_column(self, table_name, column_name, column_type, **options):
        """
        Add a column to a table.

        Args:
            table_name: Table name
            column_name: Column name
            column_type: Column type (Zen type string)
            **options: Column options (nullable, length, precision, scale, etc.)

        Returns:
            Dict with column info and generated DDL
        """
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        from sqlalchemy import Table, Column, String, MetaData

        # Create a minimal table object for the generator with fresh metadata
        temp_metadata = MetaData()
        table = Table(table_name, temp_metadata, Column('dummy', String))
        generator = DDLGenerator(table, self.engine.dialect)

        # Map the type
        col_type = self.type_mapper.from_string(
            column_type,
            length=options.get('length'),
            precision=options.get('precision'),
            scale=options.get('scale')
        )

        ddl = generator.add_column(column_name, col_type)

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'column': column_name,
            'type': column_type,
            'added': True,
            'ddl': ddl
        }

    def drop_column(self, table_name, column_name):
        """
        Drop a column from a table.

        Args:
            table_name: Table name
            column_name: Column name

        Returns:
            Dict with column info and generated DDL
        """
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        from sqlalchemy import Table, Column, String, MetaData

        # Create a minimal table object for the generator with fresh metadata
        temp_metadata = MetaData()
        table = Table(table_name, temp_metadata, Column('dummy', String))
        generator = DDLGenerator(table, self.engine.dialect)

        ddl = generator.drop_column(column_name)

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'column': column_name,
            'dropped': True,
            'ddl': ddl
        }

    def alter_table_with(self, table_name, with_clause):
        """
        Execute ALTER TABLE WITH statement (Zen-specific).

        **LIMITATION**: Zen database does NOT support ALTER TABLE WITH syntax.
        Table options (PAGESIZE, COMPRESSION, etc.) can only be set during
        CREATE TABLE, not modified afterwards.

        This method will attempt to execute the statement but is expected to fail
        with a Zen syntax error.

        **Workaround**: Use create_table_with_zen_options() to set table options
        at table creation time.

        Args:
            table_name: Table name
            with_clause: WITH clause content (e.g., "PAGESIZE = 4096")

        Returns:
            Dict with table info and generated DDL (will fail with syntax error)

        Raises:
            CompileError: Zen does not support ALTER TABLE WITH syntax

        Example (WILL FAIL):
            alter_table_with("products", "PAGESIZE = 4096")
            # Error: Syntax Error: ALTER TABLE products WITH<< ??? >> PAGESIZE = 4096
        """
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        from sqlalchemy import Table, Column, String, MetaData

        # Create a minimal table object for the generator with fresh metadata
        temp_metadata = MetaData()
        table = Table(table_name, temp_metadata, Column('dummy', String))
        generator = DDLGenerator(table, self.engine.dialect)

        ddl = generator.alter_table_with(with_clause)

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'with_clause': with_clause,
            'altered': True,
            'ddl': ddl
        }

    def create_view(self, view_name, select_clause):
        """
        Create a view.

        Args:
            view_name: View name
            select_clause: SELECT statement for the view

        Returns:
            Dict with view info and generated DDL
        """
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        from sqlalchemy import Table, Column, String, MetaData

        # Create a minimal table object for the generator with fresh metadata
        temp_metadata = MetaData()
        table = Table('dummy', temp_metadata, Column('dummy', String))
        generator = DDLGenerator(table, self.engine.dialect)

        ddl = generator.create_view(view_name, select_clause)

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'view': view_name,
            'created': True,
            'ddl': ddl
        }

    def drop_view(self, view_name):
        """
        Drop a view.

        Args:
            view_name: View name

        Returns:
            Dict with view info and generated DDL
        """
        from sqlalchemy_zen.ddl_generator import DDLGenerator
        from sqlalchemy import Table, Column, String, MetaData

        # Create a minimal table object for the generator with fresh metadata
        temp_metadata = MetaData()
        table = Table('dummy', temp_metadata, Column('dummy', String))
        generator = DDLGenerator(table, self.engine.dialect)

        ddl = generator.drop_view(view_name)

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'view': view_name,
            'dropped': True,
            'ddl': ddl
        }

    def rename_table(self, old_name, new_name):
        """
        Rename a table using Zen-specific syntax.

        Zen uses: ALTER TABLE RENAME old_name TO new_name
        NOT the standard: ALTER TABLE old_name RENAME TO new_name

        Args:
            old_name: Current table name (20 char limit)
            new_name: New table name (20 char limit)

        Returns:
            Dict with rename info and DDL executed

        Raises:
            ValueError if table names exceed 20 character limit
            Exception if old table doesn't exist or new name already exists
        """
        # Validate table name lengths (Zen limit: 20 chars)
        if len(old_name) > 20:
            raise ValueError(f"Old table name '{old_name}' exceeds 20 character limit")
        if len(new_name) > 20:
            raise ValueError(f"New table name '{new_name}' exceeds 20 character limit")

        # Zen syntax: ALTER TABLE RENAME old_name TO new_name
        ddl = f'ALTER TABLE RENAME "{old_name}" TO "{new_name}"'

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'old_name': old_name,
            'new_name': new_name,
            'renamed': True,
            'zen_syntax': True,
            'ddl': ddl
        }

    def drop_table(self, table_name):
        """
        Drop a table.

        Args:
            table_name: Name of table to drop

        Returns:
            Dict with drop info and DDL executed
        """
        ddl = f'DROP TABLE "{table_name}"'

        with self.engine.connect() as conn:
            conn.execute(text(ddl))
            conn.commit()

        return {
            'table': table_name,
            'dropped': True,
            'ddl': ddl
        }

    def close(self):
        """Close engine connections"""
        self.engine.dispose()
