---
title: Auth0 Setup Guide
description: Step-by-step guide to configure Auth0 as the OAuth identity provider for the Actian MCP Server.
---

# Auth0 Setup Guide

This section describes how to create and configure an Auth0 **Application** and **API** for OAuth 2.0 / OIDC authentication with the Actian MCP Server.

By the end, you will have all the values needed to populate the `oauth` block in your `conf.json`. For the full configuration reference and shared concepts, such as TLS, user impersonation, and security practices, see the [Authentication overview](../index.md).

!!! info "Reference"
    [FastMCP Auth0 Integration](https://gofastmcp.com/integrations/auth0)


## Quick-Start Checklist

For experienced Auth0 users, the full walkthrough follows below.

1. **Create an API** (Applications → APIs → + Create API). The **Identifier** becomes `FASTMCP_SERVER_AUTH_AUDIENCE`.
2. **Create an Application** (Applications → Applications → + Create Application → **Machine to Machine**). Authorize it for the API when prompted. Copy the **Client ID** and **Client Secret**.
3. **Authorize the Application for the API** — ensure both **User Access** and **Client Access** show AUTHORIZED (APIs → your API → Application Access → Edit).

    !!! warning
        Skipping this step causes Auth0 to reject token requests with `invalid_request`.
4. **Enable Authorization Code grant** (Application → Settings → Advanced Settings → Grant Types → check **Authorization Code**).
5. **Configure Callback URLs** (Application → Settings → Allowed Callback URLs → `<BASE_URL>/auth/callback`).
6. **Fill `conf.json`** with the values from steps 1–2 plus your Auth0 domain.
7. **Start the server** with `--transport sse` (or `http` / `streamable-http`).


## Prerequisites

- An Auth0 account ([sign up free](https://auth0.com/signup)).
- An Auth0 **Tenant** (created automatically on signup, for example, `dev-abc123`).
- The Actian MCP Server installed and ready to run.


## Part 1: Create an Auth0 API

The **API** represents the Actian MCP Server as a protected resource in Auth0. Tokens issued by Auth0 include the API's identifier as the `audience` claim.

### Steps

1. Log in to the [Auth0 Dashboard](https://manage.auth0.com/).
2. In the left sidebar, navigate to **Applications → APIs**.
1. Select **+ Create API**.
4. Fill in the form:

     | Field | Value | Notes |
     |-------|-------|-------|
     | **Name** | `Actian MCP Server` | Display name (any descriptive string). |
     | **Identifier (Audience)** | `https://<mcp-server-host>:8000/mcp` | This becomes your `FASTMCP_SERVER_AUTH_AUDIENCE`. This is a logical identifier — it doesn't need to be a reachable URL. |
     | **Signing Algorithm** | `RS256` | Default; leave as-is |

5. Select **Create**.

### What You Get from This Step

| Config Field | Where to find it |
|---|---|
| `FASTMCP_SERVER_AUTH_AUDIENCE` | The **Identifier** you entered (for example, `https://<mcp-server-host>:8000/mcp`). |


## Part 2: Create an Auth0 Application

The **Application** represents the MCP server's OAuth client. It holds the `client_id` and `client_secret` used during the OAuth handshake.

!!! note "Why Machine to Machine?"
    The MCP server's OAuth proxy (OIDCProxy) acts as a **confidential client** — it authenticates with Auth0 using a `CLIENT_ID` and `CLIENT_SECRET` pair, which is exactly the Machine to Machine pattern. The browser-based user login flow is handled between MCP clients (VS Code, Claude Desktop, etc.) and the OIDCProxy itself — MCP clients never talk to Auth0 directly.

    **Do not use "Regular Web Application"** — Auth0 enforces PKCE validation differently for web apps, which conflicts with how the OIDCProxy forwards authorization requests. This causes `code_challenge: Field required` errors.

### Steps

1. In the Auth0 Dashboard, go to **Applications → Applications**.
2. Select **+ Create Application**.
3. Fill in:

     | Field | Value |
     |-------|-------|
     | **Name** | `Actian MCP Server App` |
     | **Application Type** | **Machine to Machine Applications** |

4. Select **Create**.
5. When prompted, select your **Actian MCP Server** API and grant all scopes. (You can also do this later in [Part 3](#part-3-authorize-the-application-for-the-api).)
6. The application's **Settings** tab opens.

### Configure Application Settings

On the **Settings** tab, scroll down and configure:

| Setting | Value | Notes |
|---------|-------|-------|
| **Allowed Callback URLs** | `https://<mcp-server-host>:8000/auth/callback` | Must exactly match `<BASE_URL>/auth/callback`. Multiple URLs can be comma-separated. |
| **Allowed Logout URLs** | `https://<mcp-server-host>:8000` | (optional) For logout redirect. |
| **Allowed Web Origins** | `https://<mcp-server-host>:8000` | (optional) For CORS. |

!!! warning "Callback URL must match exactly"
    The **Allowed Callback URLs** value must match `<FASTMCP_SERVER_AUTH_BASE_URL>/auth/callback` exactly — including scheme (`http` vs `https`), host, and port. A mismatch causes Auth0 to reject the login with a `redirect_uri_mismatch` error.

Select **Save Changes**.

### Configure Grant Types

Machine to Machine applications should have **Authorization Code** enabled by default, but always verify — some tenants or configurations may differ.

1. On the **Settings** tab, scroll to the bottom and select **Show Advanced Settings**.
2. Select the **Grant Types** tab.
3. Enable **Authorization Code** (required for the browser-based OAuth login flow).
4. Keep **Client Credentials** enabled.
5. Optionally enable **Refresh Token** for token refresh support.
6. Select **Save Changes**.

!!! danger "Authorization Code grant is required"
    Without **Authorization Code** enabled, Auth0 returns `Grant type 'authorization_code' not allowed for the client`. M2M apps should have this grant type enabled by default, but always verify — if it was disabled, re-enable it here.

### What You Get from This Step

All values are on the **Settings** tab of your Application:

| Config Field | Where to find it in Auth0 |
|---|---|
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | **Client ID** (at the top of the Settings tab) |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | **Client Secret** (click the eye icon to reveal) |
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | Constructed from your **Domain**: `https://<your-domain>/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_BASE_URL` | Your MCP server's external URL (for example, `https://<mcp-server-host>:8000`). |

!!! tip "Finding the Domain"
    The **Domain** is shown at the top of the Settings tab (for example, `dev-abc123.us.auth0.com`). The OIDC discovery URL is always `https://<domain>/.well-known/openid-configuration`.


## Part 3: Authorize the Application for the API

!!! danger "This step is critical"
    Without it, Auth0 rejects token requests with `invalid_request` because your Application isn't authorized for the API.

### Why This Is Needed

Auth0 requires an explicit grant between an Application and an API before it will issue tokens. Without this authorization, token requests fail with `invalid_request`.

You can authorize from either direction — the Application's APIs tab or the API's Application Access tab:

**Option A — From the Application:**

1. Go to **Applications → Applications → your app** (for example, `Actian MCP Server App`).
2. Select the **APIs** tab.
3. Find your API (for example, `mcp_server` with identifier `https://<mcp-server-host>:8000/mcp`).
4. Select **Edit** next to your API.
5. Authorize both access types:

   - **User Access**: Set to **Authorized**. This is required for the browser-based login flow and user impersonation.
   - **Client Access**: Set to **Authorized**. This may already be authorized if you selected the API during M2M app creation.

6. Select **Update** to save.

**Option B — From the API:**

1. Go to **Applications → APIs → your API** (for example, `mcp_server`).
2. Select the **Application Access** tab.
3. Find your Application and select **Edit**.
4. Authorize both **User Access** and **Client Access** as above.

After saving, the Application should show two **AUTHORIZED** badges — one for User Access and one for Client Access.

!!! important "User Access is required for user impersonation"
    If you plan to use `user_impersonation: true`, the **User Access** column must show AUTHORIZED. Without it, Auth0 won't issue tokens with user identity claims (email, sub) during the Authorization Code flow, and the MCP server won't be able to extract a database username.


## Part 4: Create Auth0 Users (If Using User Impersonation)

If `user_impersonation` is `true`, the authenticated user's identity is forwarded to the database via `SET SESSION AUTHORIZATION`. Each OAuth user must have a matching database account. For more information, see [User Impersonation](../index.md#user-impersonation).

### Step 4.1: Create the User in Auth0

1. In the Auth0 Dashboard, go to **User Management → Users**.
2. Select **+ Create User**.
3. Fill in:

     | Field | Value | Notes |
     |-------|-------|-------|
     | **Email** | `jdoe@example.com` | The part before `@` (`jdoe`) becomes the database username. |
     | **Password** | A secure password | Used for Auth0 login. |
     | **Connection** | `Username-Password-Authentication` | Default database connection. |

4. Select **Create**.

!!! important "Database username = email prefix"
    The MCP server extracts the database username from the **email prefix** (the part before `@`). For example, `jdoe@example.com` → `jdoe`. Ensure the email prefix matches the database account name exactly.

    **Auth0 default behaviour**: Auth0's userinfo endpoint doesn't return a `username` or `preferred_username` claim by default. In practice, the server will use the **email prefix** as the database username. Always create database users to match this email prefix.

!!! note "Case sensitivity"
    If the database is case-sensitive (for example, `jdoe` ≠ `Jdoe`), ensure the email prefix exactly matches the database account name.

### Step 4.2: Create the Matching Database User

=== Example
Auth0 handles authentication, but the Actian database still needs the user to exist for impersonation to work:

```sql
-- Create the user account (no DB password needed — Auth0 handles authentication)
CREATE USER jdoe;

-- Grant access to the database
GRANT ACCESS ON DATABASE mydb TO jdoe;

-- Grant the necessary table permissions (adjust per your schema)
GRANT SELECT ON TABLE orders TO jdoe;
GRANT SELECT ON TABLE products TO jdoe;
```
=== Informix
```sql
-- Create the user account (DB password not used — Auth0 handles authentication)
CREATE USER mcpuser with password 'mcpuser' properties user 'daemon';;

-- Grant access to the database
GRANT CONNECT TO mcpuser;

-- Grant the necessary table permissions (adjust per your schema)
GRANT SELECT ON TABLE orders TO mcpuser;
GRANT SELECT ON TABLE products TO mcpuser;

-- Set session authorization to the privleged database_user passed to mcp server in conf.json
GRANT SETSESSIONAUTH ON 'mcpuser' TO 'database_user';

```

!!! note "Federated identity caveat"
    If users sign in via Google, Microsoft Entra, SAML, or corporate SSO through Auth0, the `sub` claim will look like `google-oauth2|12345` — the server strips the provider prefix, leaving `12345`, which is unlikely to match a database account. For SSO setups, set `user_impersonation` to `false` unless you can ensure the Auth0 user profile contains a matching username.


## Part 5: Assemble the Final Configuration

### Mapping Summary

| `conf.json` Field | Auth0 Source | Example Value |
|---|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `https://<Domain>/.well-known/openid-configuration` | `https://dev-abc123.us.auth0.com/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | Application → Settings → **Client ID** | `wNXUdrp9aBcDeFgHiJkLmN` |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Application → Settings → **Client Secret** | `a1B2c3D4e5F6g7H8i9J0...` |
| `FASTMCP_SERVER_AUTH_BASE_URL` | Your MCP server's external URL | `https://<mcp-server-host>:8000` |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | API → **Identifier** | `https://<mcp-server-host>:8000/mcp` |
| `user_impersonation` | Your choice | `true` or `false` |

!!! info "Audience fallback"
    If `FASTMCP_SERVER_AUTH_AUDIENCE` is omitted, the server uses `FASTMCP_SERVER_AUTH_CLIENT_ID` as the audience. This is common for Keycloak setups, but for Auth0 you should always set an explicit audience — the Client ID won't match the API Identifier.

!!! note
    The `AUDIENCE` is a logical identifier used for token validation — it doesn't need to be a reachable HTTPS URL.

### Example `conf.json`

```json
{
    "driver": "{Ingres}",
    "server": "@<db-host>,tcp_ip,<port>",
    "database": "mydb",
    "database_user": "<database_user>",
    "database_password": "<database_password>",
    "max_connections": 10,
    "host": "0.0.0.0",
    "port": 8000,
    "ssl_certfile": "/app/server.crt",
    "ssl_keyfile":  "/app/server.key",
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://<your-auth0-domain>/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "<your-client-id>",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<your-client-secret>",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://<your-server-host>:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "<your-api-identifier>",
        "user_impersonation": true
    }
}
```

!!! note
    Replace `<db-host>` with the database server address. Inside a Docker container, use the host's IP address or `host.docker.internal` — not `localhost` or `127.0.0.1`, which refer to the container itself.

For TLS setup details (certificate generation, Docker deployment, trusting self-signed certs), see [HTTPS / TLS for Remote Deployments](../index.md#https-tls-for-remote-deployments).

For security best practices (file permissions, `.gitignore`, secrets management), see [Security Best Practices](../index.md#security-best-practices).


## Verify End-to-End

After starting the MCP server container with OAuth configured:

1. Open a browser and navigate to your server's `/mcp` endpoint (for example, `https://<your-server-host>:8000/mcp`).
2. You should be **redirected to the Auth0 login page**.
3. After logging in, Auth0 redirects you back to the MCP server with a valid token.
4. Check the server logs for `Stored database username: <username>` to confirm user impersonation is active.


## Troubleshooting

### Verify OIDC Discovery Endpoint

```bash
curl https://dev-abc123.us.auth0.com/.well-known/openid-configuration \
  | python3 -m json.tool
```

You should see `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`, etc.

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `code_challenge: Field required` | Auth0 Application type is "Regular Web Application". | Recreate as **Machine to Machine** application — Auth0 doesn't allow changing app type after creation. See [Part 2](#part-2-create-an-auth0-application). |
| `Grant type 'authorization_code' not allowed` | M2M app missing Authorization Code grant. | Enable **Authorization Code** in Advanced Settings → Grant Types. See [Configure Grant Types](#configure-grant-types). |
| `invalid_request` when requesting a token | Application not authorized for the API. | [Part 3](#part-3-authorize-the-application-for-the-api) — authorize the Application. |
| `audience mismatch` | `FASTMCP_SERVER_AUTH_AUDIENCE` doesn't match the API Identifier. | Ensure they are identical strings. |
| `invalid_client` | Wrong `client_id` or `client_secret`. | Re-copy from Application → Settings. |
| `KeyError` on startup (for example, `CLIENT_SECRET`). | Some OAuth fields present but others missing. | Provide **all** required fields or remove `oauth` entirely. |
| `Could not extract username` | Token lacks `username`, `preferred_username`, or `email`. | Add email/profile scopes, or set `user_impersonation: false`. |
| `unauthorized` / 401 on every request | OAuth misconfigured or token expired. | Check server logs, verify OIDC discovery URL is reachable. |
| `redirect_uri_mismatch` | Callback URL doesn't match `<BASE_URL>/auth/callback`. | Fix **Allowed Callback URLs** in Auth0 (scheme + host + port must match exactly). |
| `ValueError: Issuer URL must be HTTPS` | OAuth without TLS configured. | Add `ssl_certfile`/`ssl_keyfile` and use `https://` for `BASE_URL`. |
| `ValueError: BASE_URL must start with https://` | SSL configured but `BASE_URL` still uses `http://`. | Update `BASE_URL` to `https://`. |
| `ssl.SSLError: PEM lib` | Missing cert/key env vars before Docker start. | Mount cert/key as volumes when starting the container (see [Docker deployment](../index.md#3-docker-deployment)). |
| `ERR_TLS_CERT_ALTNAME_INVALID` | Certificate missing SAN. | Regenerate with `-addext "subjectAltName=IP:<ip>"`. |
| `TypeError: fetch failed` (VS Code) | Self-signed cert not trusted by `Node.js`. | Launch VS Code with `NODE_EXTRA_CA_CERTS=/path/to/server.crt code .` |
| `Client Not Registered` (VS Code) | Server's Docker container was recreated, wiping client registrations, but VS Code caches the old client ID. | Quit VS Code, then delete stale registrations from the state DB (see [Clearing VS Code OAuth cache](#clearing-vs-code-oauth-cache) below) and reopen VS Code. To prevent recurrence, mount a Docker volume for `/root/.local/share/fastmcp`. |
| `Service not found: https://...` / `access_denied` | `AUDIENCE` mismatch between client request and server config (often `http` vs `https`). | Ensure `FASTMCP_SERVER_AUTH_AUDIENCE` in `conf.json` exactly matches the Auth0 API Identifier. |
| Token validation behaves unexpectedly | OIDC endpoint unreachable at startup. | Restart server after endpoint is accessible. |

### Clearing VS Code OAuth Cache

If the MCP server's Docker container is recreated, VS Code's cached OAuth client registration becomes stale. To clear it:

1. **Quit VS Code completely** (Cmd+Q on macOS, or close all windows on Linux/Windows).
2. Run the appropriate command for your OS:

    === "macOS"

        ```bash
        sqlite3 ~/Library/"Application Support"/Code/User/globalStorage/state.vscdb \
          "DELETE FROM ItemTable WHERE key LIKE '%dynamicAuth%<your-server-host>%';"
        ```

    === "Linux"

        ```bash
        sqlite3 ~/.config/Code/User/globalStorage/state.vscdb \
          "DELETE FROM ItemTable WHERE key LIKE '%dynamicAuth%<your-server-host>%';"
        ```

    === "Windows"

        ```powershell
        sqlite3 "$env:APPDATA\Code\User\globalStorage\state.vscdb" `
          "DELETE FROM ItemTable WHERE key LIKE '%dynamicAuth%<your-server-host>%';"
        ```

3. Reopen VS Code. It will re-register with the server automatically.

Replace `<your-server-host>` with your server's IP or hostname (for example, `35.185.60.76`). This only clears the registration for that specific server.

!!! tip "Prevent recurrence"
    Mount a Docker volume for the server's OAuth state so client registrations survive container recreation:
    ```bash
    docker run ... -v mcp-auth-data:/root/.local/share/fastmcp ...
    ```

### Token Expiration

Auth0 tokens have a configurable lifetime:

1. Go to **Applications → APIs → your API → Settings**.
2. Check **Token Expiration (Seconds)** — default is 86400 (24 hours).
3. Adjust as needed.

!!! note
    Token refresh is handled automatically by the OAuth flow when using browser-based authentication.


## Staging vs. Production

| Environment | Recommendation |
|---|---|
| **Development** | Use a free Auth0 tenant. |
| **Staging / Production** | Use a dedicated Auth0 tenant (or separate Application + API). Always use HTTPS for `BASE_URL` and callback URLs. |
