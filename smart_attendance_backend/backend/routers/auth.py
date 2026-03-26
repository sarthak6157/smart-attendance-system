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

# ... (Keep all your existing routes like @router.post("/register"), /login, etc.) ...

# ---------------------------------------------------------------------------
# Forgot password
# ---------------------------------------------------------------------------

@router.post("/forgot-password", status_code=200)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    db.query(User).filter(User.email == payload.email).first()
    return {"message": "If that email is registered, a reset link has been sent."}


# --- PASTE THE NEW CODE BELOW THIS LINE ---

@router.get("/manual-db-setup-secret-777")
def manual_db_setup(db: Session = Depends(get_db)):
    try:
        from models.models import User, UserRole, UserStatus
        from core.security import hash_password
        
        existing_admin = db.query(User).filter(User.inst_id == "admin1").first()
        if existing_admin:
            return {"status": "exists", "message": "Admin already exists."}

        # Use clean, short strings
        admin_p = "Pass@123"
        faculty_p = "Pass@123"

        admin = User(
            full_name="System Admin",
            inst_id="admin1",
            email="admin@smartattendance.com",
            role=UserRole.admin,
            status=UserStatus.active,
            hashed_password=hash_password(admin_p),
            department="Administration"
        )
        
        faculty = User(
            full_name="Prof. Frank Miller",
            inst_id="faculty1",
            email="faculty1@univ.edu",
            role=UserRole.faculty,
            status=UserStatus.active,
            hashed_password=hash_password(faculty_p),
            department="Computer Science"
        )

        db.add(admin)
        db.add(faculty)
        db.commit()
        return {"status": "success", "message": "Setup complete. Use admin1 / Pass@123"}

    except Exception as e:
        # This will now show the actual Python error if it still fails
        return {"status": "error", "details": str(e)}
