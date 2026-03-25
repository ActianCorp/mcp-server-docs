---
title: Keycloak Setup Guide
description: Step-by-step guide to configure Keycloak as the OAuth identity provider for the Actian MCP Server.
---

# Keycloak Setup Guide

This guide walks through creating and configuring a Keycloak **Realm**, **Client**, and **Audience Mapper** so the Actian MCP Server can authenticate users via OAuth 2.0 / OIDC.

By the end, you will have all the values needed to populate the `oauth` block in your `conf.json`. See the [Authentication overview](../index.md) for the full configuration reference and shared concepts (TLS, user impersonation, security practices).

!!! info "Generic OIDC provider"
    There is no dedicated Keycloak class in FastMCP — the server uses the generic `OIDCProxy` provider, which works with any OIDC-compliant identity provider including Keycloak.

---

## Quick-Start Checklist

For experienced Keycloak users — the full walkthrough follows below.

1. **Create a Realm** (or use an existing one).
2. **Create a Client** with _Client authentication_ enabled (confidential). Copy the **Client ID** and **Client Secret**.
3. **Add an Audience Mapper** to the client's dedicated scope so the Client ID appears in the token's `aud` claim. _Skip this and the MCP Server will reject tokens with `audience mismatch`._
4. **(Optional)** Add a **Sub Override Mapper** so the `sub` claim contains the username instead of a UUID.
5. **Create users** in the realm (if using `user_impersonation: true`).
6. **Fill `conf.json`** with the values from steps 1–3.
7. **Start the server** with `--transport sse` (or `http` / `streamable-http`).

---

## Prerequisites

- A running Keycloak instance (e.g. `http://localhost:8080`)
- Admin access to the Keycloak Admin Console
- The Actian MCP Server installed and ready to run

!!! tip "Consistent hostnames"
    Use either `localhost` or `127.0.0.1` for all services, not a mix. Modern browsers treat them as different origins. This guide uses `localhost` throughout.

!!! note "Keycloak version"
    This guide was written for **Keycloak 22+** (Quarkus-based). Older WildFly-based versions (< 17) have a different admin UI and URL structure.

!!! warning "Default admin credentials"
    If your Keycloak instance still uses the default `admin` / `admin` credentials, change them immediately via **Users → admin → Credentials** in the `master` realm.

---

## Part 1 — Create a Keycloak Realm

A **Realm** is the top-level container in Keycloak that holds users, clients, roles, and configuration.

### Steps

1. Log in to the [Keycloak Admin Console](http://localhost:8080/admin).
2. In the top-left dropdown (showing `master`), click **Create Realm**.
3. Fill in:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Realm name** | `actian-mcp` | Any descriptive name. Appears in all OIDC URLs. |
   | **Enabled** | `On` | |

4. Click **Create**.

### What you get from this step

| Config Field | Where to find it |
|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `http://localhost:8080/realms/actian-mcp/.well-known/openid-configuration` |

---

## Part 2 — Create a Keycloak Client

The **Client** represents the MCP server's OAuth credentials — it holds the `client_id` and `client_secret`.

### Steps

1. In the Admin Console, select your realm from the dropdown.
2. Click **Clients** in the left sidebar.
3. Click **Create client**.
4. Fill in:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Client type** | `OpenID Connect` | Default |
   | **Client ID** | `actian-mcp` | Becomes both `FASTMCP_SERVER_AUTH_CLIENT_ID` and `FASTMCP_SERVER_AUTH_AUDIENCE` (after audience mapper). |

5. Click **Next**.
6. On the **Capability config** screen:

   | Setting | Value | Notes |
   |---------|-------|-------|
   | **Client authentication** | `On` | Makes the client _confidential_ and generates a client secret. |
   | **Authorization** | `Off` | Not needed for basic OAuth |
   | **Standard flow** | Checked | Required for browser login |
   | **Direct access grants** | Checked | For testing only |

   !!! warning "Disable direct access grants in production"
       The `password` grant (direct access grants) is insecure for production use and only intended for local debugging with `curl`.

7. Click **Next**.
8. On the **Login settings** screen:

   | Setting | Value | Notes |
   |---------|-------|-------|
   | **Root URL** | `http://localhost:8000` | Your MCP server URL |
   | **Valid redirect URIs** | `http://localhost:8000/*` | For remote hosts, add `https://<ip>:8000/*` |
   | **Web origins** | `http://localhost:8000` | For CORS |

9. Click **Save**.

### Get the Client Secret

1. After creating the client, click the **Credentials** tab.
2. Copy the **Client secret** value.

### What you get from this step

| Config Field | Where to find it in Keycloak |
|---|---|
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | The **Client ID** you entered (e.g. `actian-mcp`) |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Clients → your client → **Credentials** tab |
| `FASTMCP_SERVER_AUTH_BASE_URL` | Your MCP server's public URL (e.g. `http://localhost:8000`) |

---

## Part 3 — Add the Audience Mapper (Critical)

!!! danger "This step is critical"
    Without it, Keycloak will not include the Client ID in the token's `aud` (audience) claim, and the MCP server will reject tokens with an `audience mismatch` error.

### Why this is needed

By default, Keycloak tokens only include internal audiences like `realm-management` and `account`. The MCP server validates that the token's `aud` claim matches the configured audience (the Client ID). You must explicitly tell Keycloak to include the Client ID in the audience list.

### Steps

1. Go to **Clients** → click your client (e.g. `actian-mcp`).
2. Click the **Client scopes** tab.
3. Click the **`actian-mcp-dedicated`** link (listed as "Dedicated").
   > If you don't see the dedicated scope, check the **Mappers** tab directly.
4. Click **Configure a new mapper** (or "Add Mapper").
5. Select **Audience** from the list (not **Audience Resolve**).

   !!! note "Audience vs Audience Resolve"
       "Audience Resolve" is a different mapper that resolves audiences dynamically — it will **not** hardcode your Client ID into `aud`. You need the plain **Audience** mapper.

6. Configure it:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Name** | `audience-mapping` | Any descriptive name |
   | **Included Client Audience** | Select your client (e.g. `actian-mcp`) | |
   | **Add to ID token** | `Off` | Not required |
   | **Add to access token** | `On` | **Required** — the MCP server checks the access token |

7. Click **Save**.

### Verify

After adding the mapper, request a token and inspect it. The `aud` claim should include your Client ID:

```
Audience: ['realm-management', 'account', 'actian-mcp']
                                                ↑ Required
```

---

## Part 4 — Add the Sub Override Mapper (Optional)

By default, Keycloak sets the `sub` claim to a UUID. You can override it to contain the login name for easier `user_impersonation` mapping.

### Steps

1. Go to **Clients** → your client → **Client scopes** tab.
2. Click the **`actian-mcp-dedicated`** link.
3. Click **Configure a new mapper** → select **User Property**.
4. Configure it:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Name** | `sub-override` | Just a label |
   | **Property** | `username` | Maps the login name |
   | **Token Claim Name** | `sub` | Overwrites the standard `sub` field |
   | **Claim JSON Type** | `String` | |
   | **Add to ID token** | `On` | |
   | **Add to access token** | `On` | |

5. Click **Save**.

### Verify

After adding the mapper, your token will contain:

```json
{
  "sub": "jdoe",
  "iss": "http://localhost:8080/realms/actian-mcp",
  "aud": ["realm-management", "account", "actian-mcp"],
  "preferred_username": "jdoe",
  "scope": "openid email profile"
}
```

!!! warning "OIDC spec trade-off"
    The OIDC spec expects `sub` to be a stable, unique identifier (like a UUID). Overriding it with a username is fine for internal tools like the MCP Server, but if a user renames their account, database permissions tied to the old name will break.

!!! tip "Alternative: use preferred_username"
    Instead of overriding `sub`, you can rely on the `preferred_username` claim (included by default when the `profile` scope is present). The MCP server's username extraction priority uses `preferred_username` before `sub`, so this works automatically without any mapper changes.

---

## Part 5 — Create Keycloak Users (If Using User Impersonation)

If `user_impersonation` is `true`, each Keycloak user must have a matching database account. See [User Impersonation](../index.md#user-impersonation) for full details.

### Steps

1. Go to **Users** in the left sidebar.
2. Click **Add user**.
3. Fill in:

   | Field | Value | Notes |
   |-------|-------|-------|
   | **Username** | `jdoe` | Must match the database account name |
   | **Email** | `jdoe@example.com` | Optional but recommended |
   | **First Name** | `John` | Optional |
   | **Last Name** | `Doe` | Optional |
   | **Enabled** | `On` | |

4. Click **Create**.
5. Go to the **Credentials** tab → **Set password** → enter a password, toggle **Temporary** to `Off` → **Save**.

### Create the Matching Database User

```sql
-- Create the user account (no DB password needed — Keycloak handles authentication)
CREATE USER jdoe;

-- Grant access to the database
GRANT ACCESS ON DATABASE mydb TO jdoe;

-- Grant the necessary table permissions (adjust per your schema)
GRANT SELECT ON TABLE orders TO jdoe;
GRANT SELECT ON TABLE products TO jdoe;
```

!!! note "Why `profile` scope is required"
    Keycloak's userinfo endpoint only returns `preferred_username` when the token includes the `profile` scope. Without it, the endpoint returns only the `sub` claim (a UUID by default).

!!! important "Keycloak does not produce a `username` claim automatically"
    The MCP server's username extraction priority is: `username` → `preferred_username` → email prefix → sanitized `sub`. Keycloak does **not** produce a `username` claim by default — it only appears if you explicitly configure a User Attribute mapper. In practice, `preferred_username` (item 2 in the priority) is the reliable choice for Keycloak, and it works automatically when the `profile` scope is present.

!!! note "Federated identity (LDAP / Social login)"
    If Keycloak federates users from an external LDAP or social provider, the `sub` claim may be a UUID that doesn't match a database account. Ensure federated users have `preferred_username` set, or add the sub override mapper ([Part 4](#part-4-add-the-sub-override-mapper-optional)), or set `user_impersonation: false`.

---

## Part 6 — Configure Scopes (Optional)

The MCP server requires at minimum `openid email profile` (added automatically). You can define custom scopes for finer access control.

### Add custom scopes in Keycloak

1. Go to **Client scopes** → **Create client scope**.
2. Fill in:

   | Field | Value |
   |-------|-------|
   | **Name** | `read:mcp_server` |
   | **Protocol** | `OpenID Connect` |
   | **Type** | `Optional` |

3. Click **Save**.
4. Go to **Clients** → your client → **Client scopes** tab → **Add client scope** → select `read:mcp_server` → **Add** as "Default".

### Config value

```json
"FASTMCP_SERVER_AUTH_SCOPE": "openid email profile read:mcp_server"
```

---

## Part 7 — Assemble the Final Configuration

### Mapping summary

| `conf.json` Field | Keycloak Source | Example Value |
|---|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `http://<host>/realms/<realm>/.well-known/openid-configuration` | `http://localhost:8080/realms/actian-mcp/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | Clients → your client → **Client ID** | `actian-mcp` |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Clients → your client → **Credentials** | (your secret) |
| `FASTMCP_SERVER_AUTH_BASE_URL` | Your MCP server's public URL | `http://localhost:8000` |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | Same as Client ID (after audience mapper) | `actian-mcp` |
| `FASTMCP_SERVER_AUTH_SCOPE` | Scopes assigned to the client | `openid email profile read:mcp_server` |
| `user_impersonation` | Your choice | `true` or `false` |
| `FASTMCP_SERVER_AUTH_REDIRECT_PATH` | (Optional) Custom OAuth callback path | `/auth/callback` (default) |

!!! info "Audience in Keycloak vs Auth0"
    In Auth0, the audience is a separate API Identifier (often a URL). In Keycloak, the audience is typically the **Client ID** itself — but only if you added the audience mapper in [Part 3](#part-3-add-the-audience-mapper-critical). If `FASTMCP_SERVER_AUTH_AUDIENCE` is omitted from config, the server falls back to `CLIENT_ID`, which is the correct behavior for Keycloak.

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
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "http://localhost:8080/realms/actian-mcp/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "actian-mcp",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "your-client-secret-here",
        "FASTMCP_SERVER_AUTH_BASE_URL": "http://localhost:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "actian-mcp",
        "FASTMCP_SERVER_AUTH_SCOPE": "openid email profile",
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
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://keycloak.example.com/realms/actian-mcp/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "actian-mcp",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "your-client-secret-here",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://34.148.108.35:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "actian-mcp",
        "FASTMCP_SERVER_AUTH_SCOPE": "openid email profile",
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

1. Open a browser and navigate to `http://localhost:8000/sse` (or `/mcp` for HTTP transport).
2. You should be **redirected to the Keycloak login page**.
3. Log in with a Keycloak user (e.g. `jdoe`).
4. After logging in, Keycloak redirects back to the MCP server with a valid token.
5. Check server logs for `Stored database username: jdoe` to confirm user impersonation is active.

---

## Troubleshooting

### Verify OIDC discovery endpoint

```bash
curl http://localhost:8080/realms/actian-mcp/.well-known/openid-configuration \
  | python3 -m json.tool
```

### Verify token contents (development only)

```bash
curl -s -X POST \
  http://localhost:8080/realms/actian-mcp/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=actian-mcp" \
  -d "client_secret=your-secret" \
  -d "username=jdoe" \
  -d "password=secret" \
  -d "scope=openid email profile" \
  | python3 -m json.tool
```

Decode the `access_token` at [jwt.io](https://jwt.io) and verify:

- `aud` contains your Client ID (e.g. `actian-mcp`)
- `sub` contains the username (if you added the sub override mapper) or a UUID
- `preferred_username` contains the login name

### Common errors

| Error | Cause | Fix |
|-------|-------|-----|
| `audience mismatch` | Client ID not in token's `aud` claim | [Part 3](#part-3-add-the-audience-mapper-critical) — add the audience mapper |
| `invalid_client` | Wrong `client_id` or `client_secret` | Re-copy from Clients → Credentials tab |
| `invalid_grant` | Wrong username/password, or user disabled | Check user exists and is enabled |
| `KeyError` on startup (e.g. `CLIENT_SECRET`) | Some OAuth fields present but others missing | Provide **all** required fields or remove `oauth` entirely |
| `Could not extract username` | No usable username claim in token | Add sub override mapper ([Part 4](#part-4-add-the-sub-override-mapper-optional)), ensure `preferred_username` is present, or set `user_impersonation: false` |
| `unauthorized` / 401 on every request | OAuth misconfigured or token expired | Check server logs, verify OIDC discovery URL is reachable |
| `Client not enabled` / `Realm not found` | Realm or client is disabled | Ensure both are Enabled in admin console |
| `ValueError: Issuer URL must be HTTPS` | OAuth on non-localhost host without TLS | Add `ssl_certfile`/`ssl_keyfile` and use `https://` for `BASE_URL` |
| `ValueError: BASE_URL must start with https://` | SSL configured but `BASE_URL` still uses `http://` | Update `BASE_URL` to `https://` |
| `ssl.SSLError: PEM lib` | Missing cert/key env vars before Docker start | Set `SSL_CERTFILE`/`SSL_KEYFILE` before `docker compose up` |
| `ERR_TLS_CERT_ALTNAME_INVALID` | Certificate missing SAN | Regenerate with `-addext "subjectAltName=IP:<ip>"` |
| `TypeError: fetch failed` (VS Code) | Self-signed cert not trusted by Node.js | Trust cert + set `NODE_EXTRA_CA_CERTS` |
| Token validation behaves unexpectedly | OIDC endpoint unreachable at startup | The server falls back to default verification without `TokenCapturingJWTVerifier` — `user_impersonation` will not work even though the server appears to be running. Restart after endpoint is accessible. |

### Token expiration

Keycloak tokens have a configurable lifetime:

1. Go to **Realm Settings** → **Tokens** tab.
2. Key settings:

   | Setting | Default | Notes |
   |---------|---------|-------|
   | **Access Token Lifespan** | 5 minutes | Increase for long-running MCP sessions (e.g. 1 hour) |
   | **SSO Session Idle** | 30 minutes | How long before an idle session expires |
   | **SSO Session Max** | 10 hours | Maximum session duration |

3. Adjust as needed and click **Save**.

---

## Keycloak vs. Auth0 — Key Differences

| Aspect | Auth0 | Keycloak |
|--------|-------|----------|
| **Provider class** | Dedicated Auth0 support in FastMCP | Generic `OIDCProxy` (standard OIDC) |
| **Audience** | Separate API Identifier (often a URL) | Client ID itself (requires audience mapper) |
| **`sub` claim** | `auth0\|<id>` or `google-oauth2\|<id>` | UUID by default (can override to username) |
| **`preferred_username`** | Not always present | Always present by default |
| **Discovery URL format** | `https://<domain>/.well-known/openid-configuration` | `http://<host>/realms/<realm>/.well-known/openid-configuration` |
| **Self-hosted** | No (SaaS only) | Yes (self-hosted or cloud) |
| **Token lifetime config** | API Settings → Token Expiration | Realm Settings → Tokens |

---

## Staging vs. Production

| Environment | Recommendation |
|---|---|
| **Development** | Run Keycloak locally (`http://localhost:8080`). Use `http://` URLs. Enable direct access grants for `curl`-based testing. |
| **Staging / Production** | Deploy Keycloak behind HTTPS. Always use HTTPS for `CONFIG_URL`, `BASE_URL`, and callback URLs. Use a strong `CLIENT_SECRET`. **Disable direct access grants**. Change default admin credentials. |
