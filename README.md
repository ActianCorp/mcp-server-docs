# Actian MCP Server
## Quick start
```
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone https://alm.actian.com/bitbucket/scm/~alokaj/actian_mcp_server.git
cd actian_mcp_server
uv sync
```
### Start the MCP server only
#### Configuration 
A configuration file is used to establish the connection to the database and start the server. The template of this file can be seen at [src/conf_temp.json](src/conf_temp.json). 
```
export DATABASE_USER=<your_database_username>
export DATABASE_PASSWORD=<your_database_password>

uv run actian-mcp-server --dbms=<dbms_name> --conf-file=<db_specific_conf_file> [ --transport=<transport_mode> ]
```

### Instructions on supporting a new database
#### Create a new file subtree
```
mkdir src/<dbms>

# MCP Server feature subtree
mkdir src/<dbms>/features
touch src/<dbms>/features/tools.py
touch src/<dbms>/features/resources.py
touch src/<dbms>/features/prompts.py

# MCP Server docker subtree
mkdir src/<dbms>/docker
touch src/<dbms>/features/Dockerfile-<dbms>
touch src/<dbms>/features/entrypoint.sh
touch src/<dbms>/features/docker-compose.yml
```

#### Implement the tools, resources and prompts
Create child classes for tools (resources) in their file that inherit from their respective interfaces MCPTools (MCPResources) and implement all the required methods declared in their interface at [src/actian_mcp_server/server_interfaces.py](). \
Add functions for instantiating the classes and registering the server components.
```
# tools.py example

class <DBMS>Tools(MCPTools):
    async def <func_name_1>(arg1, ...):
        <your implementation here>
        ...

    async def <func_name_1>(arg1, ...):
    ...

def initialize_<dbms>_tools(server, connection):
    tools = <DBMS>Tools(connection)

    server.tool(name="tool_name_1")(tools.func_name_1)
    server.tool(name="tool_name_2")(tools.func_name_2)
    ...
```
These functions are called accordingly in the lifespan object of the server together with additional minor adjustments at [src/actian_mcp_server/server.py]().

#### Adapt the configuration file
```
cp src/conf_temp.json src/<dbms>/conf.json
# adjust the configuration parameters in conf.json
```

### Testing with Vector
Apply the steps under [Adapt the configuration file](#adapt-the-configuration-file) first.
> NOTE: requires a Vector instance installation and ODBC setup.


```
export DATABASE_USER=<your_database_username>
export DATABASE_PASSWORD=<your_database_password>

cd src/vector/tests
bash test_db_init.sh
uv run pytest
```

### Docker deployment
Apply the steps under [Adapt the configuration file](#adapt-the-configuration-file) first.
> NOTE: requires a DBMS instance installation and ODBC setup.

#### Step 1: Setup the environment
```
source set_env.sh
```
#### Step 2: Build the container image
```
bash make-docker-<dbms>.sh
```
#### Step 3: Start the container
```
docker compose -f src/<dbms>/docker/docker-compose.yml up -d
```
#### Step 4: Check the container status
```
docker compose ps
docker logs actian-mcp-server
```
