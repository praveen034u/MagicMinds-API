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
    try:
        response = httpx.get(settings.AUTH0_JWKS_URL, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch JWKS: {e}")
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
        
        # Verify the token
        payload = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE,
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
    """Dependency to get current authenticated user from JWT."""
    token = credentials.credentials
    
    payload = verify_token(token)
    
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject"
        )
    
    email = payload.get("email") or payload.get("https://your-app.com/email")
    
    return CurrentUser(sub=sub, email=email, claims=payload)
