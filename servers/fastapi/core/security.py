import hashlib
import secrets
from typing import Optional
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import os


security = HTTPBasic()


def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(plain_password) == hashed_password


def get_auth_credentials() -> tuple[str, str]:
    """Get authentication credentials from environment"""
    username = os.getenv("AUTH_USERNAME", "admin")
    password = os.getenv("AUTH_PASSWORD", "admin")
    return username, password


async def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Verify HTTP Basic Auth credentials"""
    expected_username, expected_password = get_auth_credentials()
    expected_password_hash = hash_password(expected_password)
    
    # Verify username
    correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        expected_username.encode("utf8")
    )
    
    # Verify password
    provided_password_hash = hash_password(credentials.password)
    correct_password = secrets.compare_digest(
        provided_password_hash.encode("utf8"),
        expected_password_hash.encode("utf8")
    )
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username
