---
title: Keycloak Setup Guide
description: Step-by-step guide to configure Keycloak as the OAuth identity provider for the Actian MCP Server.
---

# Configuring Keycloak

This guide describes the creation and configuration of a Keycloak Realm, Client, and Audience Mapper. It enables the Actian MCP Server to authenticate users through OAuth 2.0 and OpenID Connect (OIDC). 

By the completion of this guide, you will have obtained the values that are required to populate the `oauth` block in the `conf.json` file. For the full configuration reference and shared concepts such as TLS, user impersonation, and security practices, see  [Authentication Overview](index.md).

!!! tip "Other deployment shapes"
    The numbered steps configure the default mode, in which the MCP server runs the OAuth login itself. For a server that serves several databases, see [Multi-Target Deployments: Per-Target Scopes](#multi-target-deployments-per-target-scopes). For an application that already holds the user's Keycloak token, see [Resource-Server Mode](#resource-server-mode).

!!! info "Generic OIDC provider"
    FastMCP uses a generic OIDC provider. While there is no dedicated Keycloak class, the server uses the `OIDCProxy` provider, which is compatible with any OIDC-compliant identity provider.


## Quick Start

The checklist below is the whole procedure in brief. Use it if you are already familiar with the Keycloak Admin Console. Otherwise, work through the numbered steps that follow, which give the full navigation for each item.

1. **Create a realm** (or use an existing one).
2. **Create a client** with _Client authentication_ enabled and record the **Client ID** and **Client Secret**.
3. **Add an audience mapper** using the **Included Custom Audience** field to show the audience string in the token's `aud` claim. 

    !!! warning
        If you skip this step, the MCP Server rejects tokens with `audience mismatch`.

4. **(Optional)** Add a **sub override mapper** to the `sub` claim containing the username instead of a UUID.
5. **Create an `mcp:write` client scope** and attach it to the client as **Optional**, if `query_mode` is `read-write` and the deployment does not serve more than one server or database. See [Step 5](#step-5-add-the-write-scope-read-write-deployments-only). For a multi-target deployment, create per-target scopes instead; see [Multi-Target Deployments: Per-Target Scopes](#multi-target-deployments-per-target-scopes).
6. **Create users** in the realm, if using `user_impersonation: true`.
7. **Fill `conf.json`** file with the values from [Step 1](#step-1-create-a-keycloak-realm) to [Step 3](#step-3-add-the-audience-mapper-required).
8. **Restart the container** so it loads the updated `conf.json`. The container image already serves HTTP, so no transport flag is needed. See [Getting Started: Step 3](../../get-started/index.md#step-3-start-the-container).


## Prerequisites

- A running Keycloak instance (version 22 or higher) is accessible by the MCP server.
- Admin access is granted to the Keycloak Admin Console.
- The Actian MCP Server is installed and ready for deployment.

!!! note "Keycloak version"
    This guide is optimized for Quarkus-based Keycloak (v22+). If you are using a WildFly-based version (v17 or older), the UI and URL structures will differ significantly.

!!! warning "Default admin credentials"
    If your Keycloak instance uses the default `admin` / `admin` credentials, change it through **Users** > **admin** > **Credentials** in the `master` realm.


## Step 1: Create a Keycloak Realm

A Realm is an isolated container for managing users, credentials, and roles.

1. Log in to the Keycloak Admin Console `http://<keycloak-host>:8080/admin`.
2. In the top-left drop-down (displaying `master`), select **Create Realm**.
3. Fill the form as follows:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Realm name** | `actian-mcp` | Any descriptive name; it appears in all OIDC URLs |
    | **Enabled** | `On` | A disabled realm rejects all logins and token requests for every client and user in it. Leave this `On`. |

4. Select **Create**.

### Output of Step 1

| Config Field | Where to find it |
|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `http://<keycloak-host>:8080/realms/actian-mcp/.well-known/openid-configuration` |


## Step 2: Create a Keycloak Client

The client represents the MCP server’s OAuth credentials and holds `client_id` and `client_secret`.

1. In the Admin Console, select your realm from the drop-down.
2. Select **Clients** in the left panel.
3. Select **Create client**.
4. Fill the form as follows:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Client type** | `OpenID Connect` | Default |
    | **Client ID** | `actian-mcp` | Becomes both `FASTMCP_SERVER_AUTH_CLIENT_ID` and `FASTMCP_SERVER_AUTH_AUDIENCE` (after audience mapper) |

5. Select **Next**.
6. On the **Capability config** screen, configure the following values:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Client authentication** | `On` | Makes the client _confidential_ and generates a client secret |
    | **Authorization** | `Off` | Not needed for basic OAuth |
    | **Standard flow** | Checked | Required for browser login |
    | **Direct access grants** | Checked | Required for testing only |

    !!! warning "Disable direct access grants in production"
        The `password` grant (direct access grants) is insecure for production use and only intended for local debugging with `curl`.

7. Select **Next**.
8. On the **Login settings** screen, configure the following values:

    | Setting | Value | Notes |
    |---------|-------|-------|
    | **Root URL** | `https://<mcp-server-host>:8000` | MCP server's external URL |
    | **Valid redirect URIs** | `https://<mcp-server-host>:8000/*` | Must match the server's external URL |
    | **Web origins** | `https://<mcp-server-host>:8000` | For CORS |

9. Select **Save**.

### Get the Client Secret

1. After creating the client, select the **Credentials** tab.
2. Copy the **Client secret** value.

### Output of Step 2

| Config Field | Where to find it in Keycloak |
|---|---|
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | **Client ID**, for example, `actian-mcp` |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Clients > your client > **Credentials** tab |
| `FASTMCP_SERVER_AUTH_BASE_URL` | MCP server's external URL, for example, `https://<mcp-server-host>:8000` |


## Step 3: Add the Audience Mapper (Required)

!!! danger "This step is critical"
    Without the Audience Mapper, Keycloak does not include the Client ID in the token's `aud` (audience) claim, and the MCP server rejects tokens with an `audience mismatch` error.

By default, Keycloak tokens only include internal audiences like `account`. The MCP server validates that the token's `aud` claim matches the configured `FASTMCP_SERVER_AUTH_AUDIENCE` value. You must inform Keycloak to include the audience string in the token.

!!! warning "Included Client Audience versus Included Custom Audience"
    The Audience mapper uses two audience fields:

    - **Included Client Audience** - Resolves the selected client name to its **internal UUID**, for example, `16f502e4-483e-4b0d-adbd-4d20e6e33e73`. It does not match the audience string that MCP server expects and causes `audience mismatch` errors.
    - **Included Custom Audience** - Inserts the literal string, for example, `actian-mcp`. This is required by the MCP server and the recommended option.

1. Navigate to **Clients** and select your client, for example, `actian-mcp`.
2. Select the **Client scopes** tab.
3. Select the **`actian-mcp-dedicated`** link (listed as "Dedicated"). If you do not see the dedicated scope, check the **Mappers** tab directly.
4. Select **Configure a new mapper** or **Add Mapper**.
5. Select **Audience** (not **Audience Resolve**) from the list.

    !!! note "Audience versus Audience Resolve"
         "Audience Resolve" is a different mapper that resolves audiences dynamically. It does not hardcode your audience into `aud`. Therefore, you are required to select **Audience** mapper.

6. Configure the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `audience-mapping` | Provide a descriptive name. |
    | **Included Client Audience** | _(leave empty)_ | Do not use this field. It resolves to an internal UUID. |
    | **Included Custom Audience** | `actian-mcp` | The literal string that must match `FASTMCP_SERVER_AUTH_AUDIENCE` in the `conf.json` file. |
    | **Add to ID token** | `Off` | This field is not required. |
    | **Add to access token** | `On` | **Required** - the MCP server checks the access token. |

7. Select **Save**.

### Verification

After adding the mapper, request a new token and decode it. The `aud` claim includes the audience string:

```bash
# Request a token
TOKEN=$(curl -s -X POST \
  "http://<keycloak-host>:8080/realms/actian-mcp/protocol/openid-connect/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=actian-mcp" \
  -d "client_secret=<your-secret>" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Decode and inspect the aud claim
echo "$TOKEN" | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool | grep aud
```

Expected output:
```json
"aud": ["actian-mcp", "account"]
```

!!! note "Token caching"
    If you still see a UUID instead of `actian-mcp` in the `aud` claim, the old token may be cached. Wait for it to expire (default 5 minutes) or go to **Sessions** in the Keycloak Admin Console and sign out of all sessions for the service account to force a fresh token.


## Step 4 (Optional): Add the Sub Override Mapper

By default, Keycloak sets the `sub` claim to a UUID. You can override it to contain the login name for easier `user_impersonation` mapping.

1. Navigate to **Clients** > your client > **Client scopes** tab.
2. Select the **`actian-mcp-dedicated`** link.
3. Select **Configure a new mapper** > **User Property**.
4. Configure the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `sub-override` | Acts as a label |
    | **Property** | `username` | Maps the login name |
    | **Token Claim Name** | `sub` | Overwrites the standard `sub` field |
    | **Claim JSON Type** | `String` | NA |
    | **Add to ID token** | `On` | NA |
    | **Add to access token** | `On` | NA |

5. Select **Save**.

### Verification

After adding the mapper, the token contains the following:

```json
{
  "sub": "jdoe",
  "iss": "http://<keycloak-host>:8080/realms/actian-mcp",
  "aud": ["realm-management", "account", "actian-mcp"],
  "preferred_username": "jdoe",
  "scope": "openid email profile"
}
```

!!! warning "OIDC spec trade-off"
    The OIDC spec expects `sub` to be a stable, unique identifier (like a UUID). It is acceptable to override it with a username for internal tools like the MCP Server, but if a user renames their account, database permissions tied to the old name will break.

!!! tip "Alternative: use preferred_username"
    Instead of overriding `sub`, you can rely on the `preferred_username` claim (included by default when the `profile` scope is present). The MCP server's username extraction priority uses `preferred_username` before `sub`, so it works automatically without any mapper changes.


## Step 5: Add the Write Scope (Read-Write Deployments Only)

Skip this step if `query_mode` is `read-only`. A read-only server never requests the `mcp:write` scope.

Also skip it for a multi-target deployment with more than one server or more than one database. There, `mcp:write` does not apply: each write needs the target's `actian:{host}:{instance}:{database}:write` scope instead. See [Multi-Target Deployments: Per-Target Scopes](#multi-target-deployments-per-target-scopes).

When `query_mode` is `read-write`, the server requests `mcp:write` and rejects any write whose token does not carry it. For more information, see [Write support](../write-support.md).

### Step 5.1: Create the Client Scope

1. Navigate to **Client scopes** in the left sidebar and select **Create client scope**.
2. Configure the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `mcp:write` | Must match exactly. This is the value the server requests. |
    | **Description** | `MCP database write access` | Acts as a label |
    | **Type** | `None` | You attach it to the client in Step 5.2 |
    | **Protocol** | `openid-connect` | NA |
    | **Include in token scope** | `On` | Puts the scope in the token's `scope` claim, where the server reads it |

3. Select **Save**.

### Step 5.2: Attach the Scope to the Client as Optional

1. Navigate to **Clients** > your client, for example `actian-mcp`, and select the **Client scopes** tab.
2. Select **Add client scope**.
3. Select `mcp:write`, then select **Add** > **Optional**.

!!! warning "Add it as Optional, not Default"
    An optional scope is issued only when the caller asks for it, which is what the MCP server does when `query_mode` is `read-write`. If you add `mcp:write` as a default scope instead, every token issued to this client carries write access whether it was requested or not, and the scope no longer distinguishes read-only callers from write-capable ones.

### User Eligibility

In Keycloak a client scope is attached to a **client**, not to a user. Any user who authenticates through this client and requests `scope=openid mcp:write` receives it. Keycloak roles do not change that, because the server authorizes writes from the token's `scope` claim rather than from roles.

!!! important "Restrict writes per user in the database, not in Keycloak"
    Keycloak cannot limit an optional client scope to particular users, so do not rely on it to decide who may write. Because `user_impersonation` runs each statement as the authenticated user, the effective control is the privileges you grant that user in the database. Grant `INSERT`, `UPDATE`, and `DELETE` only to the accounts that should have them, and leave the others with `SELECT`. A user who obtains `mcp:write` still cannot change a table they hold no write privilege on.

    This differs from Auth0, where the permission is assigned through a role and users without that role cannot obtain it at all. If you need the scope itself withheld per user, use a separate Keycloak client for read-only callers and attach `mcp:write` only to the client used by writers.

### Verification

Confirm the realm advertises the scope:

```bash
curl -s https://<keycloak-host>:8443/realms/actian-mcp/.well-known/openid-configuration \
  | grep -o '"scopes_supported":\[[^]]*\]'
```

The output contains `mcp:write`. Then, on the client's **Client scopes** tab, confirm `mcp:write` is listed with the **Optional** assigned type.

!!! warning "The database still decides what a user can change"
    The `mcp:write` scope permits write statements in general. It does not grant table privileges. With `user_impersonation` enabled, each write also runs as that user's own database account, so grant the matching `INSERT`, `UPDATE`, and `DELETE` privileges in the database as well. See [Creating the Matching Database User](#creating-the-matching-database-user).


## Step 6: Create Keycloak Users (If Using User Impersonation)

If `user_impersonation` is `true`, each Keycloak user contains a matching database account. For more information, see [User Impersonation](index.md#user-impersonation).

1. Navigate to **Users** in the left panel.
2. Select **Add user**.
3. Fill the form as follows:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Username** | `jdoe` | Must match with the database account name |
    | **Email** | `jdoe@example.com` | Optional but recommended |
    | **First Name** | `John` | Optional |
    | **Last Name** | `Doe` | Optional |
    | **Enabled** | `On` | A disabled user cannot log in or receive tokens, even with correct credentials. Leave this `On`. If your Keycloak version does not show this field on the Add User form, the account is enabled by default; you can still find and toggle it later from the user's Details tab. |

4. Select **Create**.
5. Navigate to the **Credentials** tab > **Set password** > enter a password > toggle **Temporary** to `Off` > **Save**.

### Creating the Matching Database User

```sql
-- Create the user account (no DB password needed — Keycloak handles authentication)
CREATE USER jdoe;

-- Grant access to the database
GRANT ACCESS ON DATABASE mydb TO jdoe;

-- Grant the necessary table permissions (adjust per your schema)
GRANT SELECT ON TABLE orders TO jdoe;
GRANT SELECT ON TABLE products TO jdoe;
```

!!! note "`profile` scope is required"
    Keycloak's userinfo endpoint only returns `preferred_username` when the token includes the `profile` scope. Without it, the endpoint returns only the `sub` claim (a UUID by default).

!!! important "Keycloak does not produce a `username` claim automatically"
    The MCP server's username extraction priority is - `username` > `preferred_username` > email prefix > sanitized `sub`. Keycloak **does not** produce a `username` claim by default. It only appears if you explicitly configure a User Attribute mapper. In practice, `preferred_username` (second in the priority) is the reliable choice for Keycloak, and it works automatically when the `profile` scope is present.

!!! note "Federated identity (LDAP / Social login)"
    If Keycloak federates users from an external LDAP or social provider, the `sub` claim may be a UUID that does not match a database account. Ensure that the federated users have `preferred_username` set, or add the sub-override mapper ([Step 4](#step-4-optional-add-the-sub-override-mapper)), or set `user_impersonation: false`.


## Step 7: Assemble the Final Configuration

### Mapping Summary

| `conf.json` Field | Keycloak Source | Example Value |
|---|---|---|
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `http://<keycloak-host>:8080/realms/<realm>/.well-known/openid-configuration` | `http://10.100.11.187:8080/realms/actian-mcp/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | Clients > your client > **Client ID**| `actian-mcp` |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Clients > your client > **Credentials**| (your secret) |
| `FASTMCP_SERVER_AUTH_BASE_URL` | MCP server's external URL | `https://<mcp-server-host>:8000` |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | Value from **Included Custom Audience** in the audience mapper | `actian-mcp` |
| `user_impersonation` | As per your choice | `true` or `false` |

!!! info "Audience in Keycloak versus Auth0"
    In Auth0, the audience is a separate API Identifier (often a URL). In Keycloak, you define the audience string through the **Included Custom Audience** field in the audience mapper ([Step 3](#step-3-add-the-audience-mapper-required)). A common convention is to set it to the Client ID, for example, `actian-mcp`. If `FASTMCP_SERVER_AUTH_AUDIENCE` is omitted from the configuration, the server falls back to `CLIENT_ID`.

### Example `conf.json`

```json
{
    "driver": "{Ingres}",
    "server": "@<db-host>,tcp_ip,<installation_id>",
    "database": "mydb",
    "database_user": "<database_user>",
    "database_password": "<database_password>",
    "max_connections": 10,
    "host": "0.0.0.0",
    "port": 8000,
    "query_mode": "read-write",
    "write_confirmation": true,
    "ssl_certfile": "/app/server.crt",
    "ssl_keyfile":  "/app/server.key",
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "http://<keycloak-host>:8080/realms/actian-mcp/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "actian-mcp",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<your-client-secret>",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp-server-host>:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "actian-mcp",
        "user_impersonation": true
    }
}
```

!!! note
    Replace `<db-host>` with the database server address. In the Docker container, use the host's IP address or `host.docker.internal`(not `localhost` or `127.0.0.1`, which refer to the container itself).

For TLS setup details (certificate generation, Docker deployment, trusting self-signed certifications), see [HTTPS / TLS for Remote Deployments](index.md#secure-remote-deployments-with-https-and-tls).

For security best practices (file permissions, `.gitignore`, secrets management), see [Security Best Practices](index.md#security-best-practices).


## Verify End-to-End

After starting the MCP server container with OAuth configured:

1. Open a browser and navigate to the server's `/mcp` endpoint, for example, `https://<mcp-server-host>:8000/mcp`.
2. You are **redirected to the Keycloak login page**.
3. Log in with a Keycloak user, for example, `jdoe`.
4. After logging in, Keycloak redirects you back to the MCP server with a valid token.
5. Check server logs for `Stored database username: jdoe` to confirm user impersonation is active.


## Troubleshooting

### Verify OIDC Discovery Endpoint

```bash
curl http://<keycloak-host>:8080/realms/actian-mcp/.well-known/openid-configuration \
  | python3 -m json.tool
```

### Verify Token Contents (Development Only)

```bash
curl -s -X POST \
  http://<keycloak-host>:8080/realms/actian-mcp/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=actian-mcp" \
  -d "client_secret=your-secret" \
  -d "username=jdoe" \
  -d "password=secret" \
  -d "scope=openid email profile" \
  | python3 -m json.tool
```

Decode the `access_token` at [jwt.io](https://jwt.io) and verify the following:

- `aud` contains Client ID, for example, `actian-mcp`.
- `sub` contains the username (if you added the sub override mapper) or a UUID.
- `preferred_username` contains the login name.

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `audience mismatch` | Audience string not in the token's `aud` claim. | [Step 3](#step-3-add-the-audience-mapper-required) - add the audience mapper using **Included Custom Audience** (not Included Client Audience, which resolves to a UUID). |
| `invalid_client` | Wrong `client_id` or `client_secret`. | Re-copy from Clients > Credentials tab. |
| `invalid_grant` | Wrong username/password, or user disabled. | Check user exists and is enabled. |
| `KeyError` on startup (for example, `CLIENT_SECRET`) | Some OAuth fields are present but others missing. | Provide **all** required fields or remove `oauth` entirely. |
| `Could not extract username` | No usable username claim in token. | Add sub-override mapper ([Step 4](#step-4-optional-add-the-sub-override-mapper)). Ensure `preferred_username` is present or set `user_impersonation: false`. |
| `unauthorized` / 401 on every request | OAuth misconfigured or token expired. | Check server logs and verify the OIDC discovery URL is reachable. |
| `403` `insufficient_scope` on a target URL | Multi-target deployment: the token has no read grant for that target, or the target does not exist. | Grant the per-target scope and sign in again. See [Multi-Target Deployments: Per-Target Scopes](#what-a-caller-without-a-grant-sees). |
| `Client not enabled` / `Realm not found` | Realm or client is disabled. | Ensure both  Realm and client are enabled in the Admin console. |
| `ValueError: Issuer URL must be HTTPS` | OAuth without TLS configured. | Add `ssl_certfile`/`ssl_keyfile` and use `https://` for `BASE_URL`. |
| `ValueError: BASE_URL must start with https://` | SSL configured but `BASE_URL` still uses `http://`. | Update `BASE_URL` to `https://`. |
| `ssl.SSLError: PEM lib` | Missing certificate/key environment variables before Docker starts. | Mount certificate/key as volumes when starting the container (see [Docker deployment](index.md#step-3-deploy-the-docker)). |
| `ERR_TLS_CERT_ALTNAME_INVALID` | Certificate missing SAN. | Regenerate with `-addext "subjectAltName=IP:<ip>"`. |
| `TypeError: fetch failed` (VS Code) | Self-signed certificate not trusted by `Node.js`. | Trust certificate and set `NODE_EXTRA_CA_CERTS`. |
| Token validation behaves unexpectedly | OIDC endpoint is unreachable at startup. | The server falls back to default verification without `TokenCapturingJWTVerifier` - `user_impersonation` does not work even though the server appears to be running. Restart after the endpoint is accessible. |

### Token Expiration

Keycloak tokens have a configurable lifetime:

1. Navigate to **Realm Settings** > **Tokens** tab.
2. Do the following key settings:

    | Setting | Default | Notes |
    |---------|---------|-------|
    | **Access Token Lifespan** | 5 minutes | Increase for long-running MCP sessions, for example, 1 hour |
    | **SSO Session Idle** | 30 minutes | How long before an idle session expires |
    | **SSO Session Max** | 10 hours | Maximum session duration |

3. Adjust as needed and select **Save**.


## Multi-Target Deployments: Per-Target Scopes

Skip this section if your `conf.json` serves a single database. It applies when the server is configured with a `targets` registry that serves several databases, each reached through its own target URL. For the deployment model and the `targets` configuration, see [Multi-Target Deployments](../multi-target.md).

In a multi-target deployment, every request to a target URL is authorized by a **per-target scope** in the caller's access token. A token without a matching grant is refused, even if it is otherwise valid.

### Scope Grammar

```
actian:{host}:{instance}:{database}:{read|write}
```

| Segment | Must match |
|---|---|
| `{host}` | The target's `host` value exactly, or `*` |
| `{instance}` | The target's `instance` value exactly, or `*` |
| `{database}` | One of the target's databases, or `*` |
| `{read\|write}` | `read` or `write` |

The following rules apply:

- `*` matches **exactly one** segment, never zero and never more than one.
- `write` implies `read`. A `:write` grant also satisfies a read of the same host, instance, and database.
- Scopes are grants only. There are no deny scopes; a request is refused only because no grant covers it.

| Scope | Grants |
|---|---|
| `actian:<db-host>:<instance>:salesdb:read` | Read `salesdb` on that one target |
| `actian:<db-host>:<instance>:salesdb:write` | Read **and** write `salesdb` on that one target |
| `actian:<db-host>:<instance>:*:read` | Read every database on that one target |
| `actian:*:*:*:read` | Read every database on every target in the registry |

!!! warning "Host wildcards are logged every time they are used"
    A scope with `*` in the host segment, such as `actian:*:*:*:write`, reaches every target. Reserve it for administrative or break-glass access. Each request it authorizes writes a `WARNING` line to the server log naming the scope and the target, for audit review.

### Where the Server Reads Scopes in the Token

The server collects grants from three access-token claims and uses all of them together:

| Claim | Accepted format |
|---|---|
| `scope` | Space-separated string (the standard OAuth claim) |
| `scp` | Space-separated string or JSON array |
| `permissions` | JSON array |

Keycloak puts the names of the client scopes it issued into `scope`. To place other values in the token, use a mapper that writes `scp` or `permissions`, as described in Option B below.

### Step 1: Create the Per-Target Scopes

Choose one of the following options.

| Option | How grants reach the token | Use when |
|---|---|---|
| **A. One client scope per grant** | The client scope name is the grant, and Keycloak lists it in the `scope` claim. | You have a small number of grants, or a calling application must request individual grants by name. |
| **B. Grouping client scope** | One client scope carries a list of grants in a Hardcoded claim mapper. | You want to issue a set of grants together under one scope name. |

#### Option A: One Client Scope per Grant

1. Navigate to **Client scopes** and select **Create client scope**.
2. Configure the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `actian:<db-host>:<instance>:salesdb:read` | The exact grant string. Keycloak copies this name into the token's `scope` claim. |
    | **Type** | `None` | You attach it to the client in [Step 2](#step-2-attach-the-scopes-to-the-client). |
    | **Protocol** | `openid-connect` | NA |
    | **Include in token scope** | `On` | **Required.** Without it the name does not appear in the `scope` claim, and the server never sees the grant. |

3. Select **Save**.
4. Repeat for each grant you intend to issue.

#### Option B: Grouping Client Scope with a Hardcoded Claim Mapper

1. Navigate to **Client scopes** and select **Create client scope**.
2. Enter a **Name** for the group, for example `mcp:targets`, set **Type** to `None` and **Protocol** to `openid-connect`, and select **Save**.
3. Open the new scope, select the **Mappers** tab, and select **Configure a new mapper** > **Hardcoded claim**.
4. Configure the following fields:

    | Field | Value | Notes |
    |-------|-------|-------|
    | **Name** | `target-scopes` | Acts as a label |
    | **Token Claim Name** | `scp` | Or `permissions`. Do not use `scope`, which Keycloak manages itself. |
    | **Claim value** | `["actian:<db-host>:<instance>:salesdb:read","actian:<db-host>:<instance>:finance:read"]` | A JSON array of grant strings |
    | **Claim JSON Type** | `JSON` | Makes the claim a real array. If you write `scp` as type `String` instead, use a space-separated list. |
    | **Add to access token** | `On` | **Required** - the server reads the access token |
    | **Add to ID token** | `Off` | Not required |
    | **Add to userinfo** | `Off` | Not required |

5. Select **Save**.

!!! warning "Two hardcoded mappers writing the same claim collide"
    If a token receives two grouping scopes whose mappers both write `scp`, only one value survives. Either keep each set of grants that can be issued together in one mapper, or give the second grouping scope a different claim name, for example `permissions`.

### Step 2: Attach the Scopes to the Client

1. Navigate to **Clients** > the client that requests tokens, and select the **Client scopes** tab.
2. Select **Add client scope**, select the per-target scopes from Step 1, then select **Add** > **Default** or **Optional**, as described below.

| Mode | Attach as | Why |
|---|---|---|
| OAuth login proxy (the walkthrough above) | **Default** | The server requests only `openid email profile`, the scopes listed in `FASTMCP_SERVER_AUTH_SCOPE`, and `mcp:write` when writes are enabled. An optional per-target scope is therefore never requested. Listing it in `FASTMCP_SERVER_AUTH_SCOPE` would make it a required scope on every token. |
| [Resource-server mode](#resource-server-mode) | **Optional** | The calling application requests the scopes it needs, at sign-in or in a token exchange. Attach them to the calling application's client, not only to the MCP client. |

!!! important "Grants follow the client, not the user"
    Like `mcp:write`, a per-target client scope is attached to a client, so every user who authenticates through that client can obtain it. To give different groups of users different targets, use a separate Keycloak client for each group and attach only that group's scopes. With `user_impersonation` enabled, each statement also runs as the user's own database account, so database privileges remain the final control over what a user can read or change.

### Writes on a Target: Per-Target `:write` Versus `mcp:write`

The server applies exactly one write model to each request. It never combines them.

| Request | Write is authorized by | `mcp:write` |
|---|---|---|
| A target URL | The `:write` grant for that host, instance, and database, or a wildcard that covers it | Not consulted. It neither grants nor blocks writes on a target. |
| The `/mcp` endpoint, with no target in the path | `mcp:write`, as in [Step 5](#step-5-add-the-write-scope-read-write-deployments-only) | Required |

The `/mcp` endpoint without a target accepts writes only in a single-database deployment, or when the `targets` block has exactly one server with one database. `mcp:write` does not apply to a multi-target deployment with more than one server or more than one database.

A `:write` grant does not bypass the other write controls. `query_mode` must still be `read-write`, each write still needs approval when `write_confirmation` is enabled, and with `user_impersonation` enabled the database user still needs the table privileges. See [Write support](../write-support.md).

### What a Caller Without a Grant Sees

When an authenticated caller requests a target its token has no read grant for, the server answers **403** with `error="insufficient_scope"`. The `WWW-Authenticate` header names the missing scope:

```
WWW-Authenticate: Bearer error="insufficient_scope",
    error_description="Required scope: actian:<db-host>:<instance>:salesdb:read",
    scope="actian:<db-host>:<instance>:salesdb:read",
    resource_metadata="https://<mcp-server-host>:8000/.well-known/oauth-protected-resource/mcp"
```

- The response is **identical for a target that does not exist**, so the endpoint cannot be used to discover which targets are configured. A path that cannot name any target gets the same 403 without a `scope` value.
- A caller with no valid token gets **401**, not 403, for every target path.
- Behind the OAuth login proxy, `scope` names only the missing scope. In resource-server mode it also lists the scopes the token already holds, so that a client requesting exactly that set keeps its existing grants.
- The server log records the refusal as `Target scope enforcement rejected request`.

!!! warning "Behind the OAuth login proxy, automatic re-login cannot add a scope"
    An MCP client that receives this 403 may try to sign in again and ask for the named scope. Behind the OAuth login proxy this fails: the browser shows an authorization error such as `Client was not registered with scope ...`, because the proxy accepts only the scopes the client registered with. The error is expected. Grant the scope in Keycloak ([Step 1](#step-1-create-the-per-target-scopes) and [Step 2](#step-2-attach-the-scopes-to-the-client)), then sign in again.

!!! note "Grouping scopes and requests by name"
    If you deliver grants through a grouping scope (Option B), the individual grant strings are claim values, not Keycloak client scopes. A client or calling application that asks Keycloak for a single grant by name, for example `scope=actian:<db-host>:<instance>:salesdb:read`, may not receive it. Request the grouping scope instead, or use Option A for grants that must be requested individually.

### Verification

1. Request a token for a test user, including the grouping scope if you use Option B, and decode it (see [Verify Token Contents](#verify-token-contents-development-only)).
2. Confirm the grants appear in `scope` (Option A), or in `scp` or `permissions` as a list (Option B):

    ```json
    {
      "aud": ["actian-mcp", "account"],
      "preferred_username": "jdoe",
      "scope": "openid email profile mcp:targets",
      "scp": ["actian:<db-host>:<instance>:salesdb:read"]
    }
    ```

3. Connect to a target the user holds a grant for and confirm the call succeeds. Then connect to a target the user has no grant for and confirm the server answers 403 `insufficient_scope`.


## Resource-Server Mode

Use this mode when an application has already signed the user in with Keycloak and calls the MCP server directly, passing a Keycloak access token. The MCP server runs no OAuth login, holds no client ID or client secret, and only verifies the tokens it receives against the realm's published signing keys. For how this mode compares with the OAuth login proxy, see [Resource-Server Mode](resource-server.md).

| | OAuth login proxy (the walkthrough above) | Resource-server mode |
|---|---|---|
| Who signs the user in | The MCP server, through Keycloak | The calling application |
| Tokens accepted | Only tokens the server issued itself | Keycloak tokens that carry the MCP audience |
| Client ID and secret in `conf.json` | Required | Not used |
| Username source | Userinfo endpoint, then token claims, then `sub` | Token claims only |
| Suits | Generic MCP clients | Applications that already hold the user's token |

A single deployment runs one mode. If you need both, run two deployments against the same databases.

### Step 1: Prepare the MCP Client in Keycloak

The MCP client from [Step 2](#step-2-create-a-keycloak-client) now serves only as the **audience**: it is never used to sign anyone in.

1. Complete [Step 1](#step-1-create-a-keycloak-realm) to [Step 3](#step-3-add-the-audience-mapper-required). The audience mapper is still required. Without it, the token's `aud` carries only internal audiences such as `account`, and every call is rejected.
2. Skip [Step 4](#step-4-optional-add-the-sub-override-mapper). This mode never reads `sub` as a username.
3. If you need writes on a single-database deployment, complete [Step 5](#step-5-add-the-write-scope-read-write-deployments-only). The server does not request `mcp:write` in this mode, so the calling application must request it.

### Step 2: Register the Calling Application as Its Own Client

The calling application needs a **separate** Keycloak client. It runs the user's login and obtains the token for the MCP server, as described in [Step 5](#step-5-get-a-token-for-the-mcp-server-calling-application).

1. Create a client for the application as in [Step 2](#step-2-create-a-keycloak-client), with **Client authentication** set to `On`.
2. If the application will use [token exchange](#exchange-the-users-token), go to the new client's **Settings** tab, under **Capability config**, enable **Standard token exchange**, and select **Save**. Token exchange requires a confidential client, which is why **Client authentication** must be `On`.

    !!! note "Enable the exchange on the calling client"
        The **Standard token exchange** switch belongs to the client that *sends* the exchange request, which is the calling application's client. Enabling it on the MCP client has no effect.

    !!! warning "Keycloak version"
        Keycloak 26.2 and later support standard token exchange (RFC 8693) without extra server configuration. On earlier versions token exchange is a preview feature with a different configuration model. Check your Keycloak version before following these steps.

### Step 3: Make the MCP Audience Available to the Calling Client

Keycloak puts an audience in a token only if the requesting client can reach it through its client scopes. Without this step, a token requested at sign-in has no MCP audience and the server rejects it with `audience mismatch`, and a token exchange fails with `Requested audience not available: actian-mcp`.

1. Navigate to **Client scopes** > **Create client scope**, name it, for example, `mcp-audience`, set **Type** to `None`, and select **Save**.
2. On its **Mappers** tab, select **Configure a new mapper** > **Audience**, and set **Included Custom Audience** to the MCP audience, for example `actian-mcp`, with **Add to access token** set to `On`. These are the same values as in [Step 3](#step-3-add-the-audience-mapper-required).
3. Navigate to **Clients** > the calling application's client > **Client scopes** tab > **Add client scope**, select `mcp-audience`, then select **Add** > **Optional**.
4. Attach the scopes the calling application will request to its client as **Optional** in the same way: the per-target scopes from [Step 1](#step-1-create-the-per-target-scopes) for a multi-target deployment, or the `mcp:write` scope from [Step 5](#step-5-add-the-write-scope-read-write-deployments-only) for writes on a single-database deployment. Keycloak cannot issue a scope the calling client cannot reach.

### Step 4: Make Sure the Token Carries a Username

With `user_impersonation` enabled (the default), each query runs as the database user named in the token. In this mode the server reads the username **only from the token itself**, in this order:

1. `username`
2. `preferred_username`
3. `email` (the part before `@`)

There is no userinfo lookup and no fallback to `sub`. A token that carries none of these claims is rejected with **401**. The reason, naming the missing claims, is written to the server log only.

Keycloak adds `preferred_username` through the built-in `profile` client scope, which Keycloak assigns to new clients by default. Nothing requests `profile` in this mode, so keep it assigned as a **Default** client scope and confirm the claim is present in the token the application sends (see [Verification](#verification-resource-server-mode)).

!!! warning "Keycloak service-account tokens carry a username"
    A `client_credentials` token from Keycloak contains `preferred_username: service-account-<client-id>`. It passes the username check, and the server then tries to run queries as `service-account-<client-id>`, a database account that normally does not exist. The failure appears at the database, not at authentication. For machine callers that do not act for a user, set `"user_impersonation": false`. Per-target scopes are still enforced when impersonation is off.

!!! note "Federated users"
    If users federated from LDAP or a social provider have no usable `preferred_username`, either set it in Keycloak or run with `"user_impersonation": false`.

### Step 5: Get a Token for the MCP Server (Calling Application)

The server accepts any token from the realm that carries the MCP audience and the scopes the call needs. The calling application can obtain one in either of two ways:

| | Request the MCP audience at sign-in | Exchange the user's token |
|---|---|---|
| How | The application includes the MCP scopes when the user signs in. | The user signs in as usual, and the application exchanges that token for a separate token for the MCP server. |
| Tokens the application holds | One. The user's token also carries the MCP audience and scopes. | Two. The user's token carries no MCP audience or scopes; only the exchanged token does. |
| Extra Keycloak setup | None | **Standard token exchange** on the calling client ([Step 2](#step-2-register-the-calling-application-as-its-own-client)) |

Choose token exchange when the user's token is also sent to other services and should not grant access to the MCP server.

#### Request the MCP Audience at Sign-In

Add the audience scope from [Step 3](#step-3-make-the-mcp-audience-available-to-the-calling-client), and any per-target scopes or `mcp:write` the application needs, to the `scope` parameter of the application's authorization request. For example:

```text
scope=openid mcp-audience actian:<db-host>:<instance>:salesdb:read
```

The resulting access token's `aud` contains `actian-mcp`. The application sends this token to the MCP server in the `Authorization: Bearer` header.

#### Exchange the User's Token

The calling application exchanges the user's own token for one that carries the MCP audience:

```bash
curl -s -X POST \
  "https://<keycloak-host>:8443/realms/<realm>/protocol/openid-connect/token" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
  -d "client_id=<calling-app-client-id>" \
  -d "client_secret=<calling-app-client-secret>" \
  -d "subject_token=<user-access-token>" \
  -d "subject_token_type=urn:ietf:params:oauth:token-type:access_token" \
  -d "requested_token_type=urn:ietf:params:oauth:token-type:access_token" \
  -d "audience=actian-mcp" \
  -d "scope=mcp-audience actian:<db-host>:<instance>:salesdb:read"
```

- The user's token (`subject_token`) must have been issued to the calling application's client, or list that client in its `aud` claim. Otherwise Keycloak rejects the exchange.
- The `audience` value is a Keycloak **Client ID**: the MCP client's Client ID, which must also be the **Included Custom Audience** and `FASTMCP_SERVER_AUTH_AUDIENCE`.
- The `scope` parameter names the audience scope from Step 3 and any per-target scopes or `mcp:write` the call needs. If you use a grouping scope (Option B), name the grouping scope, for example `mcp:targets`. Requesting a scope that is not attached to the calling client fails with `400` `invalid_scope`.

The user's original token keeps its own audience; only the exchanged token carries `actian-mcp`. The application sends the exchanged token to the MCP server in the `Authorization: Bearer` header.

### Step 6: Configure the MCP Server

```json
{
    "driver": "{Ingres}",
    "server": "@<db-host>,tcp_ip,<installation_id>",
    "database": "mydb",
    "database_user": "<database_user>",
    "database_password": "<database_password>",
    "max_connections": 10,
    "host": "0.0.0.0",
    "port": 8000,
    "ssl_certfile": "/app/server.crt",
    "ssl_keyfile":  "/app/server.key",
    "auth_mode": "resource-server",
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://<keycloak-host>:8443/realms/<realm>/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "actian-mcp",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp-server-host>:8000",
        "user_impersonation": true
    }
}
```

| Key | Location | Meaning |
|---|---|---|
| `auth_mode` | Top level of `conf.json`, **not** inside `oauth` | Set to `resource-server`. |
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `oauth` | The realm's OIDC discovery document. The server reads `issuer` and `jwks_uri` from it. Required. |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | `oauth` | The audience every token must carry, the **Included Custom Audience** value. **Required** in this mode: there is no client ID to fall back to. |
| `FASTMCP_SERVER_AUTH_BASE_URL` | `oauth` | The server's public HTTPS address, published in its protected-resource metadata. Required. |
| `FASTMCP_SERVER_AUTH_SCOPE` | `oauth` | Optional. Scopes required on **every** token. Unlike proxy mode, `openid`, `email`, and `profile` are not added automatically. |
| `user_impersonation` | `oauth` | `true` (default) runs each query as the token's user. Set `false` for machine callers. |

- Do not set `FASTMCP_SERVER_AUTH_CLIENT_ID` or `FASTMCP_SERVER_AUTH_CLIENT_SECRET`. A client ID is ignored with a warning in the log.
- The same HTTPS rules as proxy mode apply: on a non-localhost host, set `ssl_certfile` and `ssl_keyfile`, and use `https://` in `FASTMCP_SERVER_AUTH_BASE_URL`.
- Every configuration error in this mode is **fatal**. If a required key is missing or the discovery document cannot be fetched, the server refuses to start rather than starting without authentication.

### Verification (Resource-Server Mode)

1. Decode the token the application sends (for example at [jwt.io](https://jwt.io)) and confirm the following:

    - `aud` contains the MCP audience, for example `actian-mcp`.
    - `iss` is exactly the `issuer` in the discovery document.
    - `preferred_username` (or `username` or `email`) is present when `user_impersonation` is `true`.
    - The per-target scopes or `mcp:write` the call needs are present.

2. With the token in `$TOKEN` and the server address in `$BASE`, run the following checks:

    ```bash
    # The metadata names your Keycloak realm under authorization_servers
    curl -s "$BASE/.well-known/oauth-protected-resource/mcp" | python3 -m json.tool

    # No login endpoints exist in this mode (both return 404)
    curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp/authorize"
    curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp/oauth/token"

    # Without a token the server answers 401
    curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp"
    ```

    If the last check returns anything other than `401`, authentication is not active. See the last row of [Troubleshooting](#troubleshooting-resource-server-mode).

3. Make an MCP call with the token and check the server log for `Stored database username (strict claim mode): <name>`.

### Troubleshooting (Resource-Server Mode)

| Symptom | Cause | Fix |
|---|---|---|
| Server refuses to start, naming an `oauth` key | `FASTMCP_SERVER_AUTH_CONFIG_URL`, `FASTMCP_SERVER_AUTH_AUDIENCE`, or `FASTMCP_SERVER_AUTH_BASE_URL` is missing or empty. | Supply all three. No client ID is used in this mode. |
| Server refuses to start while fetching the discovery document | Keycloak is unreachable, or its certificate is not trusted. | Check that the discovery URL is reachable from inside the container and that the certificate Keycloak presents is valid. |
| `401` with `issuer mismatch` in the log | The signature is valid, but the token's `iss` differs from the discovery document's `issuer`: the same realm reached through a different hostname or scheme. | Make Keycloak report one consistent hostname (its configured frontend hostname) to both the calling application and the MCP server, and point `FASTMCP_SERVER_AUTH_CONFIG_URL` at that address. |
| `401` with only `invalid_token` in the log | The signature could not be verified. The token came from a different realm than the discovery document, or it was altered. | Point `FASTMCP_SERVER_AUTH_CONFIG_URL` at the realm that issues the tokens. |
| `401` with `audience mismatch` in the log | The token's `aud` does not contain `FASTMCP_SERVER_AUTH_AUDIENCE`. | Add the audience mapper ([Step 3](#step-3-add-the-audience-mapper-required)) and confirm the sign-in or exchange requested the audience scope ([Step 3](#step-3-make-the-mcp-audience-available-to-the-calling-client)). |
| Exchange fails with `Requested audience not available` | The calling client cannot reach the MCP audience. | Attach the audience client scope to the calling client as Optional and name it in the `scope` parameter ([Step 3](#step-3-make-the-mcp-audience-available-to-the-calling-client)). |
| Sign-in or exchange fails with `400` `invalid_scope` | A requested scope is not attached to the calling client. | Attach the scope to the calling client as Optional ([Step 3](#step-3-make-the-mcp-audience-available-to-the-calling-client)). |
| Exchange fails with `access_denied` and `Client is not within the token audience` | The user's token was issued to a different client and does not list the calling client in its `aud` claim. | Exchange a token issued to the calling application's client ([Exchange the User's Token](#exchange-the-users-token)). |
| Exchange fails with `invalid_client` and `Audience not found` | The `audience` value is not the Client ID of a client in the realm. | Use the MCP client's Client ID, which must also be the Included Custom Audience ([Step 3](#step-3-add-the-audience-mapper-required)). |
| `401`, with an ERROR naming `username`, `preferred_username`, and `email` in the log | The token carries no username claim and `user_impersonation` is `true`. | Keep the `profile` client scope assigned as Default ([Step 4](#step-4-make-sure-the-token-carries-a-username)), or set `user_impersonation: false` for machine callers. |
| Service-account token authenticates but every query fails at the database | The server impersonates `service-account-<client-id>`, which has no database account. | Set `user_impersonation: false` for deployments that serve machine callers. |
| `403` `insufficient_scope` from a target URL | The token has no read grant for that target, or the target does not exist. The two are deliberately identical. | Attach the per-target scope to the calling client and request it at sign-in or in the exchange, or correct the host, instance, or database in the URL. See [What a Caller Without a Grant Sees](#what-a-caller-without-a-grant-sees). |
| A request without a token does not return `401`, or `/mcp/authorize` returns a login page | `auth_mode` is not at the top level of `conf.json`, for example because it is inside the `oauth` block. The server runs the OAuth login proxy, or, when the `oauth` block has no client ID, without authentication. The log then says `server will run without authentication`. | Move `auth_mode` to the top level, restart, and confirm that a request without a token returns `401`. |
| Requests return `401` for a short time after Keycloak starts signing with a new key | The server fetches the realm's key set again as soon as it sees an unknown key, but at most once every 30 seconds. | Nothing; the server recovers on its own within 30 seconds. |

!!! note "Revocation takes effect at token expiry"
    Tokens are verified locally against the realm's signing keys, with no introspection call. A revoked session or grant stops working when the access token expires. Keep **Access Token Lifespan** short (see [Token Expiration](#token-expiration)).


## Keycloak Versus Auth0: Key Differences

| Aspect | Auth0 | Keycloak |
|--------|-------|----------|
| **Provider class** | Dedicated Auth0 support in FastMCP | Generic `OIDCProxy` (standard OIDC) |
| **Audience** | Separate API Identifier (often a URL) | Configured through **Included Custom Audience** in the audience mapper (typically set to the Client ID) |
| **`sub` claim** | `auth0\|<id>` or `google-oauth2\|<id>` | UUID by default (can override to username) |
| **`preferred_username`** | Not always present | Always present by default |
| **Discovery URL format** | `https://<domain>/.well-known/openid-configuration` | `http://<host>/realms/<realm>/.well-known/openid-configuration` |
| **Self-hosted** | No (SaaS only) | Yes (self-hosted or cloud) |
| **Token lifetime config** | API Settings > Token Expiration | Realm Settings > Tokens|
| **`mcp:write` model** | An API permission granted through a role, so it can be withheld from individual users | An optional client scope attached to the client, so any user of that client can request it. Control writes with database privileges instead |


## Staging Versus Production

| Environment | Recommendation |
|---|---|
| **Development** | Enable direct access grants for `curl`-based testing. |
| **Staging / Production** | Deploy Keycloak behind HTTPS. Always use HTTPS for `CONFIG_URL`, `BASE_URL`, and callback URLs. Use a strong `CLIENT_SECRET`. **Disable direct access grants**. Change default admin credentials. |



