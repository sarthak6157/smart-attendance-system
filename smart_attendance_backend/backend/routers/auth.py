"""Auth routes: register, login, logout, password management."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.security import create_access_token, get_current_user, hash_password, verify_password
from db.database import get_db
from models.models import User, UserRole, UserStatus
from schemas.schemas import LoginRequest, PasswordChangeRequest, TokenResponse, UserCreate, UserOut

router = APIRouter()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    credential = payload.credential.strip()
    user = db.query(User).filter(
        (User.email == credential) | (User.inst_id == credential)
    ).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


# ---------------------------------------------------------------------------
# Register (new student self-registration)
# ---------------------------------------------------------------------------

@router.post("/register", response_model=UserOut, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    # Check if inst_id or email already exists
    existing = db.query(User).filter(
        (User.inst_id == payload.inst_id) | (User.email == payload.email)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this ID or email already exists.")

    new_user = User(
        full_name=payload.full_name,
        inst_id=payload.inst_id,
        email=payload.email,
        role=payload.role,
        status=UserStatus.pending,
        hashed_password=hash_password(payload.password),
        department=payload.department,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ---------------------------------------------------------------------------
# Get current user profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------------------------------------------------------------------------
# Update current user profile (name, email, department, avatar)
# ---------------------------------------------------------------------------

@router.patch("/me", response_model=UserOut)
def update_me(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    allowed_fields = {"full_name", "email", "department", "avatar_url"}
    for field, value in payload.items():
        if field in allowed_fields and value is not None:
            setattr(current_user, field, value)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
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
    # Verify current password
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect.")

    # Update to new hashed password
    current_user.hashed_password = hash_password(payload.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Password updated successfully."}


# ---------------------------------------------------------------------------
# Manual DB setup (one-time admin creation)
# ---------------------------------------------------------------------------

@router.get("/manual-db-setup-secret-777")
def manual_db_setup(db: Session = Depends(get_db)):
    try:
        existing_admin = db.query(User).filter(User.inst_id == "admin1").first()
        if existing_admin:
            return {"status": "exists", "message": "Admin already exists."}

        admin = User(
            full_name="System Admin", inst_id="admin1",
            email="admin@smartattendance.com",
            role=UserRole.admin, status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Administration"
        )
        db.add(admin)
        db.commit()
        return {"status": "success", "message": "Setup complete. Use admin1 / Pass@123"}
    except Exception as e:
        return {"status": "error", "details": str(e)}
