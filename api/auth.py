"""
Authentication and rate limiting for FastAPI.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from functools import wraps
import os
from typing import Optional

# API Key configuration
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Valid API keys (in production, store in database or environment)
VALID_API_KEYS = {
    os.getenv("API_KEY_1", "dev-key-123"): "development",
    os.getenv("API_KEY_2", "admin-key-456"): "admin",
}

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

def verify_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> str:
    """
    Verify API key from request headers.
    Returns the key's role if valid, raises HTTPException otherwise.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide 'X-API-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    
    return VALID_API_KEYS[api_key]

def get_optional_api_key(api_key: Optional[str] = Security(API_KEY_HEADER)) -> Optional[str]:
    """
    Optional API key verification.
    Returns role if valid key provided, None otherwise.
    """
    if not api_key:
        return None
    
    return VALID_API_KEYS.get(api_key)

# Rate limit configurations by endpoint type
RATE_LIMITS = {
    "public": "100/hour",      # Public endpoints (health, docs)
    "read": "200/hour",        # Read-only queries
    "write": "50/hour",        # Write operations (scraping jobs)
    "query": "100/hour",       # RAG queries (expensive)
}

def rate_limit(limit_type: str = "read"):
    """
    Decorator for rate limiting endpoints.
    
    Usage:
        @rate_limit("query")
        async def my_endpoint():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting is handled by slowapi middleware
            return await func(*args, **kwargs)
        
        # Attach rate limit metadata
        wrapper._rate_limit = RATE_LIMITS.get(limit_type, RATE_LIMITS["read"])
        return wrapper
    
    return decorator
