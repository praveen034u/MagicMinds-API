"""Auth0 JWT authentication dependency."""
import httpx
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from functools import lru_cache
import logging
from ..config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

class CurrentUser:
    """Current authenticated user from JWT."""
    def __init__(self, sub: str, email: Optional[str] = None, claims: Optional[Dict[str, Any]] = None):
        self.sub = sub
        self.email = email
        self.claims = claims or {}

@lru_cache()
def get_jwks() -> Dict[str, Any]:
    """Fetch and cache JWKS from Auth0."""
    settings = get_settings()
    
    # Check if Auth0 is configured
    if not settings.AUTH0_DOMAIN or not settings.AUTH0_JWKS_URL:
        logger.error("Auth0 not configured - missing AUTH0_DOMAIN or AUTH0_JWKS_URL")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication not configured. Please set AUTH0_DOMAIN and AUTH0_JWKS_URL in environment variables."
        )
    
    try:
        logger.info(f"Fetching JWKS from: {settings.AUTH0_JWKS_URL}")
        response = httpx.get(settings.AUTH0_JWKS_URL, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching JWKS: {e.response.status_code} - {e.response.text}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Authentication service returned error: {e.response.status_code}"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error fetching JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot reach authentication service: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching JWKS: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

def get_signing_key(token: str) -> str:
    """Extract signing key from JWKS based on token header."""
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )
        
        jwks = get_jwks()
        
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate signing key"
        )
    except JWTError as e:
        logger.error(f"JWT header error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )

def verify_token(token: str) -> Dict[str, Any]:
    """Verify Auth0 JWT token and return claims."""
    settings = get_settings()
    
    try:
        signing_key = get_signing_key(token)
        
        # Accept both API audience and Client ID (for id_token)
        # This allows using either access_token or id_token
        valid_audiences = [
            settings.AUTH0_AUDIENCE,  # API audience
            settings.AUTH0_CLIENT_ID,  # Client ID (for id_token)
        ]
        
        # Try to decode with the first audience, then try others if it fails
        payload = None
        last_error = None
        
        for audience in valid_audiences:
            try:
                payload = jwt.decode(
                    token,
                    signing_key,
                    algorithms=["RS256"],
                    audience=audience,
                    issuer=settings.AUTH0_ISSUER,
                    options={
                        "verify_signature": True,
                        "verify_aud": True,
                        "verify_iat": True,
                        "verify_exp": True,
                        "verify_nbf": True,
                        "verify_iss": True,
                        "require_aud": True,
                        "require_iat": True,
                        "require_exp": True,
                    }
                )
                # If successful, break out of loop
                logger.info(f"Token verified with audience: {audience}")
                break
            except jwt.JWTClaimsError as e:
                last_error = e
                continue
        
        if payload is None:
            raise last_error or jwt.JWTClaimsError("Invalid token claims")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTClaimsError as e:
        logger.error(f"JWT claims error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims"
        )
    except JWTError as e:
        logger.error(f"JWT verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    except Exception as e:
        logger.error(f"Unexpected auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication error"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> CurrentUser:
    """
    Dependency to get current authenticated user from JWT.
    
    Extracts user information from the Authorization header:
    1. Extracts Bearer token from: Authorization: Bearer <token>
    2. Verifies the JWT signature using Auth0's public keys (JWKS)
    3. Validates token claims (audience, issuer, expiration, etc.)
    4. Extracts user data from token payload:
       - sub: Auth0 user ID (e.g., "auth0|123456789")
       - email: User's email address
    
    Returns:
        CurrentUser object with sub, email, and all token claims
        
    Raises:
        HTTPException 401: If token is invalid, expired, or missing required claims
    """
    token = credentials.credentials
    
    payload = verify_token(token)
    
    # Extract 'sub' (subject) - this is the Auth0 user ID
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject"
        )
    
    # Extract email from standard claim or custom namespace
    email = payload.get("email") or payload.get("https://your-app.com/email")
    
    return CurrentUser(sub=sub, email=email, claims=payload)
