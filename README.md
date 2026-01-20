# Actian MCP Server
## Quick start
```
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://alm.actian.com/bitbucket/scm/~alokaj/actian_mcp_server.git
cd actian_mcp_server
uv sync
```
### Start the MCP server only
```
uv run actian-mcp-server --dbms=<dbms_name> --conf_file=<db_specific_conf_file>
```

### Testing with Vector
> NOTE: requires a Vector instance installation and ODBC setup.
```
cd src/vector/tests
bash test_db_init.sh
uv run pytest
```
