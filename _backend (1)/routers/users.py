"""Users routes: list, get, update, approve, delete."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.security import get_current_user, hash_password, require_roles
from db.database import get_db
from models.models import User, UserRole, UserStatus
from schemas.schemas import UserListOut, UserOut, UserStatusUpdate, UserUpdate

router = APIRouter()

AdminOrFaculty = require_roles(UserRole.admin, UserRole.faculty)
AdminOnly      = require_roles(UserRole.admin)


# ---------------------------------------------------------------------------
# List users (admin / faculty)
# ---------------------------------------------------------------------------

@router.get("", response_model=UserListOut)
def list_users(
    role:       Optional[str]  = Query(None, description="Filter by role"),
    status_:    Optional[str]  = Query(None, alias="status"),
    search:     Optional[str]  = Query(None, description="Search name / email / inst_id"),
    skip:       int            = Query(0, ge=0),
    limit:      int            = Query(50, ge=1, le=200),
    _:          User           = Depends(AdminOrFaculty),
    db:         Session        = Depends(get_db),
):
    q = db.query(User)
    if role:
        q = q.filter(User.role == role)
    if status_:
        q = q.filter(User.status == status_)
    if search:
        like = f"%{search}%"
        q = q.filter(
            User.full_name.ilike(like)
            | User.email.ilike(like)
            | User.inst_id.ilike(like)
        )
    total = q.count()
    users = q.offset(skip).limit(limit).all()
    return {"total": total, "users": users}


# ---------------------------------------------------------------------------
# Get single user
# ---------------------------------------------------------------------------

@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Students / faculty can only view their own profile; admin can view anyone
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# ---------------------------------------------------------------------------
# Update profile
# ---------------------------------------------------------------------------

@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Approve / change status  (admin only)
# ---------------------------------------------------------------------------

@router.patch("/{user_id}/status", response_model=UserOut)
def update_status(
    user_id: int,
    payload: UserStatusUpdate,
    _: User = Depends(AdminOnly),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.status = payload.status
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Delete (admin only)
# ---------------------------------------------------------------------------

@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    _: User = Depends(AdminOnly),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    db.commit()


# ---------------------------------------------------------------------------
# Pending approvals (admin)
# ---------------------------------------------------------------------------

@router.get("/pending/list", response_model=UserListOut)
def pending_users(
    _:  User    = Depends(AdminOnly),
    db: Session = Depends(get_db),
):
    users = db.query(User).filter(User.status == UserStatus.pending).all()
    return {"total": len(users), "users": users}


# ---------------------------------------------------------------------------
# Bulk approve (admin)
# ---------------------------------------------------------------------------

@router.post("/bulk-approve", status_code=200)
def bulk_approve(
    user_ids: list[int],
    _: User = Depends(AdminOnly),
    db: Session = Depends(get_db),
):
    updated = (
        db.query(User)
        .filter(User.id.in_(user_ids), User.status == UserStatus.pending)
        .all()
    )
    for u in updated:
        u.status = UserStatus.facial_required
    db.commit()
    return {"approved": len(updated)}
