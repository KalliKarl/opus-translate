"""Opus Translate — API Key authentication."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings

_bearer = HTTPBearer(auto_error=False)


def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """API key yoksa serbest geçiş; varsa Bearer token doğrula."""
    if not settings.api_key:
        return
    if credentials is None or credentials.credentials != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
