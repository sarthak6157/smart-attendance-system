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

# Configuration - Pull from environment variables
SECRET_KEY  = os.getenv("SECRET_KEY", "fallback_dev_key_change_me")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8   # 8 hours

# Hashing configuration
pwd_context      = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme    = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(plain: str) -> str:
    """
    Hashes a password. 
    Truncates to 72 characters to prevent bcrypt from crashing (72-byte limit).
    """
    if not plain:
        return ""
    # Ensure it's a string and truncate to safely fit in bcrypt bytes
    safe_plain = str(plain)[:72]
    return pwd_context.hash(safe_plain)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifies a plain text password against its hash.
    Returns False instead of crashing if verification fails or errors.
    """
    if not plain or not hashed:
        return False
    try:
        # Truncate to match the hashing logic and stay within bcrypt limits
        safe_plain = str(plain)[:72]
        return pwd_context.verify(safe_plain, hashed)
    except Exception:
        # Catch ValueError (length) or other hashing issues to prevent 500 errors
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload  = decode_token(token)
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

def require_roles(*roles):
    """Factory that returns a dependency enforcing role membership."""
    def _check(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {[r.value for r in roles]}",
            )
        return current_user
    return _check
