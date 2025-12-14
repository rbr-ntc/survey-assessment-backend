"""
Authentication utilities: JWT tokens, password hashing, verification codes.
"""
import hashlib
import random
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt.
    For passwords longer than 72 bytes, pre-hash with SHA-256 to avoid bcrypt limitation.
    """
    # Bcrypt has a 72-byte limit. Pre-hash long passwords with SHA-256
    password_bytes = password.encode('utf-8')
    
    # Always pre-hash with SHA-256 to ensure consistent length and avoid bcrypt 72-byte limit
    # This is safe because we're still using bcrypt on top, just with a fixed-length input
    password_hash = hashlib.sha256(password_bytes).hexdigest()
    
    # Now hash the SHA-256 hash with bcrypt (always 64 bytes, well under 72 limit)
    return pwd_context.hash(password_hash)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash.
    Always pre-hash with SHA-256 to match hash_password behavior.
    """
    # Pre-hash with SHA-256 to match hash_password
    password_bytes = plain_password.encode('utf-8')
    pre_hashed = hashlib.sha256(password_bytes).hexdigest()
    
    # Verify the pre-hashed password against the bcrypt hash
    return pwd_context.verify(pre_hashed, hashed_password)


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

