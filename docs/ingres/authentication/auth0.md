---
title: Auth0 Setup Guide
description: Step-by-step guide to configure Auth0 as the OAuth identity provider for the Actian MCP Server.
---

# Configuring Auth0

Set up an Auth0 application and API to enable OAuth 2.0 and OpenID Connect (OIDC) authentication for your Actian MCP Server. After you complete these steps, you can see the credentials required for the `oauth` block in the `conf.json` configuration file.

For details on shared security concepts like TLS and user impersonation, see [Authentication Overview](index.md).


!!! info "Reference"
    [FastMCP Auth0 Integration](https://gofastmcp.com/integrations/auth0)


## Quick Start

The checklist below is the whole procedure in brief. Use it if you are already familiar with the Auth0 Dashboard. Otherwise, work through the numbered steps that follow, which give the full navigation for each item.

1. **Create an API:** Navigate to **Applications** > **APIs** > **Create API**. The **Identifier** serves as the `FASTMCP_SERVER_AUTH_AUDIENCE`. On the API's **Settings** tab, enable both **RBAC Settings** toggles.
2. **Create an Application:** Navigate to **Applications** > **Applications** > **Create Application**. Select **Regular Web Applications**. Copy the **Client ID** and **Client Secret**.
3. **Authorize the Application:** In your API's **Application Access** tab, select `mcp:write` under both **User-Delegated Access** and **Client Access** for your application.

    !!! warning
        If you skip this step, Auth0 returns an `invalid_request` error.

4. **Enable Authorization Code Grant:** In **Advanced Settings** > **Grant Types**, select **Authorization Code**.
5. **Set Callback URLs:** Add `<BASE_URL>/auth/callback` to **Allowed Callback URLs**.
6. **Add the write scope**, if `query_mode` is `read-write` and the deployment does not serve more than one server or database: define the `mcp:write` permission on the API, then grant it to users through a role. For a multi-target deployment, grant per-target permissions instead; see [Multi-Target Deployments: Per-Target Permissions](#multi-target-deployments-per-target-permissions). See [Step 1.1](#step-11-add-the-write-scope-read-write-deployments-only) and [Step 4.3](#step-43-grant-the-write-scope-read-write-deployments-only).
7. **Update Configuration:** Add your Auth0 domain and credentials to `conf.json`.
8. **Restart the container:** Restart it so it loads the updated `conf.json`. The container image already serves HTTP, so no transport flag is needed. See [Getting Started: Step 3](../../get-started/index.md#step-3-start-the-container).

!!! tip "Multi-target and resource-server deployments"
    If your `conf.json` has a `targets` block, also follow [Multi-Target Deployments: Per-Target Permissions](#multi-target-deployments-per-target-permissions). If your own application signs users in and calls the server with an Auth0 access token, follow [Resource-Server Mode](#resource-server-mode), which replaces Steps 2 and 5.


## Prerequisites

- An Auth0 account ([sign up free](https://auth0.com/signup)).
- An Auth0 **Tenant** (created automatically on sign-up, for example, `dev-abc123`). Every API, Application, and user you create below lives inside this tenant, and its domain (for example, `dev-abc123.us.auth0.com`) becomes part of the `FASTMCP_SERVER_AUTH_CONFIG_URL` you set in `conf.json`.
- Actian MCP Server installed and ready to run.


## Step 1: Create an Auth0 API

The **API** represents the Actian MCP Server as a protected resource in Auth0. Tokens issued by Auth0 include the API's identifier as the `audience` claim.

1. Log in to the [Auth0 Dashboard](https://manage.auth0.com/).
2. In the left sidebar, navigate to **Applications** > **APIs**.
3. Select **+ Create API**.
4. Fill the form as follows:

     | Field | Value | Notes |
     |-------|-------|-------|
     | **Name** | `Actian MCP Server` | Display name (any descriptive string). |
     | **Identifier (Audience)** | `https://<mcp-server-host>:8000/mcp` | Logical identifier (may not be a reachable URL). This becomes your `FASTMCP_SERVER_AUTH_AUDIENCE`.  |
     | **Signing Algorithm** | `RS256` | Default, leave the value as is. |

5. Select **Create**.
6. On the new API, select the **Settings** tab and scroll to **RBAC Settings**.
7. Enable both of the following:

     | Setting | Why it is needed |
     |---------|------------------|
     | **Enable RBAC** | Auth0 evaluates role and permission assignments during login. |
     | **Add Permissions in the Access Token** | Auth0 adds the granted permissions to the access token, in the `permissions` claim, where the server reads them. Available only after you enable RBAC. |

8. Select **Save**.

These settings are needed for the `mcp:write` scope and for per-target scopes in a multi-target deployment. They do not affect a read-only, single-database deployment, so enabling them now means you do not have to return to this page later.

### Output of Step 1

| Config Field | Where to find it |
|---|---|
| `FASTMCP_SERVER_AUTH_AUDIENCE` | The **Identifier** that you entered, for example, `https://<mcp-server-host>:8000/mcp`. |

### Step 1.1: Add the Write Scope (Read-Write Deployments Only)

Skip this step if `query_mode` is `read-only`. A read-only server never requests the `mcp:write` scope.

Also skip it for a multi-target deployment with more than one server or more than one database. There, `mcp:write` does not apply: each write needs the target's `actian:{host}:{instance}:{database}:write` permission instead. See [Multi-Target Deployments: Per-Target Permissions](#multi-target-deployments-per-target-permissions).

When `query_mode` is `read-write`, the server requests `mcp:write` and rejects any write whose token does not carry it. For more information, see [Write support](../write-support.md).

1. Open your API, for example `Actian MCP Server`, and select the **Permissions** tab.
2. Under **Add a Permission**, enter the following and select **+ Add**:

     | Field | Value |
     |-------|-------|
     | **Permission** | `mcp:write` |
     | **Description** | `Write access` |

3. Confirm that both **RBAC Settings** toggles are enabled on the **Settings** tab, as described in [Step 1](#step-1-create-an-auth0-api).

!!! note "Defining the permission does not grant it"
    At this point `mcp:write` exists on the API, but no user holds it yet. Assign it to users through a role in [Step 4.3](#step-43-grant-the-write-scope-read-write-deployments-only).


## Step 2: Create an Auth0 Application

The **Application** represents the MCP server's OAuth client. It holds `client_id` and `client_secret` used during the OAuth handshake.

!!! note "Why Regular Web Application?"
    The MCP server runs the browser sign-in for its users and holds a client secret, which is the Regular Web Application pattern. MCP clients such as Visual Studio Code and Claude Desktop sign in through the MCP server and never talk to Auth0 directly. Do not use **Single Page Application** or **Native**, which cannot hold a client secret, or **Machine to Machine**, which Auth0 intends for client-credentials callers without a browser sign-in.

1. In the Auth0 Dashboard, navigate to **Applications** > **Applications**.
2. Select **+ Create Application**.
3. Enter the values for the following fields:

     | Field | Value |
     |-------|-------|
     | **Name** | `Actian MCP Server App` |
     | **Application Type** | Regular Web Applications |

4. Select **Create**.
5. The application's **Quickstart** tab opens. Authorize the application for your API in [Step 3](#step-3-authorize-the-application-for-the-api).

### Configure Application Settings

On the **Settings** tab, configure the following:

| Setting | Value | Notes |
|---------|-------|-------|
| **Allowed Callback URLs** | `https://<mcp-server-host>:8000/auth/callback` | Must exactly match `<BASE_URL>/auth/callback`. Multiple URLs can be comma-separated. |
| **Allowed Logout URLs** | `https://<mcp-server-host>:8000` | (Optional) For logout redirect |
| **Allowed Web Origins** | `https://<mcp-server-host>:8000` | (Optional) For CORS |

!!! warning "Callback URL must match exactly"
    The **Allowed Callback URLs** value must match `<FASTMCP_SERVER_AUTH_BASE_URL>/auth/callback` exactly, including scheme (`http` or `https`), host, and port. A mismatch causes Auth0 to reject the login with a `redirect_uri_mismatch` error.

Select **Save Changes**.

### Configure Grant Types

Regular Web Applications have **Authorization Code** enabled by default, but always verify, since some tenants or configurations differ.

1. On the **Settings** tab, select **Show Advanced Settings**.
2. Select the **Grant Types** tab.
3. Enable **Authorization Code** (required for the browser-based OAuth login flow).
4. Optionally enable **Refresh Token** for token refresh support.
5. Select **Save Changes**.

!!! warning "Authorization Code grant is required"
    Without **Authorization Code** enabled, Auth0 returns `Grant type 'authorization_code' not allowed for the client`. This grant type is enabled by default for Regular Web Applications. If it is not, enable it.

### Output of Step 2

All values appear on the **Settings** tab of your application:

| Config Field | Where to find it in Auth0 |
|---|---|
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | **Client ID** (at the top of the Settings tab) |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | **Client Secret** (click the eye icon to reveal) |
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | Constructed from **Domain**: `https://<your-domain>/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_BASE_URL` | MCP server's external URL, for example, `https://<mcp-server-host>:8000`. |

!!! tip "Finding the Domain"
    The **Domain** is shown at the top of the Settings tab, for example, `dev-abc123.us.auth0.com`. The OIDC discovery URL is always `https://<domain>/.well-known/openid-configuration`.


## Step 3: Authorize the Application for the API

!!! warning "This step is critical"
    Auth0 requires an explicit grant between an application and an API before it issues tokens. Without this authorization, token requests fail with `invalid_request`.

!!! note "Authorizing means selecting permissions"
    Authorizing the application means selecting, from a permission checklist, which of the API's permissions (in this guide, just `mcp:write`, defined in [Step 1.1](#step-11-add-the-write-scope-read-write-deployments-only)) the application is allowed to request. If your API defines no permissions yet, the checklist is empty and there is nothing to select — that is expected for read-only deployments.

You can authorize from either the application's APIs tab or the API's Application Access tab:

**Option A - Authorize from Application:**

1. Navigate to **Applications** > **Applications** > **your app** > **APIs** tab. For example, `Actian MCP Server App`.
2. Select your API from the list. For example, `mcp_server` with the identifier `https://<mcp-server-host>:8000/mcp`.
3. On the **User-Delegated Access** tab, select `mcp:write` from the permission checklist (or **Select: All**), then select **Save**.
4. Switch to the **Client Access** tab, select `mcp:write` from its own permission checklist the same way, then select **Save**.

**Option B - Authorize From API:**

1. Navigate to **Applications** > **APIs** > **your API**. For example, `mcp_server`.
2. Select the **Application Access** tab.
3. Select your application from the list. For example, `Actian MCP Server App`.
4. Authorize both **User-Delegated Access** and **Client Access** as described in Option A, steps 3-4.

After saving, the application row on the **Application Access** tab shows a green checkmark and "1 / 1 permissions granted" under both **User-Delegated Access** and **Client Access**.

!!! important "User-Delegated Access is required for user impersonation"
    If you plan to use `user_impersonation: true`, the application must be authorized for **User-Delegated Access**. Without it, Auth0 will not issue tokens with user identity claims (email, sub) during the Authorization Code flow, and the MCP server will not be able to extract a database username.

!!! note "This is not the same as granting the scope to a user"
    Authorizing the application here means it is *allowed to request* `mcp:write` — not that any particular user's token will carry it. With **Enable RBAC** on (enabled in [Step 1](#step-1-create-an-auth0-api)), whether a specific user's token actually includes `mcp:write` depends on that user holding it through a role, which is a separate, per-user assignment in [Step 4.3](#step-43-grant-the-write-scope-read-write-deployments-only). Both steps are required for read-write deployments.


## Step 4: Create Auth0 Users (If Using User Impersonation)

If `user_impersonation` is `true`, the authenticated user's identity is forwarded to the database through `SET SESSION AUTHORIZATION`. Each Auth0 user must have a matching database account. For more information, see [User Impersonation](index.md#user-impersonation).

### Step 4.1: Create the User in Auth0

1. In the Auth0 Dashboard, navigate to **User Management** > **Users**.
2. Select **+ Create User**.
3. Enter the values for the following fields:

     | Field | Value | Notes |
     |-------|-------|-------|
     | **Email** | `jdoe@example.com` | Value before `@` (`jdoe`) becomes the database username |
     | **Password** | A secure password | Used for Auth0 login |
     | **Connection** | `Username-Password-Authentication` | Default database connection |

4. Select **Create**.

!!! important "Database username = email prefix"
    The MCP server extracts the database username from the **email prefix** (the value before `@`). For example, `jdoe@example.com` > `jdoe`. Ensure the email prefix exactly matches the database account name.

    **Auth0 default behaviour**: Auth0's userinfo endpoint does not return a `username` or `preferred_username` claim by default. In practice, the server uses the **email prefix** as the database username. Always create database users to match this email prefix.

!!! note "Case sensitivity"
    If the database is case-sensitive, for example, `jdoe` ≠ `Jdoe`, ensure the email prefix exactly matches the database account name.

### Step 4.2: Create the Matching Database User

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
    If users sign in through Google, Microsoft Entra, SAML, or corporate SSO through Auth0, the `sub` claim looks like `google-oauth2|12345`. The server removes the provider prefix, leaving `12345`, which is unlikely to match a database account. For SSO setups, set `user_impersonation` to `false` unless you can ensure the Auth0 user profile contains a matching username.

### Step 4.3: Grant the Write Scope (Read-Write Deployments Only)

Skip this step if `query_mode` is `read-only`, or if you skipped [Step 1.1](#step-11-add-the-write-scope-read-write-deployments-only) for a multi-target deployment.

Defining `mcp:write` on the API in [Step 1.1](#step-11-add-the-write-scope-read-write-deployments-only) does not give it to anyone. Auth0 issues the scope only to users who hold it through a role, so grant it to each user who is allowed to write.

1. In the Auth0 Dashboard, navigate to **User Management** > **Roles**.
2. Select **+ Create Role**, name it, for example `MCP Writer`, and select **Create**.
3. On the role's **Permissions** tab, select **Add Permissions**.
4. Select your API, for example `Actian MCP Server`, select the `mcp:write` permission, and add it.
5. On the role's **Users** tab, select **Add Users** and assign the users who are allowed to write.

Users without this role can still read. Their tokens do not carry `mcp:write`, so the server rejects their writes. Because the permission is granted per user, a user cannot obtain the scope by asking for it. Keycloak works differently, so if you also run Keycloak, see [which users can obtain the scope](keycloak.md#user-eligibility) there.

!!! warning "The database still decides what a user can change"
    The `mcp:write` scope permits write statements in general. It does not grant table privileges. With `user_impersonation` enabled, each write also runs as that user's own database account, so grant the matching `INSERT`, `UPDATE`, and `DELETE` privileges in the database as well. See [Step 4.2](#step-42-create-the-matching-database-user).


## Step 5: Assemble the Final Configuration

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
    If `FASTMCP_SERVER_AUTH_AUDIENCE` is omitted, the server uses `FASTMCP_SERVER_AUTH_CLIENT_ID` as the audience. This is common for Keycloak setups, but for Auth0 you should always set an explicit audience, the Client ID will not match the API Identifier.

!!! note
    The `AUDIENCE` is a logical identifier used for token validation. It may not need be a reachable HTTPS URL.

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
    Replace `<db-host>` with the database server address. In a Docker container, use the host's IP address or `host.docker.internal`(not `localhost` or `127.0.0.1`, which refer to the container itself).

For TLS setup details (certificate generation, Docker deployment, trusting self-signed certs), see [HTTPS / TLS for Remote Deployments](index.md#secure-remote-deployments-with-https-and-tls).

For security best practices (file permissions, `.gitignore`, secrets management), see [Security Best Practices](index.md#security-best-practices).


## Verify End-to-End

After starting the MCP server container with OAuth configured:

1. Open a browser and navigate to your server's `/mcp` endpoint, for example, `https://<your-server-host>:8000/mcp`.
2. You should be **redirected to the Auth0 login page**.
3. Log in with an Auth0 user, for example, the user you created in [Step 4](#step-4-create-auth0-users-if-using-user-impersonation).
4. After logging in, Auth0 redirects you back to the MCP server with a valid token.
5. Check the server logs for `Stored database username: <username>` to confirm user impersonation is active.


## Multi-Target Deployments: Per-Target Permissions

Skip this section if your `conf.json` has no `targets` block. A single-database deployment uses only the `mcp:write` scope from [Step 1.1](#step-11-add-the-write-scope-read-write-deployments-only).

In a multi-target deployment, one server fronts several databases, and each one is reached at its own URL, `https://<mcp-server-host>:8000/mcp/{host}/{instance}/{database}`. Every request to a target URL, read or write, must be covered by a **per-target scope** in the caller's access token. For the deployment model and the `targets` block, see [Multi-Target Deployments](../multi-target.md).

### Scope Grammar

```
actian:{host}:{instance}:{database}:{read|write}
```

| Segment | Must match |
|---------|------------|
| `{host}` | The target's `host` value in `conf.json`, exactly, or `*`. |
| `{instance}` | The target's `instance` value in `conf.json`, exactly, or `*`. |
| `{database}` | One of the target's `databases`, or `*`. |
| Last segment | `read` or `write`. |

- `*` matches exactly one segment. It is not a prefix or suffix wildcard, and it never matches zero or several segments.
- A `write` scope implies `read` for the same host, instance, and database. A writer does not need a separate `read` scope.
- There are no deny scopes. What a caller can reach is exactly the union of the scopes it is granted.

| Scope | Grants |
|-------|--------|
| `actian:db07.example.com:<installation_id>:sales:read` | Read `sales` on that one target. |
| `actian:db07.example.com:<installation_id>:sales:write` | Read **and** write `sales` on that one target. |
| `actian:db07.example.com:<installation_id>:*:read` | Read every database on that target. |
| `actian:*:*:*:read` | Read every database on every target. |

!!! warning "Treat host wildcards as break-glass grants"
    A scope with `*` in the `{host}` segment, such as `actian:*:*:*:write`, reaches every target. Keep it out of default roles. The server writes a `WARNING` log line every time such a scope authorizes a request, naming the scope and the target, so its use is visible in audit review.

### Which Scope Authorizes a Write

The single-target `mcp:write` scope and the per-target scopes are mutually exclusive. They are never combined, and which model applies is not a per-request choice:

| Request | Read requires | Write requires |
|---------|---------------|----------------|
| No `targets` block in `conf.json` | A valid token. | `mcp:write`. |
| A target URL, `/mcp/{host}/{instance}/{database}` | A matching `actian:…:read` or `actian:…:write` scope. | A matching `actian:…:write` scope. `mcp:write` is ignored, even if the token carries it. |

In both cases, writes are still possible only when `query_mode` allows them. See [Write support](../write-support.md).

!!! note "`mcp:write` and multi-target deployments"
    `mcp:write` does not apply to a multi-target deployment with more than one server or more than one database: every request goes to a target URL and needs a per-target scope. The only exception is a `targets` block with exactly one server and one database. Its plain `/mcp` path still works and follows the single-database rule, so writes there require `mcp:write`. Requests to its target URL follow the per-target rule.

!!! note "Writes are refused when scope checking is off"
    If `allow_unscoped_reads` is set to `true` (intended only for testing routing before OAuth is in place), reads on target URLs are allowed without a grant, but writes on target URLs are refused. The server does not fall back to `mcp:write` for them.

### Step 1: Define the Per-Target Permissions on the API

Auth0 permissions are plain strings, so each scope you intend to grant becomes one permission. Define the specific combinations your roles need, including any wildcard forms, not every possible combination.

1. Navigate to **Applications** > **APIs** > **your API**, for example `Actian MCP Server`, and select the **Permissions** tab.
2. Under **Add a Permission**, add one entry per scope, for example:

     | Permission | Description |
     |------------|-------------|
     | `actian:db07.example.com:<installation_id>:sales:read` | Read access to sales |
     | `actian:db07.example.com:<installation_id>:sales:write` | Read and write access to sales |
     | `actian:db07.example.com:<installation_id>:*:read` | Read access to every database on db07 |

3. Select **+ Add** for each entry.

### Step 2: Confirm RBAC on the API

RBAC is required for a multi-target deployment, not optional. The set of possible per-target scopes is unbounded, so the server cannot advertise them for MCP clients to request. Auth0 delivers the grants instead, in the access token's `permissions` claim, which the server reads together with `scope` and `scp`.

1. On your API, select the **Settings** tab and scroll to **RBAC Settings**.
2. Confirm that both **Enable RBAC** and **Add Permissions in the Access Token** are enabled, as described in [Step 1](#step-1-create-an-auth0-api). If they are not, enable them and select **Save**.

!!! warning "Requesting a scope does not grant it"
    Auth0 silently drops a requested scope that is not a permission granted to the caller. The token is still issued, the scope is simply absent, and nothing reports an error. A per-target scope reaches the token only when it is defined on the API (Step 1) **and** granted (Step 3 or Step 4).

### Step 3: Grant Permissions to Users Through Roles

1. Navigate to **User Management** > **Roles**.
2. Select **+ Create Role**, give it a name, for example `sales-readonly`, and select **Create**.
3. On the role's **Permissions** tab, select **Add Permissions**, select your API, select the per-target permissions the role should hold, and add them.
4. On the role's **Users** tab, select **Add Users** and assign the users.

You can also assign roles from the user's side: **User Management** > **Users** > **the user** > **Roles** tab > **Assign Roles**.

### Step 4: Grant Permissions to Machine-to-Machine Callers

Roles apply to users. An application that calls the server with its own token, using the client credentials grant, receives only the permissions selected for it on the **Client Access** tab:

1. Navigate to **Applications** > **Applications** > **the calling application** > **APIs** tab.
2. Select your API.
3. On the **Client Access** tab, select the per-target permissions, then select **Save**.

!!! warning "Client Access and User-Delegated Access look identical"
    The two tabs show the same permission checklist. **User-Delegated Access** controls what the application may request on behalf of a signed-in user. **Client Access** controls what a client credentials token carries. Selecting permissions on the wrong tab leaves them out of the token without any error.

Client credentials tokens carry no user identity, so callers of this kind are used with `user_impersonation` set to `false`, in [Resource-Server Mode](#resource-server-mode).

### What a Caller Without a Grant Sees

A request to a target URL that the token has no read grant for is refused with HTTP `403` and the error `insufficient_scope`. The `WWW-Authenticate` response header names the scope that would be required, for example:

```
WWW-Authenticate: Bearer error="insufficient_scope",
    error_description="Required scope: actian:db07.example.com:<installation_id>:sales:read",
    scope="actian:db07.example.com:<installation_id>:sales:read", ...
```

A request for a target that does not exist receives the identical response, so the response never reveals which targets are configured. Check the target URL as well as the grants.

!!! note "Behind the OAuth login proxy, sign in again after granting"
    Some MCP clients react to this response by starting a new login that asks for the missing scope (step-up). With the server's OAuth login proxy, which this guide sets up, that new login cannot obtain the scope: the browser shows an authorization error such as `Client was not registered with scope ...`. This is expected. Grant the permission or role in Auth0 ([Step 3](#step-3-grant-permissions-to-users-through-roles)), then sign in again.

!!! tip "Discover what a token can reach"
    After connecting, call the `list_accessible_targets` tool. It lists the targets and databases the caller holds a read grant for, with the URL path of each.

!!! note "Revoking a permission"
    Removing a permission or role in Auth0 does not invalidate tokens that were already issued. Access ends when the token expires. See [Token Expiration](#token-expiration).


## Resource-Server Mode

Use resource-server mode when your own application already signs users in through Auth0 and calls the MCP server with the user's Auth0 access token. The MCP server runs no login of its own and holds no client ID or secret. It only verifies each token against your Auth0 tenant's published signing keys and runs each call as the user named in the token.

Generic MCP clients, such as Visual Studio Code or Claude Desktop, keep using the login proxy described in the rest of this guide. One deployment runs one mode. For the mode itself, independent of the identity provider, see [Resource-Server Mode](resource-server.md).

| | OAuth login proxy (default) | Resource-server mode |
|---|---|---|
| Who signs the user in | The MCP server | Your application |
| Tokens accepted | Only tokens the MCP server issued | Auth0 access tokens carrying the MCP API audience |
| Client ID and secret in `conf.json` | Required | Not used |
| Auth0 Application for the server ([Step 2](#step-2-create-an-auth0-application)) | Required | Not used. Your application is the Auth0 client. |

### Step 1: Create the API

Create the API as described in [Step 1: Create an Auth0 API](#step-1-create-an-auth0-api). Its **Identifier** is the `FASTMCP_SERVER_AUTH_AUDIENCE`. If you use `mcp:write` or per-target scopes, define them on this API as in [Step 1.1](#step-11-add-the-write-scope-read-write-deployments-only) and [Multi-Target Deployments: Per-Target Permissions](#multi-target-deployments-per-target-permissions).

### Step 2: Configure the Calling Application

The calling application is an Auth0 application of its own. For an application that signs users in through a browser and holds a client secret, create it as a **Regular Web Applications** type, as in [Step 2: Create an Auth0 Application](#step-2-create-an-auth0-application).

1. Authorize your calling application for the API, as in [Step 3: Authorize the Application for the API](#step-3-authorize-the-application-for-the-api). Use **User-Delegated Access** for user logins, and **Client Access** for client credentials callers.
2. Have the application request the API **Identifier** as its `audience` when it obtains a token, for example on its `/authorize` request. Auth0 then issues an access token whose `aud` claim contains the identifier.

!!! note "No token exchange step on Auth0"
    The application requests the MCP API audience directly, at login or with a refresh token grant that names that audience. There is no token exchange to configure and no exchange permission to grant.

### Step 3: Enable RBAC and Grant Permissions

Confirm that **Enable RBAC** and **Add Permissions in the Access Token** are enabled on the API, as described in [Step 1](#step-1-create-an-auth0-api), and grant the permissions:

- **Users**: through roles, as in [Step 3: Grant Permissions to Users Through Roles](#step-3-grant-permissions-to-users-through-roles).
- **Client credentials callers**: on the application's **Client Access** tab, as in [Step 4: Grant Permissions to Machine-to-Machine Callers](#step-4-grant-permissions-to-machine-to-machine-callers).

The same applies to `mcp:write` for writes in a deployment without a `targets` block. In this mode the server advertises no scopes for clients to request. Auth0 delivers granted permissions in the `permissions` claim.

### Step 4: Add the Username to the Access Token with an Action

Skip this step if `user_impersonation` is `false`.

With `user_impersonation` set to `true` (the default), the server reads the database user name from the access token itself. It checks these claims, in order:

1. `username`
2. `preferred_username`
3. `email` (the part before `@`)

In this mode there is no userinfo lookup and no fallback to `sub`. A token that carries none of the three claims is rejected with `401`, and the reason is written to the server log, not to the response. Auth0 does not put these claims on an access token by default, so add them with a Post-Login Action.

1. Navigate to **Actions** > **Library** > **Build Custom**.
2. Enter a **Name**, for example `mcp-username-claim`, select the **Login / Post Login** trigger, and select **Create**.
3. Replace the code with the following:

    ```js
    exports.onExecutePostLogin = async (event, api) => {
      const name = event.user.username || event.user.nickname || event.user.email;
      api.accessToken.setCustomClaim('username', name);
    };
    ```

4. Select **Deploy**.
5. Navigate to **Actions** > **Triggers** > **Post-Login**.
6. Drag the `mcp-username-claim` Action from the panel on the right into the flow.
7. Select **Apply**.

!!! important "The claim name must not be namespaced"
    The server matches only the bare claim names `username`, `preferred_username`, and `email`. A namespaced claim such as `https://example.com/username` is not matched, and a token carrying only that claim is rejected. Auth0 accepts the bare `username` claim on an access token for a custom API when it is set with `api.accessToken.setCustomClaim`.

!!! important "The claim value is the database user name"
    The `username` claim is used as is, so its value must equal the user's database account name. The example takes the first of the Auth0 user's `username`, `nickname`, or `email` that is set. If that value can be an email address, or does not match the database account, change the Action to set the exact database user name. Database user names may be case sensitive.

!!! note "Auth0 dashboard naming"
    Auth0 renamed **Actions** > **Flows** to **Actions** > **Triggers**. Older Auth0 documentation that refers to **Flows** > **Login** describes the same Post-Login trigger.

### Step 5: Configure `conf.json`

Set `auth_mode` at the **top level** of `conf.json`, not inside the `oauth` block. The `oauth` block needs three keys and no client ID or secret:

| Key | Location | Value |
|-----|----------|-------|
| `auth_mode` | Top level | `resource-server` |
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `oauth` | `https://<your-tenant>.us.auth0.com/.well-known/openid-configuration` |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | `oauth` | The API **Identifier**. Required in this mode: there is no client ID to fall back to. |
| `FASTMCP_SERVER_AUTH_BASE_URL` | `oauth` | The MCP server's public URL, for example `https://<mcp-server-host>:8000`. |
| `user_impersonation` | `oauth` | `true` (default) for user tokens. `false` for client credentials callers. |

```json
{
    "driver": "{Ingres}",
    "server": "@<db-host>,tcp_ip,<installation_id>",
    "database": "mydb",
    "database_user": "<database_user>",
    "database_password": "<database_password>",
    "host": "0.0.0.0",
    "port": 8000,
    "query_mode": "read-only",
    "ssl_certfile": "/app/server.crt",
    "ssl_keyfile":  "/app/server.key",
    "auth_mode": "resource-server",
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://<your-tenant>.us.auth0.com/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "<your-api-identifier>",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp-server-host>:8000",
        "user_impersonation": true
    }
}
```

For a multi-target deployment, replace the single-database keys with a `targets` block, as described in [Multi-Target Deployments](../multi-target.md). The `auth_mode` and `oauth` settings stay the same.

- On a host other than `localhost`, TLS is required: set `ssl_certfile` and `ssl_keyfile`, and use `https://` in `FASTMCP_SERVER_AUTH_BASE_URL`. See [HTTPS / TLS for Remote Deployments](index.md#secure-remote-deployments-with-https-and-tls).
- If any of the three `oauth` keys is missing, the server refuses to start and names the missing key. It never starts unauthenticated in this mode.
- `FASTMCP_SERVER_AUTH_CLIENT_ID`, if present, is ignored, and the server logs a warning.

Start the container as described in [Deploy the Docker](index.md#step-3-deploy-the-docker), for example:

```bash
docker run -p 8000:8000 \
  -v /path/to/server.crt:/app/server.crt:ro \
  -v /path/to/server.key:/app/server.key:ro \
  -v /path/to/conf.json:/app/conf.json:ro \
  actian/ingres-mcp-server:1.2.0
```

### Step 6: Verify the Deployment

**Decode a user's access token.** Obtain an access token through your application's login, store it in `TOKEN`, and decode its payload:

```bash
python3 -c 'import sys, json, base64; p = sys.argv[1].split(".")[1]; p += "=" * (-len(p) % 4); print(json.dumps(json.loads(base64.urlsafe_b64decode(p)), indent=2))' "$TOKEN"
```

Check the following claims:

| Claim | Expected value |
|-------|----------------|
| `iss` | Your tenant, for example `https://<your-tenant>.us.auth0.com/`. It must match the `issuer` in the discovery document. |
| `aud` | Contains the API **Identifier**, exactly as in `FASTMCP_SERVER_AUTH_AUDIENCE`. |
| `username` | The user's database account name. Required when `user_impersonation` is `true`. |
| `permissions` | The `mcp:write` or `actian:…` permissions the user was granted. |

!!! tip "Do not paste production tokens into online decoders"
    An access token is a credential until it expires. Decode it locally, as shown above.

**Check the server.** Set `BASE` to the server URL, for example `https://<mcp-server-host>:8000`:

```bash
# The protected-resource metadata names your Auth0 tenant
curl -s "$BASE/.well-known/oauth-protected-resource/mcp"

# The server runs no login: both return 404
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp/authorize"
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp/oauth/token"

# Without a token: 401
curl -s -o /dev/null -w '%{http_code}\n' "$BASE/mcp"

# With the token: not 401
curl -s -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" "$BASE/mcp"
```

With `user_impersonation` set to `true`, the server log shows `Stored database username (strict claim mode): <username>` for an accepted token.

### Resource-Server Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Server refuses to start, naming an `oauth` key | `FASTMCP_SERVER_AUTH_CONFIG_URL`, `FASTMCP_SERVER_AUTH_AUDIENCE`, or `FASTMCP_SERVER_AUTH_BASE_URL` is missing or empty. | Set all three. No client ID or secret is used. |
| `401`, with `audience mismatch` in the server log | The token's `aud` does not contain `FASTMCP_SERVER_AUTH_AUDIENCE`. | Make the application request the API **Identifier** as its `audience`, and make the configured value identical to the Identifier. |
| `401`, with `issuer mismatch` in the server log | The signature is valid, but the token's `iss` differs from the issuer in the discovery document. This happens when the same tenant is reached under a different custom domain. | Point `FASTMCP_SERVER_AUTH_CONFIG_URL` at the domain that matches the `iss` in your tokens. |
| `401`, with only `invalid_token` in the server log | The signature could not be verified. The token came from a different tenant than the discovery document, or it was altered. | Point `FASTMCP_SERVER_AUTH_CONFIG_URL` at the tenant that issues the tokens. |
| `401`, with an ERROR naming `username`, `preferred_username`, and `email` in the server log | `user_impersonation` is `true` and the token carries none of these claims. | Add the Post-Login Action in [Step 4](#step-4-add-the-username-to-the-access-token-with-an-action) and make sure it is in the **Post-Login** trigger. Use a bare claim name. |
| `401` for a client credentials token | Client credentials tokens carry no user claim. | Set `user_impersonation` to `false` for the deployment that serves machine callers. |
| Queries run as an unexpected user, or the database rejects the user | The `username` claim does not equal the database account name. | Change the Action to set the exact database user name. |
| `403` `insufficient_scope` on a target URL | The token has no grant for that target, or the target does not exist. The `scope` in `WWW-Authenticate` names the required scope. | Grant the permission (see [Multi-Target Deployments: Per-Target Permissions](#multi-target-deployments-per-target-permissions)), have the application obtain a new token, or correct the target URL. |
| Granted scopes missing from `permissions` | RBAC or **Add Permissions in the Access Token** is off; the permission is not defined on the API; the user lacks the role; or, for client credentials, the permission was selected on **User-Delegated Access** instead of **Client Access**. | Enable both RBAC settings, define the permission, assign the role, and for client credentials callers select the permission on the **Client Access** tab. Then obtain a new token. |
| A request without a token does not return `401`, or `/mcp/authorize` returns a login page | `auth_mode` is not at the top level of `conf.json`, for example because it is inside the `oauth` block. The server runs the login proxy, or, when the `oauth` block has no client ID, without authentication. The log then says `server will run without authentication`. | Move `auth_mode` to the top level, restart, and confirm that a request without a token returns `401`. |


## Troubleshooting

### Verify OIDC Discovery Endpoint

```bash
curl https://dev-abc123.us.auth0.com/.well-known/openid-configuration \
  | python3 -m json.tool
```

You should see `issuer`, `authorization_endpoint`, `token_endpoint`, `jwks_uri`, and similar.

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Grant type 'authorization_code' not allowed` | The application is missing the Authorization Code grant. | Enable **Authorization Code** in Advanced Settings > Grant Types. See [Configure Grant Types](#configure-grant-types). |
| `invalid_request` when requesting a token | Application not authorized for the API. | [Step 3](#step-3-authorize-the-application-for-the-api) - authorize the application. |
| `audience mismatch` | `FASTMCP_SERVER_AUTH_AUDIENCE` does not match the API Identifier. | Ensure they are identical strings. |
| `invalid_client` | Wrong `client_id` or `client_secret`. | Re-copy from Application > Settings. |
| `KeyError` on startup (for example, `CLIENT_SECRET`). | Some OAuth fields are present but others missing. | Provide **all** required fields or remove `oauth` entirely. |
| `Could not extract username` | Token lacks `username`, `preferred_username`, or `email`. | Add email/profile scopes or set `user_impersonation: false`. |
| `unauthorized` / 401 on every request | OAuth misconfigured or token expired. | Check server logs and verify OIDC discovery URL is reachable. |
| `redirect_uri_mismatch` | Callback URL does not match `<BASE_URL>/auth/callback`. | Fix **Allowed Callback URLs** in Auth0 - scheme, host, and port must match exactly. |
| `ValueError: Issuer URL must be HTTPS` | OAuth without TLS configured. | Add `ssl_certfile`/`ssl_keyfile` and use `https://` for `BASE_URL`. |
| `ValueError: BASE_URL must start with https://` | SSL configured but `BASE_URL` still uses `http://`. | Update `BASE_URL` to `https://`. |
| `ssl.SSLError: PEM lib` | Missing cert/key env vars before Docker start. | Mount cert/key as volumes when starting the container (see [Docker Deployment](index.md#step-3-deploy-the-docker)). |
| `ERR_TLS_CERT_ALTNAME_INVALID` | Certificate missing SAN. | Regenerate with `-addext "subjectAltName=IP:<ip>"`. |
| `TypeError: fetch failed` (VS Code) | Self-signed cert not trusted by `Node.js`. | Launch Visual Studio Code with `NODE_EXTRA_CA_CERTS=/path/to/server.crt code .` |
| `Client Not Registered` (VS Code) | Server's Docker container was recreated, wiping client registrations, but Visual Studio Code caches the old client ID. | Quit Visual Studio Code, then delete stale registrations from the state DB (see [Clearing Visual Studio Code OAuth cache](#clearing-visual-studio-code-oauth-cache) below) and reopen Visual Studio Code. To prevent recurrence, mount a Docker volume for `/root/.local/share/fastmcp`. |
| `Service not found: https://...` / `access_denied` | `AUDIENCE` mismatch between client request and server config (often `http` versus `https`). | Ensure `FASTMCP_SERVER_AUTH_AUDIENCE` in `conf.json` exactly matches the Auth0 API Identifier. |
| Token validation behaves unexpectedly | OIDC endpoint is unreachable at startup. | Restart server after endpoint is accessible. |

### Clearing Visual Studio Code OAuth Cache

If the MCP server's Docker container is recreated, Visual Studio Code's cached OAuth client registration becomes stale. To clear it:

1. Quit Visual Studio Code completely (Cmd+Q on macOS, or close all windows on Linux/Windows).
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

3. Reopen Visual Studio Code. It will re-register with the server automatically.

Replace `<your-server-host>` with your server's IP or hostname, for example, `35.185.60.76`. This only clears the registration for that specific server.

!!! tip "Prevent recurrence"
    Mount a Docker volume for the server's OAuth state, so client registrations survive container recreation:
    ```bash
    docker run ... -v mcp-auth-data:/root/.local/share/fastmcp ...
    ```

### Token Expiration

Auth0 tokens have a configurable lifetime:

1. Navigate to **Applications** > **APIs** > **your API** > **Settings**.
2. Check **Token Expiration (Seconds)**. Default is 86400 (24 hours).
3. Adjust as needed.

!!! note
    Token refresh is handled automatically by the OAuth flow when using browser-based authentication.


## Staging Versus Production

| Environment | Recommendation |
|---|---|
| **Development** | Use a free Auth0 tenant. |
| **Staging / Production** | Use a dedicated Auth0 tenant or separate Application and API. Always use HTTPS for `BASE_URL` and callback URLs. |
