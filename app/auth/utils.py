"""
Authentication utilities: JWT tokens, password hashing, verification codes.
"""
import base64
import hashlib
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt directly (bypassing passlib to avoid initialization issues).
    For passwords longer than 72 bytes, pre-hash with SHA-256 + base64 to avoid bcrypt limitation.
    Based on pyca/bcrypt documentation recommendation.
    """
    # Bcrypt has a 72-byte limit. Pre-hash with SHA-256 + base64 as recommended by pyca/bcrypt
    password_bytes = password.encode('utf-8')
    
    # Pre-hash with SHA-256, then base64 encode (44 bytes, well under 72 limit)
    # This is the recommended approach from pyca/bcrypt documentation
    password_hash = base64.b64encode(hashlib.sha256(password_bytes).digest())
    
    # Generate salt and hash using bcrypt directly
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_hash, salt)
    
    # Return as string (bcrypt returns bytes)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash using bcrypt directly.
    Always pre-hash with SHA-256 + base64 to match hash_password behavior.
    """
    # Pre-hash with SHA-256 + base64 to match hash_password
    password_bytes = plain_password.encode('utf-8')
    pre_hashed = base64.b64encode(hashlib.sha256(password_bytes).digest())
    
    # Verify the pre-hashed password against the bcrypt hash
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(pre_hashed, hashed_bytes)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in token (usually user_id, email, role)
        expires_delta: Optional expiration time, defaults to ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token.
    
    Args:
        data: Data to encode in token (usually user_id)
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    
    return encoded_jwt


def hash_refresh_token(token: str) -> str:
    """Hash refresh token for storage in database"""
    return hashlib.sha256(token.encode()).hexdigest()


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            return None
        
        return payload
        
    except JWTError:
        return None


def generate_verification_code() -> str:
    """
    Generate 6-digit verification code.
    
    Returns:
        6-digit code as string
    """
    return f"{random.randint(100000, 999999)}"


def get_verification_code_expiry() -> datetime:
    """
    Get expiration time for verification code.
    
    Returns:
        Datetime when code expires
    """
    return datetime.now(timezone.utc) + timedelta(
        minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES
    )

