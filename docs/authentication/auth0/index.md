---
title: Auth0 Setup Guide
description: Step-by-step guide to configure Auth0 as the OAuth identity provider for the Actian MCP Server.
---

# Auth0 Setup Guide

This guide walks through creating and configuring an Auth0 **Application** and **API** so the Actian MCP Server can authenticate users via OAuth 2.0 / OIDC.

By the end, you will have all the values needed to populate the `oauth` block in your `conf.json`. See the [Authentication overview](../index.md) for the full configuration reference and shared concepts (TLS, user impersonation, security practices).

> **Reference**: [FastMCP Auth0 Integration](https://gofastmcp.com/integrations/auth0)

---

## Quick-Start Checklist

For experienced Auth0 users — the full walkthrough follows below.

1. **Create an API** (Applications → APIs → + Create API). The **Identifier** becomes `FASTMCP_SERVER_AUTH_AUDIENCE`.
2. **Create an Application** (Applications → Applications → + Create Application → Regular Web Application). Copy the **Client ID** and **Client Secret**.
3. **Authorize the Application for the API** (APIs → your API → Machine to Machine Applications → toggle your app). _Skip this and you get `invalid_request`._
4. **Fill `conf.json`** with the values from steps 1–3 plus your Auth0 domain.
5. **Start the server** with `--transport sse` (or `http` / `streamable-http`).

---

## Prerequisites

- An Auth0 account ([sign up free](https://auth0.com/signup))
- An Auth0 **Tenant** (created automatically on signup, e.g. `dev-abc123`)
- The Actian MCP Server installed and ready to run

---

## Part 1 — Create an Auth0 API

The **API** represents the Actian MCP Server as a protected resource in Auth0. Tokens issued by Auth0 will include the API's identifier as the `audience` claim.

### Steps

1. Log in to the [Auth0 Dashboard](https://manage.auth0.com/).
2. In the left sidebar, navigate to **Applications → APIs**.
3. Click **+ Create API**.
4. Fill in the form:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Name** | `Actian MCP Server` | Display name (any descriptive string) |
   | **Identifier (Audience)** | `http://127.0.0.1:8000/mcp` | This becomes your `FASTMCP_SERVER_AUTH_AUDIENCE`. Use your actual MCP server URL + path. This is a logical identifier — it does **not** need to be a reachable URL. |
   | **Signing Algorithm** | `RS256` | Default; leave as-is |

5. Click **Create**.

### What you get from this step

| Config Field | Where to find it |
|---|---|
| `FASTMCP_SERVER_AUTH_AUDIENCE` | The **Identifier** you entered (e.g. `http://127.0.0.1:8000/mcp`) |

!!! info "Auth0 requires an explicit audience"
    Unlike Keycloak (where the audience defaults to the Client ID), Auth0 requires you to create a separate API and use its Identifier as the audience. If you omit `FASTMCP_SERVER_AUTH_AUDIENCE` from your config, the server falls back to `CLIENT_ID` — which won't match the API Identifier, causing `audience mismatch` errors.

---

## Part 2 — Create an Auth0 Application

The **Application** represents the MCP server's OAuth client — it holds the `client_id` and `client_secret` used during the OAuth handshake.

!!! note "About the auto-created Test Application"
    When you created the API in Part 1, Auth0 automatically created a **Machine to Machine (Test Application)**. You _can_ use it for quick local testing, but for production use a **Regular Web Application** as described below — M2M applications have different defaults for token lifetimes, refresh tokens, and grant types.

### Steps

1. In the Auth0 Dashboard, go to **Applications → Applications**.
2. Click **+ Create Application**.
3. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `Actian MCP Server App` |
   | **Application Type** | **Regular Web Applications** |

   > Choose **Regular Web Applications** because the MCP server is a backend that can securely store a client secret.

4. Click **Create**.
5. You are taken to the application's **Settings** tab.

### Configure Application Settings

On the **Settings** tab, scroll down and configure:

| Setting | Value | Notes |
|---------|-------|-------|
| **Allowed Callback URLs** | `http://127.0.0.1:8000/auth/callback` | Must exactly match `<BASE_URL>/auth/callback`. For remote hosts with TLS, use e.g. `https://34.148.108.35:8000/auth/callback`. Multiple URLs can be comma-separated. |
| **Allowed Logout URLs** | `http://127.0.0.1:8000` | (Optional) For logout redirect |
| **Allowed Web Origins** | `http://127.0.0.1:8000` | (Optional) For CORS |

!!! warning "Callback URL must match exactly"
    The **Allowed Callback URLs** value must match `<FASTMCP_SERVER_AUTH_BASE_URL>/auth/callback` exactly — including scheme (`http` vs `https`), host, and port. A mismatch causes Auth0 to reject the login with a `redirect_uri_mismatch` error.

Click **Save Changes**.

### Configure Grant Types

1. On the **Settings** tab, scroll to the bottom and click **Show Advanced Settings**.
2. Click the **Grant Types** tab.
3. Ensure **Authorization Code** is checked (required for the browser-based OAuth login flow).
4. Optionally enable **Refresh Token** for token refresh support.
5. Click **Save Changes**.

!!! warning "Authorization Code grant is required"
    Without **Authorization Code** enabled, the OAuth flow will fail — Auth0 won't issue an authorization code during the login redirect, even though the login page appears to work normally.

### What you get from this step

All values are on the **Settings** tab of your Application:

| Config Field | Where to find it in Auth0 |
|---|---|
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | **Client ID** (at the top of the Settings tab) |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | **Client Secret** (click the eye icon to reveal) |
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | Constructed from your **Domain**: `https://<your-domain>/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_BASE_URL` | Your MCP server's public URL (e.g. `http://127.0.0.1:8000`) |

!!! tip "Finding the Domain"
    The **Domain** is shown at the top of the Settings tab (e.g. `dev-abc123.us.auth0.com`). The OIDC discovery URL is always `https://<domain>/.well-known/openid-configuration`.

---

## Part 3 — Authorize the Application for the API

!!! danger "This step is critical"
    Without it, Auth0 will reject token requests with `invalid_request` because your Application is not authorized for the API.

### Why this is needed

During the OAuth handshake:

- **Client**: "I want a token for the API `http://127.0.0.1:8000/mcp`."
- **Auth0**: "I know that API exists, but who are you? Oh, you are App `wNXUdrp9...`. Let me check if `wNXUdrp9...` is authorized for that API... **NOPE → Error: `invalid_request`**."

You must explicitly authorize the Application for the API.

### Steps

1. In the Auth0 Dashboard, go to **Applications → Applications**.
2. Click on your Application (e.g. `Actian MCP Server App`).
3. Click the **APIs** tab.
4. Find your API (e.g. `mcp_server` with identifier `http://127.0.0.1:8000/mcp`). It will show as **UNAUTHORIZED** initially.
5. Click **Edit** next to your API. A permissions popup opens.
6. In the popup:

   - **User Access** tab: Set the **Authorization** dropdown to **Authorized — Pick and choose permissions**. Select your scopes (e.g. `read:mcp_server`) or click **All**.
     > A yellow warning _"You are about to create a grant with all permissions available"_ appears when **All** is selected. This is expected — it means the token will include all scopes you defined on the API.
   - **Client Access** tab: This is typically already set to **Authorized** by default. Verify it shows **AUTHORIZED** before proceeding.

7. Click **Update** to save.
8. The Application row should show two **AUTHORIZED** badges — one for User Access and one for Client Access.

---

## Part 4 — Configure Scopes (Optional)

Scopes restrict what actions a token allows. The MCP server requires at minimum `openid email profile` (added automatically).

### Define custom scopes on the API

1. Go to **Applications → APIs → your API → Permissions** tab.
2. Add scopes as needed:

   | Permission (Scope) | Description |
   |---|---|
   | `read:mcp_server` | Read access to MCP server tools and resources |

3. Click **Add**.

### Config value

Scopes are **space-separated** (not comma-separated):

```json
"FASTMCP_SERVER_AUTH_SCOPE": "openid email profile read:mcp_server"
```

---

## Part 5 — Create Auth0 Users (If Using User Impersonation)

If `user_impersonation` is `true`, the authenticated user's identity is forwarded to the database via `SET SESSION AUTHORIZATION`. Each OAuth user must have a matching database account. See [User Impersonation](../index.md#user-impersonation) for full details.

### Step 5.1 — Create the User in Auth0

1. In the Auth0 Dashboard, go to **User Management → Users**.
2. Click **+ Create User**.
3. Fill in:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Email** | `jdoe@example.com` | The part before `@` (`jdoe`) becomes the database username |
   | **Password** | A secure password | Used for Auth0 login |
   | **Connection** | `Username-Password-Authentication` | Default database connection |

4. Click **Create**.

!!! important "Database username = email prefix"
    The MCP server extracts the database username from the **email prefix** (the part before `@`). For example, `jdoe@example.com` → `jdoe`. Ensure the email prefix matches the database account name exactly.

    **Auth0 default behaviour**: Auth0's userinfo endpoint does not return a `username` or `preferred_username` claim by default. In practice, the server will use the **email prefix** as the database username. Always create database users to match this email prefix.

!!! note "Case sensitivity"
    If the database is case-sensitive (e.g. `jdoe` ≠ `Jdoe`), ensure the email prefix exactly matches the database account name.

### Step 5.2 — Create the Matching Database User

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

!!! note "Federated identity caveat"
    If users sign in via Google, Microsoft Entra, SAML, or corporate SSO through Auth0, the `sub` claim will look like `google-oauth2|12345` — the server strips the provider prefix, leaving `12345`, which is unlikely to match a database account. For SSO setups, set `user_impersonation` to `false` unless you can ensure the Auth0 user profile contains a matching username.

---

## Part 6 — Assemble the Final Configuration

### Mapping summary

| `conf.json` Field | Auth0 Source | Example Value |
|---|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `https://<Domain>/.well-known/openid-configuration` | `https://dev-abc123.us.auth0.com/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | Application → Settings → **Client ID** | `wNXUdrp9aBcDeFgHiJkLmN` |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Application → Settings → **Client Secret** | `a1B2c3D4e5F6g7H8i9J0...` |
| `FASTMCP_SERVER_AUTH_BASE_URL` | Your MCP server's public URL | `http://127.0.0.1:8000` |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | API → **Identifier** | `http://127.0.0.1:8000/mcp` |
| `FASTMCP_SERVER_AUTH_SCOPE` | Scopes you defined on the API | `openid email profile read:mcp_server` |
| `user_impersonation` | Your choice | `true` or `false` |
| `FASTMCP_SERVER_AUTH_REDIRECT_PATH` | (Optional) Custom OAuth callback path | `/auth/callback` (default) |

> **Audience fallback**: If `FASTMCP_SERVER_AUTH_AUDIENCE` is omitted, the server uses `FASTMCP_SERVER_AUTH_CLIENT_ID` as the audience. This is common for Keycloak setups, but for Auth0 you should always set an explicit audience — the Client ID won't match the API Identifier.

> **All-or-nothing**: Provide **all** required OAuth fields (`CONFIG_URL`, `CLIENT_ID`, `CLIENT_SECRET`, `BASE_URL`) or **none**. If only some fields are present, the server will fail to start with a `KeyError`.

> **Note**: The `AUDIENCE` is a logical identifier used for token validation — it does **not** need to be a reachable HTTPS URL.

### Example `conf.json` (local development)

```json
{
    "driver": "{Ingres}",
    "server": "@localhost,tcp_ip,VW",
    "database": "mydb",
    "max_connections": 10,
    "host": "127.0.0.1",
    "port": 8000,
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://dev-abc123.us.auth0.com/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "wNXUdrp9aBcDeFgHiJkLmN",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "a1B2c3D4e5F6g7H8i9J0kLmNoPqRsTuVwXyZ",
        "FASTMCP_SERVER_AUTH_BASE_URL": "http://127.0.0.1:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "http://127.0.0.1:8000/mcp",
        "FASTMCP_SERVER_AUTH_SCOPE": "openid email profile read:mcp_server",
        "user_impersonation": true
    }
}
```

### Example `conf.json` (remote deployment with TLS)

```json
{
    "driver": "{Ingres}",
    "server": "@localhost,tcp_ip,VW",
    "database": "mydb",
    "max_connections": 10,
    "host": "0.0.0.0",
    "port": 8000,
    "ssl_certfile": "/app/server.crt",
    "ssl_keyfile":  "/app/server.key",
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://dev-abc123.us.auth0.com/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "wNXUdrp9aBcDeFgHiJkLmN",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "a1B2c3D4e5F6g7H8i9J0kLmNoPqRsTuVwXyZ",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://34.148.108.35:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "http://127.0.0.1:8000/mcp",
        "FASTMCP_SERVER_AUTH_SCOPE": "openid email profile read:mcp_server",
        "user_impersonation": true
    }
}
```

For TLS setup details (certificate generation, Docker deployment, trusting self-signed certs), see [HTTPS / TLS for Remote Deployments](../index.md#https-tls-for-remote-deployments).

For security best practices (file permissions, `.gitignore`, secrets management), see [Security Best Practices](../index.md#security-best-practices).

---

## Start the Server

```bash
export DATABASE_USER=<your_database_username>
export DATABASE_PASSWORD=<your_database_password>

uv run actian-mcp-server \
  --dbms=analytics_engine \
  --conf-file=src/analytics_engine/conf.json \
  --transport=sse
```

### Verify end-to-end

1. Open a browser and navigate to `http://127.0.0.1:8000/sse` (or `/mcp` for HTTP transport).
2. You should be **redirected to the Auth0 login page**.
3. After logging in, Auth0 redirects you back to the MCP server with a valid token.
4. Check the server logs for `Stored database username: <username>` to confirm user impersonation is active.

---

## Troubleshooting

### Verify OIDC discovery endpoint

```bash
curl https://dev-abc123.us.auth0.com/.well-known/openid-configuration \
  | python3 -m json.tool
```

You should see `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`, etc.

### Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `invalid_request` when requesting a token | Application not authorized for the API | [Part 3](#part-3-authorize-the-application-for-the-api) — authorize the Application |
| `audience mismatch` | `FASTMCP_SERVER_AUTH_AUDIENCE` doesn't match the API Identifier | Ensure they are identical strings |
| `invalid_client` | Wrong `client_id` or `client_secret` | Re-copy from Application → Settings |
| `KeyError` on startup (e.g. `CLIENT_SECRET`) | Some OAuth fields present but others missing | Provide **all** required fields or remove `oauth` entirely |
| `Could not extract username` | Token lacks `username`, `preferred_username`, or `email` | Add email/profile scopes, or set `user_impersonation: false` |
| `unauthorized` / 401 on every request | OAuth misconfigured or token expired | Check server logs, verify OIDC discovery URL is reachable |
| `redirect_uri_mismatch` | Callback URL doesn't match `<BASE_URL>/auth/callback` | Fix **Allowed Callback URLs** in Auth0 (scheme + host + port must match exactly) |
| `ValueError: Issuer URL must be HTTPS` | OAuth on non-localhost host without TLS | Add `ssl_certfile`/`ssl_keyfile` and use `https://` for `BASE_URL` |
| `ValueError: BASE_URL must start with https://` | SSL configured but `BASE_URL` still uses `http://` | Update `BASE_URL` to `https://` |
| `ssl.SSLError: PEM lib` | Missing cert/key env vars before Docker start | Set `SSL_CERTFILE`/`SSL_KEYFILE` before `docker compose up` |
| `ERR_TLS_CERT_ALTNAME_INVALID` | Certificate missing SAN | Regenerate with `-addext "subjectAltName=IP:<ip>"` |
| `TypeError: fetch failed` (VS Code) | Self-signed cert not trusted by Node.js | Trust cert + set `NODE_EXTRA_CA_CERTS` |
| Token validation behaves unexpectedly | OIDC endpoint unreachable at startup | Restart server after endpoint is accessible |

### Token expiration

Auth0 tokens have a configurable lifetime:

1. Go to **Applications → APIs → your API → Settings**.
2. Check **Token Expiration (Seconds)** — default is 86400 (24 hours).
3. Adjust as needed.

> Token refresh is handled automatically by the OAuth flow when using browser-based authentication.

---

## Staging vs. Production

| Environment | Recommendation |
|---|---|
| **Development** | Use a free Auth0 tenant with `http://127.0.0.1` URLs. |
| **Staging / Production** | Use a dedicated Auth0 tenant (or separate Application + API). Always use HTTPS for `BASE_URL` and callback URLs. |
