# Zen MCP Server Implementation

**DBMS:** Actian Zen (formerly Pervasive PSQL, Btrieve)
**Engine:** Btrieve/MicroKernel Database Engine (MKDE)
**Implementation Status:** Basic connectivity (execute_query + schema retrieval)

## Overview

This is a minimal Zen MCP server implementation that provides:
- **1 Tool:** `execute_query` - Execute SQL queries against Zen database
- **1 Resource:** `resource://database/schema` - Get database schema
- **1 Prompt:** `ask_question` - Ask questions about Zen database

## Configuration

### Option 1: DSN Connection (Recommended)

Create `conf.json`:
```json
{
    "conn_string": "DSN=demodata"
}
```

This uses an ODBC Data Source Name (DSN) configured in Windows ODBC Data Source Administrator.

### Option 2: Full Connection String

```json
{
    "conn_string": "DRIVER={Pervasive ODBC Interface};SERVERNAME=localhost;DBQ=DEMODATA;Uid=zenuser;Pwd=zenpw"
}
```

### Connection String Components

- `DRIVER`: ODBC driver name (usually "Pervasive ODBC Interface" or "Actian Zen ODBC")
- `SERVERNAME`: Server hostname/IP (use "localhost" for local)
- `DBQ`: Database name (e.g., "DEMODATA")
- `Uid`: Username (optional)
- `Pwd`: Password (optional)
- `TCPPort`: TCP port (default 1583, optional)

## Running the Server

```bash
# Using DSN
uv run actian-mcp-server --dbms=zen --conf-file=src/zen/conf.json

# Using custom config
uv run actian-mcp-server --dbms=zen --conf-file=path/to/your/conf.json
```

## Zen SQL Differences from Vector

### System Catalogs

┌────────────────────────────────────────────────────────────┐
│  Vector (Ingres)      │  Zen (Btrieve)                    │
├───────────────────────┼───────────────────────────────────┤
│ iitables              │ X$File                            │
│ iicolumns             │ X$Field                           │
│ iiindexes             │ X$Index                           │
│                       │                                   │
│ system_use='U'        │ Xf$Name NOT LIKE 'X$%'            │
│ trim() required       │ No trim() needed                  │
└────────────────────────────────────────────────────────────┘

### Data Types

Zen uses Btrieve data type codes (0-22):
- 0: STRING/VARCHAR
- 1: INTEGER
- 3: DATE
- 4: TIME
- 6: MONEY
- 7: BIT/LOGICAL
- 15: AUTOINC
- 20: TIMESTAMP
- 22: IDENTITY

See `resources.py:_map_zen_datatype()` for full mapping.

### Key Differences

**Zen:**
- Btrieve engine (record-level locking)
- X$ system tables
- Data type codes instead of type names
- No CHAR padding issues
- Supports ANSI SQL with Zen extensions

**Vector:**
- Columnar RDBMS (Ingres-based)
- ii* system tables
- Requires trim() for CHAR fields
- SIMD vectorization
- ANSI SQL:2003 compliant

## Testing with Zen

Prerequisites:
1. Actian Zen installed
2. ODBC DSN configured (or use full connection string)
3. Test database accessible (e.g., DEMODATA)

Create test database:
```bash
# If using Zen utilities
createdb testdb
# Configure DSN pointing to testdb
```

Test connection:
```bash
uv run actian-mcp-server --dbms=zen --conf-file=src/zen/conf.json
```

## Implementation Notes

### Based on DB_MCP_PILOT Reference

This implementation uses patterns from `d:\ZenMCP\DB_MCP_PILOT\` including:
- ODBC connection via pyodbc
- DSN-based or full connection string support
- X$ system table queries for schema
- Btrieve data type mapping

### Minimal by Design

Unlike the full DB_MCP_PILOT implementation which includes:
- SQLAlchemy ORM integration
- DDL operations (procedures, triggers, functions)
- Transaction management
- File upload/download (BLOB support)
- 32+ tools and complex features

This Zen implementation provides only:
- Basic SQL query execution
- Schema retrieval
- Simple prompt

This matches the actian_mcp_server pattern: minimal proof-of-concept for database connectivity.

## Future Enhancements

To match Vector implementation, could add:
- Parameterized queries (SQL injection protection)
- Transaction support (BEGIN/COMMIT/ROLLBACK)
- More detailed schema info (indexes, constraints)
- Data type validation
- Query timeouts
- Result pagination

To match DB_MCP_PILOT functionality, could integrate:
- SQLAlchemy Zen dialect
- ORM operations
- DDL tools (procedures, triggers, UDFs)
- BLOB file management
- Advanced type mapping (45+ Zen types)

## Connection String Examples

### Local DEMODATA
```json
{"conn_string": "DSN=demodata"}
```

### Remote Server
```json
{
    "conn_string": "DRIVER={Pervasive ODBC Interface};SERVERNAME=192.168.1.100;DBQ=PRODDB;Uid=admin;Pwd=secret"
}
```

### With TCP Port
```json
{
    "conn_string": "DRIVER={Actian Zen ODBC};SERVERNAME=zenserver;DBQ=APPDB;TCPPort=1583;Uid=user;Pwd=pass"
}
```

## Troubleshooting

### Connection Errors

**Error:** "Data source name not found"
- **Solution:** Create DSN in Windows ODBC Data Source Administrator (64-bit)

**Error:** "Cannot connect to server"
- **Solution:** Check SERVERNAME and TCPPort, ensure Zen server is running

**Error:** "Login failed"
- **Solution:** Verify Uid/Pwd credentials, check Zen user permissions

### Schema Query Errors

**Error:** "X$File not found"
- **Solution:** Ensure connected to actual Zen database (not Vector or other DBMS)
- **Note:** X$ tables are Zen system catalogs

**Error:** "Invalid object name"
- **Solution:** Check database name in connection string (DBQ parameter)

## References

- Zen System Tables: X$File, X$Field, X$Index
- DB_MCP_PILOT: `d:\ZenMCP\DB_MCP_PILOT\zen_sqlalchemy_mcp_server.py`
- Actian Zen Documentation: https://docs.actian.com/psql/
