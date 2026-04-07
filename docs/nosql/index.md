---
title: Actian NoSQL Database
description: Use the Actian MCP Server to connect MCP clients to Actian NoSQL Databases.
---

# Actian NoSQL Database

This page explains how to use the **Actian MCP Server** with **Actian NoSQL Database**.

<!-- TODO: Describe what the NoSQL plugin does and what AI clients can do with it. -->

## What you can do

With the NoSQL server, AI clients can:

- Discover the Schema of an Actian NoSQL Database
	- List classes
	- Explore details of persistent classes
- Run queries on database objects
	- Use Filter, Projections, Navigation
	- Implements optimized load for direct References
- Read Objects by ID
	- Including optimizations for collections of Object IDs

## Configuration

There are basically just two settings you need to define in order to
configure the NSQL MCP Server.

1. The port which you want to use to connect to the MCP Server
2. The database url you want to explore with the MCP Server<br>
	The database url looks like `database@server:port#user:password`.<br>
	`port`, `user` and `password` are optional.


<!-- TODO: Describe the configuration file format and required fields for NoSQL. Example:

```json
{
  "plugins": [
    "actian_mcp_server.nosql.plugin.NoSQLPlugin"
  ],
  "nosql": {
    "host": "localhost",
    "port": 27017,
    "database": "mydb",
    "username": "admin",
    "password": "secret"
  }
}
```
-->

## Quick start

In order to start the MCP Server, you just need to run the docker image by providing the parameters specified above.

`docker run --name NSQL-MCP -e NSQL_CONNECTIONURL=cars@localhost -p 8080:8080 actian/nsql-mcp-server`

## Authentication Methods

### Method 1: Bearer Token (API/CLI)

For programmatic access (CLI tools, scripts, AI agents), use a Bearer token.
application-type: service

**How to get a token:**

1. **Using Auth0 Client Credentials** (M2M):
   ```bash
   curl --request POST \
     --url https://dev-6t410orjb0bb8cis.us.auth0.com/oauth/token \
     --header 'content-type: application/json' \
     --data '{
       "client_id": <your_client_id>,
       "client_secret": "<your-secret>",
       "audience": "http://localhost:8090/",
       "grant_type": "client_credentials"
     }'
   ```

 **Response:**
   ```json
   {
     "access_token": "eyJhbGc...",
     "token_type": "Bearer",
     "expires_in": 86400
   }
   ```
During development, the token can be easily generated for testing purpose using auth0 CLI 
```auth0 test token -a http://localhost:8090/ -s openid
```

**How to use the token:**
The MCP server normally expects the token to be provided in the Authorization header using the Bearer scheme. However, some MCP clients—such as Copilot—do not send an Authorization header. 
In these cases, the token is instead included as a query parameter.

To support both approaches, the server includes a pre‑authentication filter that intercepts incoming requests. If a token is found in the query parameters, the filter extracts it and inserts 
it into the Authorization header before the authentication process runs. The token is preserved both in the header and in the query parameter, ensuring compatibility with clients that send the token in either location. 
Add the following to your MCP configuration (`mcp.json` or similar):
```json
{
  "servers": {
    "nsql-mcp-server": {
      "type": "http",
      "url": "http://localhost:8090/mcp?token=<your_access_token>",
	  "headers": {
        "Authorization": "Bearer <your_access_token>"
      }
   }
  }
}
```

**This is How It Works**
```
┌──────────────┐                                        ┌────────────┐
│  AI Client   │  ① Get token (client_credentials)  ──► │   Auth0    │
│              │  ◄── ② access_token (JWT)              └────────────┘
│              │
│              │  ③ Tool call + Authorization: Bearer <token>
│              │  ─────────────────────────────────────► ┌──────────────┐
│              │  ◄── ④ Tool result                      │  MCP Server  │
└──────────────┘                                         │  (Quarkus)   │
                                                         └──────────────┘
```

- **Quarkus does all the work on the server-side**: validates the token, extracts identity, enforces `@Authenticated`.
- **The client's only job**: include `Authorization: Bearer <token>` or `?token=<token>` in requests.
---

### Method 2: Session-Based (Browser)

When accessing MCP endpoints from a browser or web application, authentication happens automatically via OAuth 2.0 session cookies.
application-type: web-app

**Flow:**
1. User visits protected endpoint
2. Redirects to Auth0 login
3. After login, session cookie is set
4. Subsequent requests use the session cookie

Quarkus handles this automatically.

## Authentication Configuration

Authentication can be enabled or disabled for MCP tools via configuration. This is useful for:
- **Development**: Disable auth for easier local testing
- **Production**: Enable auth for security

**Configuration Property:**
```properties
# Enable/disable MCP tool authentication
mcp.security.authentication.enabled=true   # Production (default)
mcp.security.authentication.enabled=false  # Development/testing
```

**Environment Variable:**
```bash
export MCP_SECURITY_AUTHENTICATION_ENABLED=false  # Disable auth
export MCP_SECURITY_AUTHENTICATION_ENABLED=true   # Enable auth (default)
```

**By Profile:**
```properties
# Default: authentication required
mcp.security.authentication.enabled=true

# Development: authentication disabled for easier testing
%dev.mcp.security.authentication.enabled=false

# Production: authentication required
%prod.mcp.security.authentication.enabled=true
```

**Usage:**
- When **enabled** (default): All MCP tools annotated with @McpAuthenticated require authentication (session or bearer token)
- When **disabled**: MCP tools are publicly accessible (no authentication needed) whether annotated with McpAuthenticated or not

**Example - Disable for Development:**
```bash
# In application.properties
%dev.mcp.security.authentication.enabled=false

# Or via environment variable
export MCP_SECURITY_AUTHENTICATION_ENABLED=false

# Or via command line
mvn quarkus:dev -Dmcp.security.authentication.enabled=false
```
** All other configurations that are needed for the application types "web-application" and "service" (M2M) are in the application.properties file. 
