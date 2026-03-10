"""Custom JWT verifier wrapper and middleware for capturing upstream access tokens."""
import jwt
import httpx
from typing import Any, Dict, Optional
from contextvars import ContextVar
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth.oidc_proxy import OIDCProxy
import logging

# Async-safe context variable to store the authenticated username
# Different requests won't overwrite each other
current_username: ContextVar[str | None] = ContextVar("current_username", default=None)

logger = logging.getLogger(__name__)


class TokenCapturingJWTVerifier(JWTVerifier):
    """
    Wrapper around JWTVerifier that captures the upstream access token
    during verification and stores it in a ContextVar.
    
    When OIDCProxy validates the upstream Keycloak/Auth0 token, it calls the
    token_verifier. This wrapper intercepts that call, stores the token,
    then passes it to the parent JWTVerifier for actual validation.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize and log that the verifier is being created."""
        super().__init__(*args, **kwargs)
        logger.info(f"TokenCapturingJWTVerifier initialized with issuer: {kwargs.get('issuer')}, audience: {kwargs.get('audience')}")
    
    def _extract_username_from_claims(self, claims: Dict[str, Any], source: str = "token") -> Optional[str]:
        """
        Extract username from claims with consistent priority order.
        
        Priority: username > preferred_username > email (prefix) > sub (sanitized)
        
        Args:
            claims: Dictionary of claims from token or userinfo
            source: Description of the source for logging ("token" or "userinfo")
            
        Returns:
            Extracted username or None
        """
        # 1. Explicit Username
        if 'username' in claims:
            username = claims['username']
            logger.info(f"Extracted username from {source} 'username': {username}")
            return username
        
        # 2. Preferred Username (Keycloak standard)
        if 'preferred_username' in claims:
            username = claims['preferred_username']
            logger.info(f"Extracted username from {source} 'preferred_username': {username}")
            return username
        
        # 3. Email (extract prefix before @)
        if claims.get('email'):
            email = claims['email']
            username = email.split('@')[0] if '@' in email else email
            logger.info(f"Extracted username from {source} email: {username}")
            return username
        
        # 4. Subject (sanitized) - only for token, not userinfo
        if source == "token" and claims.get('sub'):
            sub = claims['sub']
            # Handle Auth0 style "google-oauth2|12345" or "auth0|12345"
            username = sub.split('|', 1)[1] if '|' in sub else sub
            logger.info(f"Extracted username from sanitized sub: {username}")
            return username
        
        return None
    
    async def _fetch_userinfo(self, token: str, issuer: str, aud: list) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile from OIDC userinfo endpoint.
        
        Args:
            token: Access token to use for authentication
            issuer: Token issuer URL
            aud: List of audience values from token
            
        Returns:
            Userinfo dictionary or None if fetch fails
        """
        # Check if userinfo endpoint is in audience
        userinfo_url = None
        for audience in aud:
            if 'userinfo' in audience:
                userinfo_url = audience
                break
        
        # If not found in audience, construct standard OIDC userinfo endpoint from issuer
        if not userinfo_url and issuer:
            userinfo_url = f"{issuer.rstrip('/')}/userinfo"
        
        if not userinfo_url:
            return None
        
        try:
            logger.info(f"Fetching user profile from userinfo endpoint: {userinfo_url}")
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    userinfo_url,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch userinfo from {userinfo_url}: {e}")
            return None
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Override verify_token to extract database username and store it.
        
        Args:
            token: The JWT token string to verify
            
        Returns:
            The validated token claims
        """
        username = None
        
        try:
            # Decode token to extract username
            decoded = jwt.decode(token, options={"verify_signature": False})
            logger.debug(f"Upstream token claims - sub: {decoded.get('sub')}, "
                       f"email: {decoded.get('email')}, "
                       f"preferred_username: {decoded.get('preferred_username')}")
            
            # Try userinfo endpoint FIRST (especially for Auth0/Google OAuth)
            aud = decoded.get('aud', [])
            if isinstance(aud, str):
                aud = [aud]
            
            userinfo = await self._fetch_userinfo(token, decoded.get('iss', ''), aud)
            if userinfo:
                logger.debug(f"Userinfo response: {userinfo}")
                username = self._extract_username_from_claims(userinfo, "userinfo")
            
            # If userinfo didn't work, fallback to token claims
            if not username:
                logger.info("Userinfo fetch failed or username not found, falling back to token claims")
                username = self._extract_username_from_claims(decoded, "token")
            
        except Exception as e:
            logger.error(f"Error extracting username from token: {e}")

        # Call parent's verify_token to do actual validation first
        claims = await super().verify_token(token)

        # Store username only after token is verified
        if username:
            current_username.set(username)
            logger.info(f"Stored database username: {username}")
        else:
            logger.warning("Could not extract username from token or userinfo")

        return claims


def configure_authentication(conf_file_args):
    """Configure OAuth authentication if enabled in config.
    
    Returns:
        OIDCProxy instance if OAuth is configured, None otherwise.
    """
    oauth_config = conf_file_args.get("oauth", {})
    
    if not oauth_config.get("FASTMCP_SERVER_AUTH_CONFIG_URL") or not oauth_config.get("FASTMCP_SERVER_AUTH_CLIENT_ID"):
        logger.info("OAuth authentication not configured - server will run without authentication")
        return None
    
    logger.info("Configuring OIDCProxy authentication")
    
    # Determine audience (Auth0 uses explicit audience, Keycloak uses client_id)
    audience = oauth_config.get("FASTMCP_SERVER_AUTH_AUDIENCE")
    
    # Prepare scopes for Auth0 (ensure openid, email, profile)
    required_scopes = None
    if oauth_config.get("FASTMCP_SERVER_AUTH_SCOPE"):
        scopes = [s.strip() for s in oauth_config["FASTMCP_SERVER_AUTH_SCOPE"].split()]
        for scope in ['openid', 'email', 'profile']:
            if scope not in scopes:
                scopes.append(scope)
        required_scopes = scopes
    
    # Fetch OIDC config and create token verifier
    token_verifier = None
    try:
        logger.info(f"Fetching OIDC configuration from: {oauth_config['FASTMCP_SERVER_AUTH_CONFIG_URL']}")
        # Use synchronous client since this runs during server initialization
        with httpx.Client(timeout=10.0) as client:
            response = client.get(oauth_config['FASTMCP_SERVER_AUTH_CONFIG_URL'])
            response.raise_for_status()
            oidc_config = response.json()
        
            jwks_uri = oidc_config.get('jwks_uri')
            issuer = oidc_config.get('issuer')
        
            if jwks_uri:
                verifier_kwargs = {
                    'jwks_uri': jwks_uri,
                    'issuer': issuer,
                    'audience': audience
                }
                if required_scopes:
                    verifier_kwargs['required_scopes'] = required_scopes
                    logger.info(f"Token verifier scopes: {required_scopes}")
                
                impersonate = oauth_config.get("user_impersonation", True)
                if impersonate:
                    token_verifier = TokenCapturingJWTVerifier(**verifier_kwargs)
                    logger.info(f"Created TokenCapturingJWTVerifier - audience: {audience}, issuer: {issuer}")
                else:
                    logger.info("user_impersonation disabled - using default OIDCProxy token verifier")
            else:
                logger.warning("No jwks_uri found in OIDC config")
            
    except Exception as e:
        logger.warning(f"Could not create token verifier: {e}")
    
    # Build OIDCProxy kwargs
    auth_kwargs = {
        'config_url': oauth_config['FASTMCP_SERVER_AUTH_CONFIG_URL'],
        'client_id': oauth_config['FASTMCP_SERVER_AUTH_CLIENT_ID'],
        'client_secret': oauth_config['FASTMCP_SERVER_AUTH_CLIENT_SECRET'],
        'base_url': oauth_config['FASTMCP_SERVER_AUTH_BASE_URL']
    }
    
    if oauth_config.get('FASTMCP_SERVER_AUTH_REDIRECT_PATH'):
        auth_kwargs['redirect_path'] = oauth_config['FASTMCP_SERVER_AUTH_REDIRECT_PATH']
    
    auth_kwargs['audience'] = audience if audience else oauth_config['FASTMCP_SERVER_AUTH_CLIENT_ID']
    
    # Use custom token_verifier or fallback to required_scopes
    if token_verifier:
        auth_kwargs['token_verifier'] = token_verifier
    elif required_scopes:
        auth_kwargs['required_scopes'] = required_scopes
    
    return OIDCProxy(**auth_kwargs)


def get_current_username() -> str | None:
    """
    Retrieves the database username that was extracted and stored during token verification.
    The TokenCapturingJWTVerifier extracts the username during verify_token().
    """
    # Get the username from ContextVar (stored during token verification)
    username = current_username.get()
    
    if username:
        logger.debug(f"Retrieved database username from context: {username}")
        return username
    
    logger.debug("No username found in context")
    return None
