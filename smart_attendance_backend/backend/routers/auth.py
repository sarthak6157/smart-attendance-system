"""Auth routes: register, login, logout, password management."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from db.database import get_db
from models.models import User, UserRole, UserStatus
from schemas.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    PasswordResetRequest,
    TokenResponse,
    UserCreate,
    UserOut,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    - Students are created with status=pending (admin must approve).
    - After approval they move to facial_required, then active once face is enrolled.
    """
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    if db.query(User).filter(User.inst_id == payload.inst_id).first():
        raise HTTPException(status_code=400, detail="Institution ID already in use.")

    initial_status = UserStatus.pending if payload.role == UserRole.student else UserStatus.active

    user = User(
        full_name       = payload.full_name,
        inst_id         = payload.inst_id,
        email           = payload.email,
        role            = payload.role,
        status          = initial_status,
        hashed_password = hash_password(payload.password),
        department      = payload.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with inst_id or email + password.
    Returns a JWT access token and user info.
    """
    credential = payload.credential.strip()

    # Allow email or inst_id login
    user = (
        db.query(User).filter(User.email == credential).first()
        or db.query(User).filter(User.inst_id == credential).first()
    )

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        )

    if user.status == UserStatus.inactive:
        raise HTTPException(status_code=403, detail="Account is inactive. Contact admin.")

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


# ---------------------------------------------------------------------------
# Current user info
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

@router.post("/change-password", status_code=200)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully."}


# ---------------------------------------------------------------------------
# Forgot password (demo – in production send an email)
# ---------------------------------------------------------------------------

@router.post("/forgot-password", status_code=200)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # Always return 200 to avoid email enumeration
    return {"message": "If that email is registered, a reset link has been sent."}
