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
uv run src/actian_mcp_server/server.py --dbms=<dbms_name>
```

### Testing with Vector
> NOTE: requires a Vector instance installation.
```
cd src/vector/tests
bash test_db_init.sh
uv run pytest
```
