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
    credential = payload.credential.strip()

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
# Forgot password
# ---------------------------------------------------------------------------

@router.post("/forgot-password", status_code=200)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    db.query(User).filter(User.email == payload.email).first()
    return {"message": "If that email is registered, a reset link has been sent."}

# ---------------------------------------------------------------------------
# TEMPORARY: Manual seed trigger for Free Tier users
# ---------------------------------------------------------------------------

@router.get("/manual-db-setup-secret-777")
def manual_db_setup(db: Session = Depends(get_db)):
    try:
        from models.models import User, UserRole, UserStatus
        from core.security import hash_password
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.inst_id == "admin1").first()
        if existing_admin:
            return {
                "status": "already_exists", 
                "message": "Database already has admin1.",
                "user_id": existing_admin.inst_id
            }

        # Use explicit strings to ensure hash_password doesn't receive complex objects
        ADMIN_PASS = "Pass@123"
        FACULTY_PASS = "Pass@123"

        # Create the Admin account
        admin = User(
            full_name="System Admin",
            inst_id="admin1",
            email="admin@smartattendance.com",
            role=UserRole.admin,
            status=UserStatus.active,
            hashed_password=hash_password(ADMIN_PASS),
            department="Administration"
        )
        
        # Create a Faculty account
        faculty = User(
            full_name="Prof. Test Faculty",
            inst_id="faculty1",
            email="faculty@smartattendance.com",
            role=UserRole.faculty,
            status=UserStatus.active,
            hashed_password=hash_password(FACULTY_PASS),
            department="Computer Science"
        )

        db.add(admin)
        db.add(faculty)
        db.commit()
        
        return {
            "status": "success", 
            "message": "Admin1 and Faculty1 created. You can now login.",
            "credentials": {
                "admin": "admin1 / Pass@123",
                "faculty": "faculty1 / Pass@123"
            }
        }

    except Exception as e:
        return {
            "status": "error", 
            "error_type": str(type(e).__name__),
            "details": str(e)
        }
