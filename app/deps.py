from app.config import settings
from fastapi import Depends, Header, HTTPException, status


def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API Key") 