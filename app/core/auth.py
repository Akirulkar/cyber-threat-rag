# app/core/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    # If no API_KEY_SECRET is configured in .env, skip check
    if not settings.API_KEY_SECRET:
        return True

    if api_key == settings.API_KEY_SECRET:
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key in 'X-API-Key' header.",
    )
