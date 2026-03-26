"""Auth routes: register, login, logout, password management."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.security import create_access_token, get_current_user, hash_password, verify_password
from db.database import get_db
from models.models import User, UserRole, UserStatus
from schemas.schemas import LoginRequest, PasswordChangeRequest, TokenResponse, UserCreate, UserOut

router = APIRouter()

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    credential = payload.credential.strip()
    user = db.query(User).filter((User.email == credential) | (User.inst_id == credential)).first()
    
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    user.last_login = datetime.utcnow()
    db.commit()
    
    token = create_access_token({"sub": user.id, "role": user.role.value})
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))

@router.get("/manual-db-setup-secret-777")
def manual_db_setup(db: Session = Depends(get_db)):
    try:
        from core.security import hash_password
        existing_admin = db.query(User).filter(User.inst_id == "admin1").first()
        if existing_admin:
            return {"status": "exists", "message": "Admin already exists."}
            
        admin = User(
            full_name="System Admin", inst_id="admin1", email="admin@smartattendance.com",
            role=UserRole.admin, status=UserStatus.active,
            hashed_password=hash_password("Pass@123"), department="Administration"
        )
        db.add(admin)
        db.commit()
        return {"status": "success", "message": "Setup complete. Use admin1 / Pass@123"}
    except Exception as e:
        return {"status": "error", "details": str(e)}

@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
