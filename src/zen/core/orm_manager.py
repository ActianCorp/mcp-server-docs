"""
Zen ORM Manager - ORM-based entity management

Modified for actian-zen: Uses ZenConnection for shared engine management.
"""

from sqlalchemy import create_engine, select, and_, or_, func, text, literal_column, exists, union
import re
import time
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.inspection import inspect as sqlalchemy_inspect

Base = declarative_base()

class ZenORMManager:
    """Manage ORM operations for Zen database"""

    def __init__(self, connection):
        """
        Initialize ORM manager.

        Args:
            connection: ZenConnection instance (preferred) or connection string (legacy)
        """
        # Import here to avoid circular import
        from .connection import ZenConnection

        if isinstance(connection, ZenConnection):
            # Use shared engine from ZenConnection
            self.engine = connection.get_engine()
            self._owns_engine = False
            self._zen_connection = connection
        else:
            # Legacy: create own engine from connection string
            connection_string = connection
            if not connection_string.startswith('zen://'):
                connection_string = f"zen://?odbc_connect={connection_string}"

            self.engine = create_engine(
                connection_string,
                echo=False,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            self._owns_engine = True
            self._zen_connection = None

        self.Session = sessionmaker(bind=self.engine)
        self.metadata = Base.metadata
        self.metadata.bind = self.engine

        # Model cache: {table_name: (model_class, timestamp)}
        # TTL: 5 minutes (300 seconds)
        self._model_cache = {}
        self._model_cache_ttl = 300

    def get_model_class(self, table_name):
        """
        Get or create ORM model class for a table with proper IDENTITY handling.

        This dynamically creates a model class based on reflected metadata,
        and ensures IDENTITY columns are properly configured as autoincrement.

        Also handles Zen ODBC driver not reporting primary key constraints by
        inferring the PK from column properties.

        Uses caching with 5-minute TTL to avoid redundant schema reflection.
        """
        from sqlalchemy import Table, Column, inspect

        # Check cache first
        if table_name in self._model_cache:
            cached_model, cached_at = self._model_cache[table_name]
            cache_age = time.time() - cached_at
            if cache_age < self._model_cache_ttl:
                # Cache hit - return cached model
                return cached_model
            else:
                # Cache expired - remove from cache
                del self._model_cache[table_name]

        # Cache miss or expired - create new model
        # Get column info first to check for potential primary keys
        inspector = inspect(self.engine)
        columns_info = inspector.get_columns(table_name)

        # Check if table has a primary key constraint reported
        pk_constraint = inspector.get_pk_constraint(table_name)
        has_pk = bool(pk_constraint.get('constrained_columns'))

        # If no PK reported, infer one from column properties
        pk_column_override = None
        if not has_pk:
            # Look for likely primary key columns
            for col_info in columns_info:
                col_name = col_info['name']
                col_type = str(col_info['type']).upper()
                is_nullable = col_info.get('nullable', True)

                # Common PK patterns: ID column, or non-nullable INTEGER/BIGINT
                if col_name.upper() == 'ID' and not is_nullable:
                    pk_column_override = (col_name, col_info['type'])
                    break
                elif (col_name.upper().endswith('_ID') and
                      not is_nullable and
                      ('INT' in col_type or 'BIGINT' in col_type)):
                    pk_column_override = (col_name, col_info['type'])
                    # Don't break - prefer 'ID' over '*_ID'

        # Reflect the table, with PK override if needed
        if pk_column_override:
            col_name, col_type = pk_column_override
            table = Table(
                table_name,
                self.metadata,
                Column(col_name, col_type, primary_key=True),
                autoload_with=self.engine,
                extend_existing=True
            )
        else:
            table = Table(table_name, self.metadata, autoload_with=self.engine)

        # Dialect now correctly detects IDENTITY via TYPE_NAME field
        # No need to override autoincrement - trust the dialect

        # Create dynamic model class
        class DynamicModel(Base):
            __table__ = table
            __tablename__ = table_name

        # Cache the model with current timestamp
        self._model_cache[table_name] = (DynamicModel, time.time())

        return DynamicModel

    def _parse_aggregate_expression(self, expr):
        """
        Parse aggregate function expressions from columns array.

        Handles formats like:
        - "COUNT(*)"
        - "COUNT(*) as count"
        - "COUNT(*) AS person_count"
        - "SUM(Salary)"
        - "AVG(Age) as avg_age"
        - "MIN(Date_Of_Birth)"
        - "MAX(Salary) AS max_salary"
        - "SUM(CAST(amount AS DECIMAL(10,2))) AS total"  (complex expressions)
        - "COUNT(DISTINCT employee_id) AS unique_employees"

        Args:
            expr: String expression to parse

        Returns:
            dict with 'function', 'column'/'expression', 'alias' if aggregate, None otherwise
        """
        import re

        # Enhanced pattern: FUNC(anything) [AS alias]
        # Supports: COUNT, SUM, AVG, MIN, MAX with complex expressions
        # Uses non-greedy matching to find the outermost function call
        pattern = r'^(COUNT|SUM|AVG|MIN|MAX)\s*\((.+?)\)\s*(?:(?:AS|as)\s+(\w+))?$'
        match = re.match(pattern, expr.strip(), re.IGNORECASE)

        if match:
            func_name = match.group(1).upper()
            inner_expr = match.group(2).strip()
            alias = match.group(3) if match.group(3) else None

            # Check if inner expression is simple or complex
            if inner_expr == '*':
                # COUNT(*)
                column_or_expr = '*'
            elif re.match(r'^[\w]+$', inner_expr):
                # Simple column name: SUM(amount)
                column_or_expr = inner_expr
            else:
                # Complex expression: SUM(CAST(amount AS DECIMAL(10,2)))
                # or COUNT(DISTINCT employee_id)
                column_or_expr = inner_expr

            # Generate default alias if not provided
            if not alias:
                if column_or_expr == '*':
                    alias = f"{func_name.lower()}_star"
                elif re.match(r'^[\w]+$', column_or_expr):
                    alias = f"{func_name.lower()}_{column_or_expr}"
                else:
                    # For complex expressions, use just the function name
                    alias = f"{func_name.lower()}_result"

            return {
                'function': func_name,
                'expression': column_or_expr,  # Can be column name or complex expression
                'alias': alias
            }

        return None

    def _parse_date_expression(self, expr):
        """
        Parse date extraction expressions from columns array.

        Handles formats like:
        - "YEAR(Date_Of_Birth)"
        - "MONTH(created_at) as birth_month"
        - "EXTRACT(YEAR FROM date_column)"
        - "DATEPART(year, date_column)"

        All are converted to Zen's DATEPART syntax.
        """
        # Pattern 1: Simple date functions - YEAR(col), MONTH(col), DAY(col), etc.
        simple_pattern = r'^(YEAR|MONTH|DAY|HOUR|MINUTE|SECOND)\s*\(\s*([\w]+)\s*\)\s*(?:(?:AS|as)\s+(\w+))?$'
        match = re.match(simple_pattern, expr.strip(), re.IGNORECASE)
        if match:
            unit = match.group(1).upper()
            column = match.group(2)
            alias = match.group(3) if match.group(3) else f"{unit.lower()}_{column}"
            return {'expression': f'DATEPART({unit}, {column})', 'alias': alias}

        # Pattern 2: EXTRACT(unit FROM column) [AS alias]
        extract_pattern = r'^EXTRACT\s*\(\s*(\w+)\s+FROM\s+([\w]+)\s*\)\s*(?:(?:AS|as)\s+(\w+))?$'
        match = re.match(extract_pattern, expr.strip(), re.IGNORECASE)
        if match:
            unit = match.group(1).upper()
            column = match.group(2)
            alias = match.group(3) if match.group(3) else f"{unit.lower()}_{column}"
            return {'expression': f'DATEPART({unit}, {column})', 'alias': alias}

        # Pattern 3: Already in DATEPART(unit, column) format [AS alias]
        datepart_pattern = r'^DATEPART\s*\(\s*(\w+)\s*,\s*([\w]+)\s*\)\s*(?:(?:AS|as)\s+(\w+))?$'
        match = re.match(datepart_pattern, expr.strip(), re.IGNORECASE)
        if match:
            unit = match.group(1).upper()
            column = match.group(2)
            alias = match.group(3) if match.group(3) else f"{unit.lower()}_{column}"
            return {'expression': f'DATEPART({unit}, {column})', 'alias': alias}

        # Pattern 4: Date/time literal functions
        datetime_funcs = {
            'CURRENT_DATE': 'CURRENT_DATE()', 'CURRENT_TIME': 'CURRENT_TIME()',
            'CURRENT_TIMESTAMP': 'CURRENT_TIMESTAMP()', 'NOW': 'NOW()', 'GETDATE': 'GETDATE()',
        }
        datetime_pattern = r'^(CURRENT_DATE|CURRENT_TIME|CURRENT_TIMESTAMP|NOW|GETDATE)\s*(\(\s*\))?\s*(?:(?:AS|as)\s+(\w+))?$'
        match = re.match(datetime_pattern, expr.strip(), re.IGNORECASE)
        if match:
            func_name = match.group(1).upper()
            alias = match.group(3) if match.group(3) else func_name.lower()
            zen_func = datetime_funcs.get(func_name, f'{func_name}()')
            return {'expression': zen_func, 'alias': alias}

        return None

    def _parse_window_function(self, expr):
        """
        Parse window function expressions from columns array.

        Handles formats like:
        - "ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC)"
        - "ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC) as salary_rank"
        - "RANK() OVER (ORDER BY total_sales DESC) AS sales_rank"

        Returns dict with 'expression' and 'alias' that will be processed by
        _execute_aggregation_query(), which uses literal_column() to pass it
        through to SQLAlchemy Engine's do_execute(), triggering _rewrite_window_functions().

        Args:
            expr: String expression to parse

        Returns:
            dict with 'expression' and 'alias' if window function, None otherwise
        """
        import re

        # Pattern: WINDOW_FUNC() OVER (...)  [AS alias]
        # Supports: ROW_NUMBER, RANK, DENSE_RANK, NTILE
        pattern = r'^(ROW_NUMBER|RANK|DENSE_RANK|NTILE)\s*\(\s*\)\s+OVER\s*\('

        if re.search(pattern, expr.strip(), re.IGNORECASE):
            # Extract alias if present
            alias_match = re.search(r'\s+(?:AS|as)\s+(\w+)\s*$', expr.strip())

            if alias_match:
                alias = alias_match.group(1)
                # Remove the alias part to get clean expression
                expression = expr[:alias_match.start()].strip()
            else:
                # No alias - generate default
                alias = 'window_function_result'
                expression = expr.strip()

            # Return dict format that _execute_aggregation_query expects
            return {
                'expression': expression,
                'alias': alias
            }

        return None

    def _normalize_zen_expression(self, expr):
        """
        Normalize SQL expressions for Zen database dialect.

        Transforms standard SQL date functions to Zen-specific syntax:
        - DATEDIFF(date1, date2) -> DATEDIFF(DAY, date2, date1)
        - DATE_ADD(date, INTERVAL n DAY) -> DATEADD(DAY, n, date)
        - CURRENT_DATE -> CURRENT_DATE()

        Args:
            expr: SQL expression string

        Returns:
            Normalized expression string for Zen database
        """
        result = expr

        # Normalize DATEDIFF: Standard SQL uses 2 params, Zen uses 3 with unit first
        # Pattern: DATEDIFF(date1, date2) -> DATEDIFF(DAY, date2, date1)
        datediff_pattern = r'DATEDIFF\s*\(\s*([^,]+?)\s*,\s*([^)]+?)\s*\)'
        datediff_match = re.search(datediff_pattern, result, re.IGNORECASE)
        if datediff_match:
            date1 = datediff_match.group(1).strip()
            date2 = datediff_match.group(2).strip()
            # Zen syntax: DATEDIFF(unit, start_date, end_date)
            # Standard: DATEDIFF(end_date, start_date) returns end - start
            # So we swap: DATEDIFF(DAY, date2, date1) to get date1 - date2
            result = re.sub(datediff_pattern, f'DATEDIFF(DAY, {date2}, {date1})', result, flags=re.IGNORECASE)

        # Normalize DATE_ADD: Standard SQL -> Zen DATEADD
        # Pattern: DATE_ADD(date, INTERVAL n unit) -> DATEADD(unit, n, date)
        date_add_pattern = r'DATE_ADD\s*\(\s*([^,]+?)\s*,\s*INTERVAL\s+(\d+)\s+(\w+)\s*\)'
        date_add_match = re.search(date_add_pattern, result, re.IGNORECASE)
        if date_add_match:
            date_col = date_add_match.group(1).strip()
            interval_val = date_add_match.group(2).strip()
            interval_unit = date_add_match.group(3).strip().upper()
            result = re.sub(date_add_pattern, f'DATEADD({interval_unit}, {interval_val}, {date_col})', result, flags=re.IGNORECASE)

        # Normalize CURRENT_DATE -> CURRENT_DATE() for Zen
        # But only if not already followed by parentheses
        result = re.sub(r'\bCURRENT_DATE\b(?!\s*\()', 'CURRENT_DATE()', result, flags=re.IGNORECASE)

        return result

    def _get_column(self, Model, column_name):
        """
        Get column from model with case-insensitive fallback.

        Callers often pass lowercase column names (e.g., 'last_name')
        but Zen databases typically use PascalCase (e.g., 'Last_Name').
        This method tries exact match first, then case-insensitive.

        Args:
            Model: SQLAlchemy model class
            column_name: Column name to find

        Returns:
            Column attribute from model

        Raises:
            AttributeError: If column not found
        """
        # Try exact match first
        if hasattr(Model, column_name):
            return getattr(Model, column_name)

        # Build case-insensitive lookup map
        column_map = {}
        for col in Model.__table__.columns:
            column_map[col.name.lower()] = col.name

        # Try case-insensitive match
        lower_name = column_name.lower()
        if lower_name in column_map:
            actual_name = column_map[lower_name]
            return getattr(Model, actual_name)

        # Not found - raise with helpful message
        available = list(column_map.values())
        raise AttributeError(
            f"Column '{column_name}' not found in {Model.__tablename__}. "
            f"Available columns: {available}"
        )

    def _parse_column_reference(self, col_name):
        """
        Parse column reference which may include table prefix.
        
        Supports:
        - Simple column: "employee_id"
        - Table-prefixed: "sales.employee_id"
        - Table-prefixed: "employees.first_name"
        
        Args:
            col_name: Column name (optionally with table prefix)
            
        Returns:
            Tuple of (table_name or None, column_name)
        """
        if '.' in col_name:
            parts = col_name.split('.', 1)
            return (parts[0], parts[1])
        return (None, col_name)
    
    def _get_column_from_table(self, Model, col_name):
        """
        Get column from specific model, with case-insensitive fallback.
        
        Similar to _get_column but for use with JOINs where we know the table.
        
        Args:
            Model: SQLAlchemy model class
            col_name: Column name (without table prefix)
            
        Returns:
            Column attribute from model
        """
        # Try exact match first
        if hasattr(Model, col_name):
            return getattr(Model, col_name)
        
        # Build case-insensitive lookup map
        column_map = {}
        for col in Model.__table__.columns:
            column_map[col.name.lower()] = col.name
        
        # Try case-insensitive match
        lower_name = col_name.lower()
        if lower_name in column_map:
            actual_name = column_map[lower_name]
            return getattr(Model, actual_name)
        
        # Not found - raise with helpful message
        available = list(column_map.values())
        raise AttributeError(
            f"Column '{col_name}' not found in {Model.__tablename__}. "
            f"Available columns: {available}"
        )

    def query_builder(self, query_spec):
        """
        Execute abstract query using ORM.

        Args:
            query_spec: Abstract query specification
                {
                    'table': 'table_name',
                    'columns': ['col1', 'col2'],  # Optional column selection
                    'select': [...],  # Alternative: aggregation specs
                    'joins': [  # Optional JOIN clauses
                        {
                            'table': 'other_table',
                            'on': 'table.id = other_table.table_id',
                            'type': 'INNER'  # Optional: INNER (default), LEFT, RIGHT
                        }
                    ],
                    'where': {...},
                    'group_by': ['col1', 'col2'],  # GROUP BY columns
                    'having': {...},  # HAVING clause
                    'order_by': [...],
                    'limit': int,
                    'offset': int
                }

        Returns:
            Query results as list of dictionaries
        """
        session = self.Session()

        try:
            # Check if this is a UNION query
            if 'union' in query_spec:
                return self._execute_union_query(session, query_spec)

            # Check if query has subqueries or EXISTS (requires Core select(), not ORM query())
            if self._has_subquery_or_exists(query_spec.get('where', {})):
                return self._execute_core_select_query(session, query_spec)

            # Get model class for primary table
            primary_table = query_spec['table']
            PrimaryModel = self.get_model_class(primary_table)

            # Check if columns contain aggregate/window/date functions FIRST
            # This must be done before checking for JOINs, because JOIN queries
            # with aggregates need to use the aggregation path, not the join path
            columns = query_spec.get('columns', [])
            converted_select = []
            has_special_in_columns = False

            for col in columns:
                if isinstance(col, str):
                    # Check for aggregate functions (COUNT, SUM, AVG, MIN, MAX)
                    agg = self._parse_aggregate_expression(col)
                    if agg:
                        has_special_in_columns = True
                        converted_select.append(agg)
                    else:
                        # Check for window functions (ROW_NUMBER, RANK, DENSE_RANK, NTILE)
                        window_expr = self._parse_window_function(col)
                        if window_expr is not None:
                            has_special_in_columns = True
                            converted_select.append(window_expr)
                        else:
                            # Check for date functions (YEAR, MONTH, DAY, EXTRACT, DATEPART)
                            date_expr = self._parse_date_expression(col)
                            if date_expr:
                                has_special_in_columns = True
                                converted_select.append(date_expr)
                            else:
                                converted_select.append(col)
                else:
                    converted_select.append(col)

            # If we found special functions in columns, convert to select format
            if has_special_in_columns:
                query_spec = dict(query_spec)  # Copy to avoid modifying original
                query_spec['select'] = converted_select

            # Check if this query has JOINs WITHOUT aggregates
            joins = query_spec.get('joins', [])

            if joins and not has_special_in_columns:
                # Use JOIN query builder for simple JOINs without aggregates
                return self._execute_join_query(session, PrimaryModel, query_spec)

            # Check if this is an aggregation query
            has_aggregation = query_spec.get('group_by') or query_spec.get('select')

            if has_aggregation:
                # Use aggregation builder
                return self._execute_aggregation_query(session, PrimaryModel, query_spec)

            # Build standard query with column selection support
            requested_columns = query_spec.get('columns', [])

            # Filter to only simple column names (no aggregates/functions at this point)
            simple_columns = [c for c in requested_columns if isinstance(c, str) and
                             not self._parse_aggregate_expression(c) and
                             not self._parse_window_function(c) and
                             not self._parse_date_expression(c)]

            if simple_columns:
                # Query specific columns only
                column_objects = [self._get_column(PrimaryModel, col_name) for col_name in simple_columns]
                query = session.query(*column_objects).select_from(PrimaryModel)
                selected_column_names = simple_columns
            else:
                # Query all columns (original behavior)
                query = session.query(PrimaryModel)
                selected_column_names = None  # Flag to use all columns

            # Apply WHERE conditions
            if query_spec.get('where'):
                where_clause = self._build_where_clause(PrimaryModel, query_spec['where'])
                query = query.filter(where_clause)

            # Apply ORDER BY
            if query_spec.get('order_by'):
                for order in query_spec['order_by']:
                    col = self._get_column(PrimaryModel, order['column'])
                    if order.get('direction', 'ASC').upper() == 'DESC':
                        query = query.order_by(col.desc())
                    else:
                        query = query.order_by(col.asc())

            # Apply LIMIT and OFFSET
            if query_spec.get('limit'):
                query = query.limit(query_spec['limit'])
            if query_spec.get('offset'):
                query = query.offset(query_spec['offset'])

            # Execute and convert to dictionaries
            results = []
            for row in query.all():
                row_dict = {}
                if selected_column_names:
                    # Return only requested columns
                    for i, col_name in enumerate(selected_column_names):
                        row_dict[col_name] = row[i]
                else:
                    # Return all columns (original behavior)
                    for col in sqlalchemy_inspect(PrimaryModel).columns:
                        row_dict[col.name] = getattr(row, col.name)
                results.append(row_dict)

            return {
                'results': results,
                'count': len(results),
                'method': 'orm_query'
            }

        except Exception as e:
            # Suggest SQL fallback for complex operations
            error_msg = str(e)

            # Check if error is due to complex query ORM can't handle
            if any(keyword in error_msg.upper() for keyword in ['JOIN', 'SUBQUERY', 'WINDOW', 'NESTED']):
                hint = (
                    f"ORM query failed: {error_msg}\n\n"
                    "This operation may be too complex for ORM (JOINs, subqueries, etc.).\n"
                    "Consider using execute_raw_sql or execute_custom_sql for full SQL control.\n"
                    "Check resource://database/query-patterns for Zen SQL examples."
                )
            else:
                hint = (
                    f"ORM query failed: {error_msg}\n\n"
                    "Try raw SQL for more control:\n"
                    "- execute_raw_sql (SELECT queries)\n"
                    "- execute_custom_sql (all SQL operations)\n"
                    "Or check resource://database/schema to verify column names and types."
                )

            raise RuntimeError(hint) from e

        finally:
            session.close()

    def _execute_join_query(self, session, PrimaryModel, query_spec):
        """
        Execute query with JOIN clauses.
        
        Supports:
        - INNER JOIN (default)
        - LEFT JOIN (LEFT OUTER JOIN)
        - RIGHT JOIN (RIGHT OUTER JOIN)
        - Column selection from multiple tables with table prefixes
        
        Args:
            session: SQLAlchemy session
            PrimaryModel: Primary table model class
            query_spec: Query specification with joins
            
        Returns:
            Query results as list of dictionaries
        """
        from sqlalchemy import and_
        
        # Get all involved tables
        primary_table = query_spec['table']
        joins = query_spec.get('joins', [])
        
        # Build map of table name -> Model class
        table_models = {primary_table: PrimaryModel}
        for join_spec in joins:
            join_table = join_spec['table']
            if join_table not in table_models:
                table_models[join_table] = self.get_model_class(join_table)
        
        # Parse columns to determine which tables they reference
        requested_columns = query_spec.get('columns', [])
        column_objects = []
        column_names = []
        
        for col_spec in requested_columns:
            if isinstance(col_spec, str):
                table_name, col_name = self._parse_column_reference(col_spec)
                
                if table_name:
                    # Column has table prefix: "sales.sale_id"
                    if table_name not in table_models:
                        raise ValueError(f"Table '{table_name}' referenced in column '{col_spec}' is not in query")
                    
                    Model = table_models[table_name]
                    col_obj = self._get_column_from_table(Model, col_name)
                    column_objects.append(col_obj)
                    column_names.append(col_name)  # Use simple name for result dict
                else:
                    # No table prefix - try to find in primary table
                    col_obj = self._get_column_from_table(PrimaryModel, col_name)
                    column_objects.append(col_obj)
                    column_names.append(col_name)
        
        if not column_objects:
            # If no columns specified, select all from primary table
            for col in PrimaryModel.__table__.columns:
                column_objects.append(getattr(PrimaryModel, col.name))
                column_names.append(col.name)
        
        # Build base query with selected columns
        query = session.query(*column_objects)
        
        # Apply JOINs
        for join_spec in joins:
            join_table = join_spec['table']
            join_on = join_spec['on']
            join_type = join_spec.get('type', 'INNER').upper()
            
            JoinModel = table_models[join_table]
            
            # Parse the ON clause: "sales.employee_id = employees.employee_id"
            # This is a simplified parser - handles basic equality joins
            join_condition = self._parse_join_condition(join_on, table_models)
            
            # Apply JOIN based on type
            if join_type == 'LEFT':
                query = query.outerjoin(JoinModel, join_condition)
            elif join_type == 'RIGHT':
                raise ValueError(
                    "RIGHT JOIN is not supported in ORM mode. "
                    "Use execute_query with raw SQL, or rewrite as LEFT JOIN with swapped table order."
                )
            else:  # INNER JOIN (default)
                query = query.join(JoinModel, join_condition)
        
        # Apply WHERE conditions
        if query_spec.get('where'):
            where_clause = self._build_where_clause_with_joins(
                query_spec['where'], table_models, primary_table
            )
            query = query.filter(where_clause)
        
        # Apply ORDER BY
        if query_spec.get('order_by'):
            for order in query_spec['order_by']:
                col_name = order['column']
                table_name, col = self._parse_column_reference(col_name)
                
                if table_name:
                    Model = table_models[table_name]
                    col_obj = self._get_column_from_table(Model, col)
                else:
                    col_obj = self._get_column_from_table(PrimaryModel, col)
                
                if order.get('direction', 'ASC').upper() == 'DESC':
                    query = query.order_by(col_obj.desc())
                else:
                    query = query.order_by(col_obj.asc())
        
        # Apply LIMIT and OFFSET
        if query_spec.get('limit'):
            query = query.limit(query_spec['limit'])
        if query_spec.get('offset'):
            query = query.offset(query_spec['offset'])
        
        # Execute and convert to dictionaries
        results = []
        for row in query.all():
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = row[i]
            results.append(row_dict)
        
        return {
            'results': results,
            'count': len(results),
            'method': 'orm_join_query'
        }
    
    def _parse_join_condition(self, on_clause, table_models):
        """
        Parse JOIN ON condition.
        
        Handles: "sales.employee_id = employees.employee_id"
        
        Args:
            on_clause: ON condition string
            table_models: Dict of table_name -> Model class
            
        Returns:
            SQLAlchemy join condition
        """
        import re
        
        # Simple parser for "table1.col1 = table2.col2"
        pattern = r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)'
        match = re.match(pattern, on_clause.strip())
        
        if not match:
            raise ValueError(f"Cannot parse JOIN condition: {on_clause}")
        
        left_table = match.group(1)
        left_col = match.group(2)
        right_table = match.group(3)
        right_col = match.group(4)
        
        if left_table not in table_models:
            raise ValueError(f"Table '{left_table}' not found in query")
        if right_table not in table_models:
            raise ValueError(f"Table '{right_table}' not found in query")
        
        LeftModel = table_models[left_table]
        RightModel = table_models[right_table]
        
        left_column = self._get_column_from_table(LeftModel, left_col)
        right_column = self._get_column_from_table(RightModel, right_col)
        
        return left_column == right_column
    
    def _build_where_clause_with_joins(self, where_spec, table_models, primary_table):
        """
        Build WHERE clause for JOIN queries.
        
        Similar to _build_where_clause but handles table-prefixed column names.
        
        Args:
            where_spec: WHERE specification
            table_models: Dict of table_name -> Model class
            primary_table: Name of primary table
            
        Returns:
            SQLAlchemy filter condition
        """
        from sqlalchemy import and_, or_
        
        # Handle array of conditions as implicit AND
        if isinstance(where_spec, list):
            if len(where_spec) == 0:
                return None
            if len(where_spec) == 1:
                return self._build_where_clause_with_joins(where_spec[0], table_models, primary_table)
            conditions = [self._build_where_clause_with_joins(cond, table_models, primary_table) for cond in where_spec]
            return and_(*conditions)
        
        if 'and' in where_spec:
            conditions = [self._build_where_clause_with_joins(cond, table_models, primary_table) for cond in where_spec['and']]
            return and_(*conditions)
        
        if 'or' in where_spec:
            conditions = [self._build_where_clause_with_joins(cond, table_models, primary_table) for cond in where_spec['or']]
            return or_(*conditions)
        
        # Simple condition
        field = where_spec['field']
        table_name, col_name = self._parse_column_reference(field)
        
        if table_name:
            Model = table_models[table_name]
        else:
            Model = table_models[primary_table]
        
        column = self._get_column_from_table(Model, col_name)
        operator = where_spec['operator']
        value = where_spec.get('value')
        
        # Normalize value and operator (handles NULL strings, quoted values)
        value, operator = self._normalize_where_value(value, operator)
        
        # Normalize boolean values (Zen uses 1/0 instead of TRUE/FALSE)
        value = self._normalize_boolean_value(value)
        
        if operator == '=':
            return column == value
        elif operator == '>':
            return column > value
        elif operator == '<':
            return column < value
        elif operator == '>=':
            return column >= value
        elif operator == '<=':
            return column <= value
        elif operator == '!=':
            return column != value
        elif operator == 'LIKE':
            return column.like(value)
        elif operator == 'IN':
            return column.in_(value)
        elif operator == 'IS NULL':
            return column.is_(None)
        elif operator == 'IS NOT NULL':
            return column.isnot(None)
        
        return column == value

    def _execute_aggregation_query(self, session, Model, query_spec):
        """
        Execute aggregation query with GROUP BY and aggregate functions.

        Args:
            session: SQLAlchemy session
            Model: Table model class
            query_spec: Query specification with group_by, select, having

        Returns:
            Query results as list of dictionaries
        """
        select_spec = query_spec.get('select', [])
        columns_spec = query_spec.get('columns', [])
        group_by = query_spec.get('group_by', [])
        having = query_spec.get('having')

        # Build table_models map for JOINs (needed for table-qualified columns)
        joins = query_spec.get('joins', [])
        table_models = {query_spec['table']: Model}
        for join_spec in joins:
            join_table = join_spec['table']
            if join_table not in table_models:
                table_models[join_table] = self.get_model_class(join_table)

        # Normalize select_spec: callers sometimes pass dict instead of array
        # e.g., {"select": {"new_column": "DATE_ADD(...) AS alias"}}
        # or {"select": {"expression": "DATEDIFF(...) AS age"}}
        if isinstance(select_spec, dict):
            normalized_select = []
            for key, value in select_spec.items():
                if isinstance(value, str):
                    # Parse "EXPR AS alias" format
                    expr_match = re.match(r'^(.+?)\s+AS\s+(\w+)$', value.strip(), re.IGNORECASE)
                    if expr_match:
                        normalized_select.append({
                            'expression': expr_match.group(1).strip(),
                            'alias': expr_match.group(2).strip()
                        })
                    else:
                        # Use the key as alias if no AS clause
                        normalized_select.append({
                            'expression': value,
                            'alias': key
                        })
                else:
                    normalized_select.append(value)
            select_spec = normalized_select

        # Merge columns and select specs
        # Callers sometimes put regular columns in 'columns' and aggregates in 'select'
        combined_spec = []

        # Add columns first (these are typically the GROUP BY columns)
        for col in columns_spec:
            if isinstance(col, str):
                # Check if it's an aggregate expression in columns array
                agg = self._parse_aggregate_expression(col)
                if agg:
                    combined_spec.append(agg)
                else:
                    # Check for window functions (ROW_NUMBER, RANK, DENSE_RANK, NTILE)
                    window_expr = self._parse_window_function(col)
                    if window_expr is not None:
                        combined_spec.append(window_expr)
                    else:
                        # Check for date functions (YEAR, MONTH, DAY, EXTRACT, DATEPART)
                        date_expr = self._parse_date_expression(col)
                        if date_expr:
                            combined_spec.append(date_expr)
                        else:
                            combined_spec.append(col)
            else:
                combined_spec.append(col)

        # Then add select specs (aggregates)
        for spec in select_spec:
            combined_spec.append(spec)

        # Build SELECT columns with aggregations
        select_columns = []
        column_names = []  # Track names for result dict

        for spec in combined_spec:
            if isinstance(spec, dict) and 'function' in spec:
                # Aggregate function
                func_name = spec['function'].upper()
                expression = spec.get('expression', spec.get('column', '*'))
                alias = spec.get('alias', f"{func_name.lower()}_result")

                # Check if expression is simple column name or complex expression
                if expression == '*':
                    # COUNT(*)
                    if func_name == 'COUNT':
                        agg_col = func.count().label(alias)
                    else:
                        raise ValueError(f"Function {func_name} requires a column name")
                elif re.match(r'^[\w]+$', expression):
                    # Simple column name: SUM(amount)
                    column_obj = self._get_column(Model, expression)

                    if func_name == 'COUNT':
                        agg_col = func.count(column_obj).label(alias)
                    elif func_name == 'SUM':
                        agg_col = func.sum(column_obj).label(alias)
                    elif func_name == 'AVG':
                        agg_col = func.avg(column_obj).label(alias)
                    elif func_name == 'MIN':
                        agg_col = func.min(column_obj).label(alias)
                    elif func_name == 'MAX':
                        agg_col = func.max(column_obj).label(alias)
                    else:
                        raise ValueError(f"Unsupported aggregate function: {func_name}")
                elif re.match(r'^[\w]+\.[\w]+$', expression):
                    # Table-qualified column name: SUM(employees.salary)
                    table_name, col_name = expression.split('.', 1)
                    if table_name not in table_models:
                        raise ValueError(f"Table '{table_name}' referenced in aggregate function is not in query")
                    TableModel = table_models[table_name]
                    column_obj = self._get_column_from_table(TableModel, col_name)

                    if func_name == 'COUNT':
                        agg_col = func.count(column_obj).label(alias)
                    elif func_name == 'SUM':
                        agg_col = func.sum(column_obj).label(alias)
                    elif func_name == 'AVG':
                        agg_col = func.avg(column_obj).label(alias)
                    elif func_name == 'MIN':
                        agg_col = func.min(column_obj).label(alias)
                    elif func_name == 'MAX':
                        agg_col = func.max(column_obj).label(alias)
                    else:
                        raise ValueError(f"Unsupported aggregate function: {func_name}")
                else:
                    # Complex expression: SUM(CAST(amount AS DECIMAL(10,2)))
                    # Use literal_column to wrap the expression, then apply func
                    inner_expr = literal_column(expression)

                    if func_name == 'COUNT':
                        agg_col = func.count(inner_expr).label(alias)
                    elif func_name == 'SUM':
                        agg_col = func.sum(inner_expr).label(alias)
                    elif func_name == 'AVG':
                        agg_col = func.avg(inner_expr).label(alias)
                    elif func_name == 'MIN':
                        agg_col = func.min(inner_expr).label(alias)
                    elif func_name == 'MAX':
                        agg_col = func.max(inner_expr).label(alias)
                    else:
                        raise ValueError(f"Unsupported aggregate function: {func_name}")

                select_columns.append(agg_col)
                column_names.append(alias)

            elif isinstance(spec, dict) and 'column' in spec:
                # Regular column from spec dict
                col_name = spec['column']
                column_obj = self._get_column(Model, col_name)
                select_columns.append(column_obj)
                column_names.append(col_name)

            elif isinstance(spec, dict) and 'expression' in spec:
                # Raw SQL expression (e.g., DATEADD, DATEDIFF)
                expr = spec['expression']
                alias = spec.get('alias', 'expr_result')
                # Normalize expression for Zen dialect
                normalized_expr = self._normalize_zen_expression(expr)
                # Use literal_column for raw SQL expressions (supports .label())
                select_columns.append(literal_column(normalized_expr).label(alias))
                column_names.append(alias)

            elif isinstance(spec, str):
                # Simple column name string or table-qualified
                if '.' in spec:
                    # Table-qualified: departments.department_name
                    table_name, col_name = spec.split('.', 1)
                    if table_name not in table_models:
                        raise ValueError(f"Table '{table_name}' in columns is not in query")
                    TableModel = table_models[table_name]
                    column_obj = self._get_column_from_table(TableModel, col_name)
                    select_columns.append(column_obj)
                    column_names.append(col_name)  # Use simple name for result dict
                else:
                    # Simple column name
                    column_obj = self._get_column(Model, spec)
                    select_columns.append(column_obj)
                    column_names.append(spec)

        # If no select columns specified, use group_by columns
        if not select_columns and not combined_spec and group_by:
            for col_name in group_by:
                if '.' in col_name:
                    # Table-qualified column name
                    table_name, simple_name = col_name.split('.', 1)
                    if table_name not in table_models:
                        raise ValueError(f"Table '{table_name}' in GROUP BY is not in query")
                    TableModel = table_models[table_name]
                    column_obj = self._get_column_from_table(TableModel, simple_name)
                    select_columns.append(column_obj)
                    column_names.append(simple_name)
                else:
                    column_obj = self._get_column(Model, col_name)
                    select_columns.append(column_obj)
                    column_names.append(col_name)

        # Build query with specific columns
        # Use select_from to ensure FROM clause is present even when only expressions are selected
        query = session.query(*select_columns).select_from(Model)

        # Apply JOINs (must be done before WHERE/GROUP BY/HAVING)
        if joins:
            for join_spec in joins:
                join_table = join_spec['table']
                join_on = join_spec['on']
                join_type = join_spec.get('type', 'INNER').upper()

                JoinModel = table_models[join_table]

                # Parse the ON clause
                join_condition = self._parse_join_condition(join_on, table_models)

                # Apply JOIN based on type
                if join_type == 'LEFT':
                    query = query.outerjoin(JoinModel, join_condition)
                elif join_type == 'RIGHT':
                    raise ValueError(
                        "RIGHT JOIN is not supported in ORM mode. "
                        "Use execute_query with raw SQL, or rewrite as LEFT JOIN with swapped table order."
                    )
                else:  # INNER JOIN (default)
                    query = query.join(JoinModel, join_condition)

        # Apply WHERE conditions (before grouping)
        if query_spec.get('where'):
            where_clause = self._build_where_clause(Model, query_spec['where'])
            query = query.filter(where_clause)

        # Apply GROUP BY
        if group_by:
            group_columns = []
            for col in group_by:
                # Handle table-qualified column names: departments.department_name
                if '.' in col:
                    table_name, col_name = col.split('.', 1)
                    if table_name not in table_models:
                        raise ValueError(f"Table '{table_name}' in GROUP BY is not in query")
                    TableModel = table_models[table_name]
                    group_columns.append(self._get_column_from_table(TableModel, col_name))
                else:
                    group_columns.append(self._get_column(Model, col))
            query = query.group_by(*group_columns)

        # Apply HAVING
        if having:
            having_clause = self._build_having_clause(Model, having, select_columns, column_names)
            query = query.having(having_clause)

        # Apply ORDER BY
        if query_spec.get('order_by'):
            for order in query_spec['order_by']:
                col_name = order['column']
                # Check if ordering by an alias
                if col_name in column_names:
                    idx = column_names.index(col_name)
                    col = select_columns[idx]
                else:
                    col = self._get_column(Model, col_name)

                if order.get('direction', 'ASC').upper() == 'DESC':
                    query = query.order_by(col.desc())
                else:
                    query = query.order_by(col.asc())

        # Apply LIMIT and OFFSET
        if query_spec.get('limit'):
            query = query.limit(query_spec['limit'])
        if query_spec.get('offset'):
            query = query.offset(query_spec['offset'])

        # Execute and convert to dictionaries
        results = []
        for row in query.all():
            row_dict = {}
            for i, name in enumerate(column_names):
                row_dict[name] = row[i]
            results.append(row_dict)

        return {
            'results': results,
            'count': len(results),
            'method': 'orm_aggregation'
        }

    def _build_having_clause(self, Model, having_spec, select_columns, column_names):
        """
        Build HAVING clause for aggregation queries.

        Args:
            Model: Table model class
            having_spec: HAVING specification
            select_columns: List of select column objects
            column_names: List of column/alias names

        Returns:
            SQLAlchemy filter condition
        """
        field = having_spec['field']
        operator = having_spec['operator']
        value = having_spec['value']

        # Find the column (could be an alias)
        if field in column_names:
            idx = column_names.index(field)
            column = select_columns[idx]
        else:
            column = self._get_column(Model, field)

        # Build condition
        if operator == '=':
            return column == value
        elif operator == '>':
            return column > value
        elif operator == '<':
            return column < value
        elif operator == '>=':
            return column >= value
        elif operator == '<=':
            return column <= value
        elif operator == '!=':
            return column != value

        return column == value

    def _normalize_boolean_value(self, value):
        """
        Normalize boolean values for Zen database.

        Zen uses 1/0 instead of TRUE/FALSE. Common input patterns:
        - "true"/"false" (strings)
        - true/false (JSON booleans)
        - "TRUE"/"FALSE" (uppercase strings)

        This method converts all these to 1/0.

        Args:
            value: Value to normalize

        Returns:
            Normalized value (1/0 for booleans, original value otherwise)
        """
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, str):
            lower_val = value.lower().strip()
            if lower_val == 'true':
                return 1
            elif lower_val == 'false':
                return 0
        return value

    def _normalize_where_value(self, value, operator):
        """
        Normalize WHERE clause values for Zen compatibility.

        Handles:
        - NULL strings: "NULL", "null", None -> (value=None, operator="IS NULL")
        - Quoted strings: "'1980-01-01'" -> "1980-01-01" (strip outer quotes)
        - Date strings: Convert to proper date format

        Args:
            value: The value from the WHERE spec
            operator: The comparison operator

        Returns:
            Tuple of (normalized_value, normalized_operator)
        """
        # Handle NULL values
        if value is None:
            return None, 'IS NULL'
        if isinstance(value, str):
            stripped = value.strip()
            # Check for NULL string
            if stripped.upper() == 'NULL':
                return None, 'IS NULL'
            # Strip surrounding single or double quotes from values
            # Handle double-quoted dates: "'1980-01-01'" instead of "1980-01-01"
            if len(stripped) >= 2:
                if (stripped.startswith("'") and stripped.endswith("'")) or \
                   (stripped.startswith('"') and stripped.endswith('"')):
                    stripped = stripped[1:-1]
            return stripped, operator
        return value, operator

    def _build_subquery(self, subquery_spec):
        """
        Build a SQLAlchemy subquery from specification.

        Supports:
        - Simple subqueries: SELECT AVG(col) FROM table
        - Subqueries with WHERE: SELECT COUNT(*) FROM table WHERE condition
        - Column references for correlation

        Args:
            subquery_spec: Subquery specification dict
                {
                    'select': ['AVG(salary)'] or ['COUNT(*)'] or ['column_name'],
                    'from': 'table_name',
                    'where': {...}  # Optional WHERE clause
                }

        Returns:
            SQLAlchemy scalar subquery object
        """
        # Get the table model for the subquery
        SubqueryModel = self.get_model_class(subquery_spec['from'])

        # Parse the SELECT columns
        select_expr = subquery_spec['select']
        if isinstance(select_expr, str):
            select_expr = [select_expr]

        # Build select columns
        select_columns = []
        for col_spec in select_expr:
            # Check for aggregate functions
            agg = self._parse_aggregate_expression(col_spec)
            if agg:
                # Build aggregate expression based on function type
                # _parse_aggregate_expression returns: {'function': 'AVG', 'expression': 'column_name', 'alias': '...'}
                func_name = agg['function']
                expr = agg['expression']

                if func_name == 'COUNT' and expr == '*':
                    select_columns.append(func.count())
                elif func_name == 'AVG':
                    select_columns.append(func.avg(self._get_column(SubqueryModel, expr)))
                elif func_name == 'SUM':
                    select_columns.append(func.sum(self._get_column(SubqueryModel, expr)))
                elif func_name == 'MIN':
                    select_columns.append(func.min(self._get_column(SubqueryModel, expr)))
                elif func_name == 'MAX':
                    select_columns.append(func.max(self._get_column(SubqueryModel, expr)))
                else:
                    # Unsupported aggregate function, fall back to column reference
                    select_columns.append(self._get_column(SubqueryModel, expr))
            else:
                # Simple column reference
                select_columns.append(self._get_column(SubqueryModel, col_spec))

        # Build the subquery
        subquery = select(*select_columns).select_from(SubqueryModel)

        # Add WHERE clause if specified
        if 'where' in subquery_spec:
            where_condition = self._build_where_clause(SubqueryModel, subquery_spec['where'])
            if where_condition is not None:
                subquery = subquery.where(where_condition)

        # Return as scalar subquery
        return subquery.scalar_subquery()

    def _execute_union_query(self, session, query_spec):
        """
        Execute UNION query combining multiple SELECT queries.

        Supports:
        - Simple UNION: Combines results from multiple tables/queries
        - UNION with column selection from each query
        - WHERE/ORDER BY/LIMIT on individual queries

        Args:
            session: SQLAlchemy session
            query_spec: Query specification with UNION
                {
                    'table': 'employees',
                    'columns': ['first_name'],
                    'where': {...},  # Optional WHERE for primary query
                    'union': [
                        {
                            'table': 'departments',
                            'columns': ['department_name'],
                            'where': {...}  # Optional WHERE for union query
                        }
                    ]
                }

        Returns:
            Query results as list of dictionaries
        """
        from sqlalchemy import union

        # Build primary query
        primary_query = self._build_select_for_union(query_spec)

        # Build union queries
        union_queries = [primary_query]
        for union_spec in query_spec['union']:
            union_query = self._build_select_for_union(union_spec)
            union_queries.append(union_query)

        # Combine with UNION
        combined = union(*union_queries)

        # Apply ORDER BY if specified on the main query_spec (applies to final result)
        if query_spec.get('order_by'):
            for order in query_spec['order_by']:
                # For UNION queries, order by column index (0-based) or label
                col_name = order['column']
                # Use literal_column for ordering by column name/label
                from sqlalchemy import literal_column
                col = literal_column(col_name)
                if order.get('direction', 'ASC').upper() == 'DESC':
                    combined = combined.order_by(col.desc())
                else:
                    combined = combined.order_by(col.asc())

        # Apply LIMIT/OFFSET on final result
        if query_spec.get('limit'):
            combined = combined.limit(query_spec['limit'])
        if query_spec.get('offset'):
            combined = combined.offset(query_spec['offset'])

        # Execute and convert to dictionaries
        results = []
        result_rows = session.execute(combined).fetchall()

        # Get column names from the first query's columns spec
        column_names = query_spec.get('columns', [])
        if not column_names:
            # If no columns specified, we need to inspect the result
            # This is a fallback - ideally columns should always be specified
            if result_rows:
                column_names = [f'col_{i}' for i in range(len(result_rows[0]))]

        for row in result_rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                row_dict[col_name] = row[i]
            results.append(row_dict)

        return {
            'results': results,
            'count': len(results),
            'method': 'orm_union_query'
        }

    def _build_select_for_union(self, query_spec):
        """
        Build a single SELECT statement for use in UNION.

        Args:
            query_spec: Query specification for one query in the UNION
                {
                    'table': 'table_name',
                    'columns': ['col1', 'col2'],  # Required for UNION
                    'where': {...}  # Optional
                }

        Returns:
            SQLAlchemy select() construct
        """
        # Get model class
        Model = self.get_model_class(query_spec['table'])

        # Get columns (required for UNION - all queries must have same number of columns)
        columns = query_spec.get('columns', [])
        if not columns:
            raise ValueError(f"UNION queries must specify 'columns' list for table '{query_spec['table']}'")

        # Build select columns with labels
        select_columns = []
        for col_name in columns:
            col = self._get_column(Model, col_name)
            # Label each column to ensure consistent naming across UNION queries
            select_columns.append(col.label(col_name))

        # Build the select statement
        stmt = select(*select_columns).select_from(Model)

        # Add WHERE clause if specified
        if 'where' in query_spec:
            where_condition = self._build_where_clause(Model, query_spec['where'])
            if where_condition is not None:
                stmt = stmt.where(where_condition)

        return stmt

    def _has_subquery_or_exists(self, where_spec):
        """
        Recursively check if WHERE specification contains subqueries or EXISTS clauses.

        Returns True if subqueries/EXISTS found, False otherwise.
        """
        if not where_spec:
            return False

        # Handle list of conditions (implicit AND)
        if isinstance(where_spec, list):
            return any(self._has_subquery_or_exists(cond) for cond in where_spec)

        if not isinstance(where_spec, dict):
            return False

        # Check for EXISTS/NOT EXISTS
        if 'exists' in where_spec or 'not_exists' in where_spec:
            return True

        # Check for subquery in value
        if 'value' in where_spec:
            value = where_spec['value']
            if isinstance(value, dict) and 'subquery' in value:
                return True

        # Recursively check AND/OR conditions
        if 'and' in where_spec:
            return any(self._has_subquery_or_exists(cond) for cond in where_spec['and'])

        if 'or' in where_spec:
            return any(self._has_subquery_or_exists(cond) for cond in where_spec['or'])

        # Check array of conditions (implicit AND)
        if isinstance(where_spec, list):
            return any(self._has_subquery_or_exists(cond) for cond in where_spec)

        return False

    def _execute_core_select_query(self, session, query_spec):
        """
        Execute query using Core select() instead of ORM query().

        Required when WHERE clause contains subqueries or EXISTS, because
        ORM query() doesn't properly handle scalar_subquery() objects.

        Args:
            session: SQLAlchemy session
            query_spec: Query specification

        Returns:
            Query results as list of dictionaries
        """
        # Get model class
        Model = self.get_model_class(query_spec['table'])

        # Build select columns
        columns = query_spec.get('columns', [])
        if columns:
            select_columns = [self._get_column(Model, col) for col in columns]
        else:
            # Select all columns
            from sqlalchemy import inspect as sqlalchemy_inspect
            select_columns = [col for col in sqlalchemy_inspect(Model).columns]
            columns = [col.name for col in select_columns]

        # Build Core select statement
        stmt = select(*select_columns).select_from(Model)

        # Add WHERE clause
        if query_spec.get('where'):
            where_condition = self._build_where_clause(Model, query_spec['where'])
            if where_condition is not None:
                stmt = stmt.where(where_condition)

        # Add ORDER BY
        if query_spec.get('order_by'):
            for order in query_spec['order_by']:
                col = self._get_column(Model, order['column'])
                if order.get('direction', 'ASC').upper() == 'DESC':
                    stmt = stmt.order_by(col.desc())
                else:
                    stmt = stmt.order_by(col.asc())

        # Add LIMIT/OFFSET
        if query_spec.get('limit'):
            stmt = stmt.limit(query_spec['limit'])
        if query_spec.get('offset'):
            stmt = stmt.offset(query_spec['offset'])

        # Execute and convert to dictionaries
        result_rows = session.execute(stmt).fetchall()

        results = []
        for row in result_rows:
            row_dict = {}
            for i, col_name in enumerate(columns):
                row_dict[col_name] = row[i]
            results.append(row_dict)

        return {
            'results': results,
            'count': len(results),
            'method': 'orm_core_select'
        }

    def _build_where_clause(self, Model, where_spec):
        """
        Build WHERE clause from specification.

        Supports:
        - Simple conditions: {"field": "salary", "operator": ">", "value": 50000}
        - AND/OR logic: {"and": [...]} or {"or": [...]}
        - Subqueries in value: {"field": "salary", "operator": ">", "value": {"subquery": {...}}}
        - EXISTS clauses: {"exists": {"select": [...], "from": "table", "where": {...}}}
        - NOT EXISTS: {"not_exists": {...}}
        """
        # Handle array of conditions as implicit AND
        # Handle array-style where: [{...}, {...}] instead of {"and": [...]}
        if isinstance(where_spec, list):
            if len(where_spec) == 0:
                return None
            if len(where_spec) == 1:
                return self._build_where_clause(Model, where_spec[0])
            conditions = [self._build_where_clause(Model, cond) for cond in where_spec]
            return and_(*conditions)

        if 'and' in where_spec:
            conditions = [self._build_where_clause(Model, cond) for cond in where_spec['and']]
            return and_(*conditions)

        if 'or' in where_spec:
            conditions = [self._build_where_clause(Model, cond) for cond in where_spec['or']]
            return or_(*conditions)

        # Handle EXISTS clause
        if 'exists' in where_spec:
            exists_spec = where_spec['exists']
            # Build the subquery for EXISTS
            ExistsModel = self.get_model_class(exists_spec['from'])

            # Parse SELECT (usually just literal 1 for EXISTS)
            select_expr = exists_spec.get('select', [1])
            if isinstance(select_expr, list) and len(select_expr) > 0:
                if select_expr[0] == 1:
                    # EXISTS (SELECT 1 FROM ...)
                    subquery = select(literal_column('1')).select_from(ExistsModel)
                else:
                    # EXISTS (SELECT column FROM ...)
                    select_columns = [self._get_column(ExistsModel, col) for col in select_expr]
                    subquery = select(*select_columns).select_from(ExistsModel)
            else:
                subquery = select(literal_column('1')).select_from(ExistsModel)

            # Add WHERE clause if specified (typically for correlation)
            if 'where' in exists_spec:
                where_condition = self._build_where_clause(ExistsModel, exists_spec['where'])
                if where_condition is not None:
                    subquery = subquery.where(where_condition)

            return exists(subquery)

        # Handle NOT EXISTS clause
        if 'not_exists' in where_spec:
            not_exists_spec = where_spec['not_exists']
            # Build the subquery for NOT EXISTS (same as EXISTS but negated)
            ExistsModel = self.get_model_class(not_exists_spec['from'])

            select_expr = not_exists_spec.get('select', [1])
            if isinstance(select_expr, list) and len(select_expr) > 0:
                if select_expr[0] == 1:
                    subquery = select(literal_column('1')).select_from(ExistsModel)
                else:
                    select_columns = [self._get_column(ExistsModel, col) for col in select_expr]
                    subquery = select(*select_columns).select_from(ExistsModel)
            else:
                subquery = select(literal_column('1')).select_from(ExistsModel)

            if 'where' in not_exists_spec:
                where_condition = self._build_where_clause(ExistsModel, not_exists_spec['where'])
                if where_condition is not None:
                    subquery = subquery.where(where_condition)

            return ~exists(subquery)

        # Simple condition
        column = self._get_column(Model, where_spec['field'])
        operator = where_spec['operator']
        value = where_spec.get('value')

        # Check if value is a subquery specification
        if isinstance(value, dict) and 'subquery' in value:
            # Build subquery and use it as the value
            value = self._build_subquery(value['subquery'])
        else:
            # Normalize value and operator (handles NULL strings, quoted values)
            value, operator = self._normalize_where_value(value, operator)

            # Normalize boolean values (Zen uses 1/0 instead of TRUE/FALSE)
            value = self._normalize_boolean_value(value)

        if operator == '=':
            return column == value
        elif operator == '>':
            return column > value
        elif operator == '<':
            return column < value
        elif operator == '>=':
            return column >= value
        elif operator == '<=':
            return column <= value
        elif operator == '!=':
            return column != value
        elif operator == 'LIKE':
            return column.like(value)
        elif operator == 'IN':
            return column.in_(value)
        elif operator == 'IS NULL':
            return column.is_(None)
        elif operator == 'IS NOT NULL':
            return column.isnot(None)

        return column == value

    def create_entity(self, table_name, data):
        """
        Create a new entity (row) using ORM.

        Args:
            table_name: Table name
            data: Dictionary of column:value pairs

        Returns:
            Created entity as dictionary
        """
        session = self.Session()

        try:
            Model = self.get_model_class(table_name)

            # CRITICAL FIX: Check if primary key columns have IDENTITY/autoincrement
            # before allowing creation without explicit values
            mapper = sqlalchemy_inspect(Model)
            for pk_col in mapper.primary_key:
                col_name = pk_col.name

                # If primary key is missing from data AND column doesn't have autoincrement
                if col_name not in data and not pk_col.autoincrement:
                    return {
                        'created': False,
                        'error': f'Primary key column "{col_name}" is required but not provided. '
                                f'This column does NOT have IDENTITY/autoincrement property.\n\n'
                                f'Options:\n'
                                f'1. Provide "{col_name}" value in data dict\n'
                                f'2. Alter table to use IDENTITY type (e.g., ALTER TABLE {table_name} ...)\n'
                                f'3. Use execute_custom_sql for explicit INSERT with all columns'
                    }

            entity = Model(**data)
            session.add(entity)
            session.commit()

            # Return created entity
            result = {}
            for col in sqlalchemy_inspect(Model).columns:
                result[col.name] = getattr(entity, col.name)

            return {
                'created': True,
                'entity': result
            }

        except Exception as e:
            session.rollback()
            # Suggest SQL fallback with helpful context
            error_msg = str(e)
            hint = (
                f"ORM create failed: {error_msg}\n\n"
                "If you need more control over the INSERT operation, consider:\n"
                "1. execute_custom_sql - For explicit INSERT with all columns specified\n"
                "2. insert_data - For batch inserts (faster for multiple rows)\n"
                "3. Check resource://database/schema to verify column names and types"
            )
            return {
                'created': False,
                'error': hint
            }

        finally:
            session.close()

    def update_entity(self, table_name, entity_id, data):
        """
        Update an entity using ORM.

        Args:
            table_name: Table name
            entity_id: Primary key value
            data: Dictionary of column:value pairs to update

        Returns:
            Updated entity as dictionary
        """
        session = self.Session()

        try:
            Model = self.get_model_class(table_name)
            entity = session.query(Model).get(entity_id)

            if not entity:
                return {
                    'updated': False,
                    'error': 'Entity not found'
                }

            # Update attributes
            for key, value in data.items():
                setattr(entity, key, value)

            session.commit()

            # Return updated entity
            result = {}
            for col in sqlalchemy_inspect(Model).columns:
                result[col.name] = getattr(entity, col.name)

            return {
                'updated': True,
                'entity': result
            }

        except Exception as e:
            session.rollback()
            # Suggest SQL fallback with helpful context
            error_msg = str(e)
            hint = (
                f"ORM update failed: {error_msg}\n\n"
                "If you need more control over the UPDATE operation, consider:\n"
                "1. execute_custom_sql - For explicit UPDATE with complex WHERE clauses\n"
                "2. update_data - For batch updates with raw SQL\n"
                "3. Check resource://database/schema to verify column names and types"
            )
            return {
                'updated': False,
                'error': hint
            }

        finally:
            session.close()

    def delete_entity(self, table_name, entity_id):
        """
        Delete an entity using ORM.

        Args:
            table_name: Table name
            entity_id: Primary key value

        Returns:
            Result dictionary
        """
        session = self.Session()

        try:
            Model = self.get_model_class(table_name)
            entity = session.query(Model).get(entity_id)

            if not entity:
                return {
                    'deleted': False,
                    'error': 'Entity not found'
                }

            session.delete(entity)
            session.commit()

            return {
                'deleted': True,
                'entity_id': entity_id
            }

        except Exception as e:
            session.rollback()
            # Suggest SQL fallback with helpful context
            error_msg = str(e)
            hint = (
                f"ORM delete failed: {error_msg}\n\n"
                "If you need more control over the DELETE operation, consider:\n"
                "1. execute_custom_sql - For explicit DELETE with complex WHERE clauses\n"
                "2. delete_data - For batch deletes with raw SQL\n"
                "3. Check resource://database/schema to verify table structure"
            )
            return {
                'deleted': False,
                'error': hint
            }

        finally:
            session.close()

    def clear_model_cache(self):
        """Clear the model cache (useful after schema changes)"""
        self._model_cache.clear()

    def close(self):
        """Close engine connections and clear cache"""
        self._model_cache.clear()
        self.engine.dispose()
