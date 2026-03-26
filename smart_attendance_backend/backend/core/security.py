"""Security utilities: JWT creation/verification and password hashing."""

import os
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from db.database import get_db
from models.models import User

# Configuration
SECRET_KEY  = os.getenv("SECRET_KEY", "fallback_dev_key_change_me")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

pwd_context      = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme    = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(plain: str) -> str:
    """Hashes a password with strict 72-character truncation to prevent bcrypt crash."""
    if not plain:
        return ""
    return pwd_context.hash(str(plain)[:72])

def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a password safely."""
    if not plain or not hashed:
        return False
    try:
        return pwd_context.verify(str(plain)[:72], hashed)
    except Exception:
        return False

# ... (Include create_access_token, decode_token, and get_current_user as they were before)
