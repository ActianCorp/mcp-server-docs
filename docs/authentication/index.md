---
title: Authentication
description: Enable OAuth 2.0 / OIDC authentication for the Actian MCP Server — configuration reference for every database, user impersonation, TLS setup, and security best practices.
---

# Configuring OAuth 2.0 and OIDC Authentication

The Actian MCP Server supports OAuth 2.0 and OpenID Connect (OIDC) authentication. When you enable this feature, every client request must include a valid JSON Web Token (JWT) issued by a trusted identity provider (IdP).

The SQL engines and Actian NoSQL use different OAuth architectures and different configuration systems. Both are covered below — select your database in the tabs.

!!! note "Deployment Considerations"
    - **Transport requirements**: OAuth only works with network transport such as `sse`, `http`, and `streamable-http`. You cannot use OAuth with the stdio transport, which is used for local IDE integrations like Claude Desktop or Cursor.

## Working with OAuth

=== "SQL databases"

    The Actian MCP Server acts as an `OIDC Relying Party` by redirecting unauthenticated AI clients to the identity provider for secure login and token issuance. Once authenticated, the client includes this bearer token in all subsequent requests, allowing the server to validate the session and securely fulfill database queries.

    ```mermaid
    %%{init: {'theme': 'dark', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'arial'}}}%%
    sequenceDiagram
        participant Client as MCP Client
        participant Server as MCP Server (OIDCProxy)
        participant Browser as Browser
        participant IdP as Identity Provider (Auth0 / Keycloak)

        Client->>Server: Connect (no token)
        Server->>Browser: Redirect to IdP login
        Browser->>IdP: User enters credentials
        IdP->>Browser: Authorization code
        Browser->>Server: Callback with auth code
        Server->>IdP: Exchange code for tokens
        IdP->>Server: Access token + ID token
        Server->>Client: Session established

        loop Every request
            Client->>Server: Request + Bearer token
            Server->>Server: Validate JWT
            Server->>Client: Response
        end
    ```

=== "Actian NoSQL"

    !!! info "Database credentials versus OAuth"
        There are two distinct types of authentication used by the system:

        - **Database credentials:** The `user:password` portion of the NoSQL connection URL (for example, `cars@localhost#admin:secret`) is used to authenticate with the database itself when the server starts.
        - **OAuth 2.0:** This protocol controls access to the MCP Server endpoint.

    Authentication is disabled by default. When enabled, all `/mcp/*` endpoints require a valid Bearer token issued by an OIDC provider. The server acts as an OAuth 2.0 resource server and exposes a resource metadata endpoint at `/.well-known/oauth-protected-resource`. MCP clients use this endpoint to discover the identity provider and initiate the appropriate OAuth flow.

    The server supports two primary flows:

    - **Authorization Code:** Used for interactive clients (such as Claude Desktop, Cursor, and the FastMCP Python client). The client redirects the user to the IdP for login and receives a token after consent.
    - **Client Credentials:** Used for machine-to-machine (M2M) scenarios where no user interaction is possible. The client authenticates directly with the IdP using its own credentials.

    The diagram below illustrates the Authorization Code flow:

    ```mermaid
    %%{init: {'theme': 'dark', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'arial'}}}%%
    sequenceDiagram
        participant Client as MCP Client
        participant Server as MCP Server
        participant IdP as Identity Provider (Auth0 / Keycloak)

        Client->>Server: Connect (no token)
        Server->>Client: 401 WWW-Authenticate Bearer resource_metadata=<br/><mcp_server_url>/.well-known/oauth-protected-resource

        Client->>Server: GET /.well-known/oauth-protected-resource
        Server->>Client: {"authorization_servers": ["<idp_url>"]}

        Client->>IdP: Discover metadata
        Client->>IdP: Login, get authorization code
        IdP->>Client: Authorization code
        Client->>IdP: Exchange code for access token
        IdP->>Client: Access token (JWT)

        loop Every request
            Client->>Server: Request + Bearer token
            Server->>IdP: Get keys (JWKS) / verify token
            IdP->>Server: Token valid
            Server->>Client: Response
        end
    ```

## Configuring OAuth

=== "SQL databases"

    To enable authentication, add an `oauth` object to the `conf.json` file. The server reads the following data during startup:

    | Field | Required | Description |
    | :---- | :------- | :---------- |
    | `FASTMCP_SERVER_AUTH_CONFIG_URL` | Yes | OIDC discovery URL, for example `https://domain/.well-known/openid-configuration`. Use `https://` in production |
    | `FASTMCP_SERVER_AUTH_CLIENT_ID` | Yes | OAuth client ID provided by the identity provider |
    | `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | Yes | OAuth client secret |
    | `FASTMCP_SERVER_AUTH_BASE_URL` | Yes | External URL of the MCP server, for example `https://<mcp-server-host>:8000`. It must use `https://`. |
    | `FASTMCP_SERVER_AUTH_AUDIENCE` | Yes | Token audience |
    | `user_impersonation` | No | Boolean. If `true` (the default setting), the server runs each query as the authenticated user using `SET SESSION AUTHORIZATION`. |

    **Example**

    ```json
    {
      "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://dev-abc123.us.auth0.com/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "wNXUdrp9aBcDeFgHiJkLmN",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "a1B2c3D4e5F6g7H8i9J0kLmNoPqRsTuVwXyZ",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp-server-host>:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "<your-audience>",
        "user_impersonation": true
      }
    }
    ```

    !!! note "Configuration Considerations"
        You must either provide all four required OAuth fields (`CONFIG_URL`, `CLIENT_ID`, `CLIENT_SECRET`, and `BASE_URL`) or none. If you include `CONFIG_URL` and `CLIENT_ID`, and omit `CLIENT_SECRET` or `BASE_URL`, the server fails to start and throws a `KeyError`. To disable OAuth, remove the entire `oauth` block.

=== "Actian NoSQL"

    Authentication is configured through individual properties in `application.properties`, not through a block.

    | Property | Required | Description |
    |---|---|---|
    | `mcp.auth.enabled` | Yes (to enable) | Set to `true` to enable OAuth2 authentication. Disabled by default. |
    | `quarkus.oidc.auth-server-url` | Yes (if enabled) | Issuer URL of your OIDC provider, for example, `https://your-idp.example.com/`. |
    | `quarkus.oidc.sse-tenant.auth-server-url` | No | Overrides the OIDC provider for the SSE endpoint (`/mcp/sse`) only. Defaults to `quarkus.oidc.auth-server-url`. |

    !!! note "Quarkus OIDC configuration"
        The table lists the most common properties. The full set of options is available in the [Quarkus OIDC configuration reference](https://quarkus.io/guides/security-openid-connect-client-reference#configuration-reference).

    Two OIDC tenants are preconfigured:

    | Tenant | Path | Property Prefix |
    |---|---|---|
    | Default | `/mcp/*` | `quarkus.oidc.*` |
    | SSE | `/mcp/sse` | `quarkus.oidc.sse-tenant.*` |

    Both tenants share the same authentication server URL by default. Override the SSE tenant only if that endpoint requires a different identity provider.

    **Example**

    Add the following to your `application.properties` and start the server as instructed in [Start the Server](../nosql/index.md#start-the-server):

    ```properties
    nsql.connectionURL=<connection-url>
    mcp.auth.enabled=true
    quarkus.oidc.auth-server-url=https://your-idp.example.com/
    ```

!!! info "Scopes"
    For read access you do not need to configure specific scopes. The server automatically requests the `openid`, `email`, and `profile` scopes.

    If you set `query_mode` to `read-write`, the server also requests the `mcp:write` scope, and a token without it cannot perform writes. You must define that scope in your identity provider first. See [Write support](../write-support/index.md) for how writes are authorized, and [Auth0](auth0/index.md) or [Keycloak](keycloak/index.md) for the setup steps.

## User Impersonation

=== "SQL databases"

    By default, the `user_impersonation` field is set to `true`. The server extracts a username from the authenticated user's JWT and runs `SET SESSION AUTHORIZATION "<username>"` before executing a database query. This ensures users only interact with data their specific database account is permitted to see.

    Impersonation covers extension-authored tools as well as the built-in ones, so an extension is also bounded by the end user's own database privileges. See [Extensions](../extensions/index.md#statements-run-as-the-end-user).

    |  user_impersonation | Server |
    | :------------------- | :------- |
    | `true` (default) | Verify the `JWT` and run `SET SESSION AUTHORIZATION "<user>"` for each query. Every OAuth user needs a matching database account. |
    | `false` | Verify the `JWT` and reject unauthenticated requests. However, all approved queries will run under the shared service-account connection pool credentials.|

    !!! note "Zen does not support it"
        Actian Zen does not support `SET SESSION AUTHORIZATION`. Set `user_impersonation` to `false` in the `oauth` block. JWT authentication works and only per-user database switching is skipped.

    **Extracting the username**

    When user impersonation is active, the server extracts the database username from the token using the following priority order:

    ```mermaid
    %%{init: {'theme': 'default', 'themeVariables': {'fontSize': '16px', 'fontFamily': 'arial'}}}%%
    flowchart TD
        A[Incoming Request with JWT] --> B{user_impersonation?}
        B -- false --> C[Run query as service account]
        B -- true --> D[Query userinfo endpoint]
        D --> E{username claim?}
        E -- found --> K[Use username]
        E -- not found --> F{preferred_username?}
        F -- found --> K
        F -- not found --> G{email claim?}
        G -- found --> H["Extract prefix (jdoe@example.com → jdoe)"]
        H --> K
        G -- not found --> I{sub claim?}
        I -- found --> J["Sanitize sub (auth0|12345 → 12345)"]
        J --> K
        K --> L["SET SESSION AUTHORIZATION 'username'"]
        L --> M[Execute query]
    ```

    !!! tip "Provider-Specific Behavior"
        - **Auth0**: Does not return `username` or `preferred_username` by default. The server usually falls back to the email prefix. Ensure that the database usernames match the email prefixes, for example, create database user `jdoe` for `jdoe@example.com`.
        - **Keycloak**: Returns `preferred_username` by default when the `profile` scope is present. Create database users that match the Keycloak login names.
        - **Either provider, when users sign in through an upstream connection**: Auth0 and Keycloak can both broker logins from Google, Microsoft Entra, SAML, or corporate single sign-on. In that case the `sub` claim carries a provider-specific ID such as `google-oauth2|12345`. The server strips the prefix and is left with `12345`, which is unlikely to match a database account. Map a usable `username` in the provider's user profile, or set `user_impersonation` to `false`.

=== "Actian NoSQL"

    Actian NoSQL does not support user impersonation. The `user_impersonation` field does not apply, and statements run as the database user configured in `application.properties`.

## Secure Remote Deployments with HTTPS and TLS

OAuth 2.0 requires HTTPS. If you configure OAuth, the server mandates HTTPS and refuses to start unless you provide a certificate and a private key.

### Step 1: Generate a Certificate

For remote testing, generate a self-signed certificate with a Subject Alternative Name (SAN).

```bash
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt \
  -days 365 -nodes \
  -subj "/CN=<your-ip-or-hostname>" \
  -addext "subjectAltName=IP:<your-ip>"
chmod 600 server.key
```

!!! note "SAN is required"
    The `-addext "subjectAltName=IP:..."` flag is required. Node.js-based MCP clients (like VS Code and Cursor) strictly enforce SAN validation and reject certificates that only use the Common Name (CN) field.

!!! tip "Production certificates"
    For production environments, use a certificate issued by a trusted Certificate Authority (CA), such as `Let's Encrypt or your corporate CA`.

### Step 2: Configure TLS

=== "SQL databases"

    Add the `ssl_certfile` certificate and `ssl_keyfile` key paths to the top level of the `conf.json` file (outside the `oauth` block). Ensure the usage of `https://` in `BASE_URL`:

    ```json
    {
      "ssl_certfile": "/app/server.crt",
      "ssl_keyfile": "/app/server.key",
      "oauth": {
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://<your-ip-or-hostname>:8000"
      }
    }
    ```

    The server validates the existance of both paths at startup, and the usage of `https://` for `BASE_URL` when SSL is active.

=== "Actian NoSQL"

    In the property names below, the `.0.` represents the index of the PEM keystore entry; increment this index to add multiple certificates.

    | Property | Required | Description |
    |---|---|---|
    | `quarkus.tls.key-store.pem.0.cert` | Yes (for TLS) | Path to the PEM certificate file inside the container. |
    | `quarkus.tls.key-store.pem.0.key` | Yes (for TLS) | Path to the PEM private key file inside the container. |
    | `quarkus.http.insecure-requests` | No | Controls how insecure HTTP requests are handled. Set it to `redirect` to send all HTTP traffic to HTTPS, or to `disabled` to reject insecure HTTP requests entirely. |

    !!! note "Quarkus TLS configuration"
        The table lists the most common properties. The full set of options is provided by the [Quarkus TLS Registry](https://quarkus.io/guides/tls-registry-reference) extension.

    Add the following to your `application.properties`:

    ```properties
    nsql.connectionURL=<connection-url>
    quarkus.tls.key-store.pem.0.cert=/certs/server.crt
    quarkus.tls.key-store.pem.0.key=/certs/server.key
    quarkus.http.insecure-requests=redirect
    ```

### Step 3: Deploy the Container

=== "SQL databases"

    Mount the certificate and key into the container using volume flags:

    !!! note "Analytics Engine example"
        The following example demonstrates how to deploy the Analytics Engine docker.

    ```bash
    docker run -p 8000:8000 \
      -v /path/to/server.crt:/app/server.crt:ro \
      -v /path/to/server.key:/app/server.key:ro \
      -v /path/to/conf.json:/app/conf.json:ro \
      actian/analytics-engine-mcp-server:1.1.0
    ```

    Reference the container paths in `conf.json`:

    ```json
    {
      "ssl_certfile": "/app/server.crt",
      "ssl_keyfile": "/app/server.key"
    }
    ```

    !!! note "Docker Key Permissions"
        If mounting the key as a volume, the container user must be able to read it:

        - **Best practice**: Ensure that `server.key` and `conf.json` file permissions are set to `600`.

=== "Actian NoSQL"

    Mount both the properties file and the certificate directory, and expose the HTTPS port:

    ```bash
    docker run \
      -v $(pwd)/application.properties:/home/jboss/config/application.properties:ro \
      -v $(pwd)/certs:/certs:ro \
      -p 8080:8080 \
      -p 8443:8443 \
      actian/nsql-mcp-server:1.1.0
    ```

### Step 4: Trust the Certificate in the MCP Client

By default, Node.js-based MCP clients (VS Code and Cursor) reject self-signed certificates. You must explicitly trust the certificate on your development machine.

1. Securely copy the certificate to your machine:

     ```bash
       scp user@<your-vm>:/path/to/server.crt ~/server.crt
     ```

2. Configure the operating system:

=== "macOS"

    ```bash
    # Add to system keychain
    sudo security add-trusted-cert -d -r trustRoot \
      -k /Library/Keychains/System.keychain ~/server.crt

    # Ensure VS Code's Node.js runtime picks it up
    launchctl setenv NODE_EXTRA_CA_CERTS "$HOME/server.crt"

    # Fully restart VS Code (Cmd+Q, then reopen)
    ```

    !!! tip "Persist across reboots"
        Add `export NODE_EXTRA_CA_CERTS="$HOME/server.crt"` to `~/.zprofile`.

    !!! tip "Remove the certificate"
        Run `sudo security delete-certificate -c "<CN>" /Library/Keychains/System.keychain`

=== "Linux"

    ```bash
    sudo cp ~/server.crt /usr/local/share/ca-certificates/mcp-server.crt
    sudo update-ca-certificates

    # For VS Code / Node.js:
    export NODE_EXTRA_CA_CERTS="$HOME/server.crt"
    # Add to ~/.bashrc or ~/.profile to persist across sessions
    ```

=== "Windows"

    ```powershell
    # Import into Trusted Root store (run PowerShell as Administrator)
    Import-Certificate -FilePath "$env:USERPROFILE\server.crt" `
      -CertStoreLocation Cert:\LocalMachine\Root

    # For VS Code / Node.js:
    [System.Environment]::SetEnvironmentVariable(
      "NODE_EXTRA_CA_CERTS",
      "$env:USERPROFILE\server.crt",
      "User"
    )

    # Fully restart VS Code after setting the variable
    ```

## Security Best Practices

!!! danger "Protect your secrets"
    The configuration file contains the OAuth client secret in plaintext — `conf.json` on the SQL engines, `application.properties` on Actian NoSQL. The following are the security guidelines:

    - **Lock down file permissions**: Run `chmod 600` on the configuration file to restrict access on the host machine.

    - **Mandate HTTPS**: Always use `https://` for the external server URL. Tokens sent over plain HTTP are vulnerable to interception.

## Provider Setup Guides

Choose your identity provider for step-by-step setup instructions:

<div class="grid cards" markdown>

- :material-cloud: **[Auth0](auth0/index.md)**  
  Cloud-hosted identity provider. Ideal for teams that want a managed service with no infrastructure to maintain.

- :material-key: **[Keycloak](keycloak/index.md)**  
  Open-source, self-hosted identity provider. Ideal for teams that need full control over their authentication infrastructure.

</div>
