"""Session routes: create, list, start, end, QR token."""

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session as DBSession

from core.security import get_current_user, require_roles
from db.database import get_db
from models.models import Session, SessionStatus, User, UserRole
from schemas.schemas import SessionCreate, SessionListOut, SessionOut, SessionUpdate

router = APIRouter()

FacultyOrAdmin = require_roles(UserRole.faculty, UserRole.admin)


# ---------------------------------------------------------------------------
# Create session
# ---------------------------------------------------------------------------

@router.post("", response_model=SessionOut, status_code=201)
def create_session(
    payload: SessionCreate,
    current_user: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    session = Session(
        course_id     = payload.course_id,
        faculty_id    = current_user.id,
        title         = payload.title,
        location      = payload.location,
        scheduled_at  = payload.scheduled_at,
        grace_minutes = payload.grace_minutes,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


# ---------------------------------------------------------------------------
# List sessions
# ---------------------------------------------------------------------------

@router.get("", response_model=SessionListOut)
def list_sessions(
    course_id:   Optional[int] = None,
    faculty_id:  Optional[int] = None,
    status_:     Optional[str] = Query(None, alias="status"),
    skip:        int           = 0,
    limit:       int           = 50,
    current_user: User         = Depends(get_current_user),
    db:           DBSession    = Depends(get_db),
):
    q = db.query(Session)

    # Faculty only see their own sessions unless they are admin
    if current_user.role == UserRole.faculty:
        q = q.filter(Session.faculty_id == current_user.id)
    elif faculty_id:
        q = q.filter(Session.faculty_id == faculty_id)

    if course_id:
        q = q.filter(Session.course_id == course_id)
    if status_:
        q = q.filter(Session.status == status_)

    total = q.count()
    sessions = q.order_by(Session.scheduled_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "sessions": sessions}


# ---------------------------------------------------------------------------
# Get single session
# ---------------------------------------------------------------------------

@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    _: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    return s


# ---------------------------------------------------------------------------
# Update session metadata
# ---------------------------------------------------------------------------

@router.patch("/{session_id}", response_model=SessionOut)
def update_session(
    session_id: int,
    payload: SessionUpdate,
    current_user: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    if current_user.role != UserRole.admin and s.faculty_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(s, field, value)
    db.commit()
    db.refresh(s)
    return s


# ---------------------------------------------------------------------------
# Start session – generates QR token
# ---------------------------------------------------------------------------

@router.post("/{session_id}/start", response_model=SessionOut)
def start_session(
    session_id: int,
    current_user: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    from datetime import datetime
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    if current_user.role != UserRole.admin and s.faculty_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if s.status != SessionStatus.scheduled:
        raise HTTPException(status_code=400, detail=f"Session is already {s.status.value}.")
    s.status     = SessionStatus.active
    s.started_at = datetime.utcnow()
    s.qr_token   = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(s)
    return s


# ---------------------------------------------------------------------------
# End / close session
# ---------------------------------------------------------------------------

@router.post("/{session_id}/end", response_model=SessionOut)
def end_session(
    session_id: int,
    current_user: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    from datetime import datetime
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    if current_user.role != UserRole.admin and s.faculty_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    if s.status != SessionStatus.active:
        raise HTTPException(status_code=400, detail="Session is not active.")
    s.status   = SessionStatus.closed
    s.ended_at = datetime.utcnow()
    s.qr_token = None   # invalidate QR
    db.commit()
    db.refresh(s)
    return s


# ---------------------------------------------------------------------------
# Refresh QR token (while session is active)
# ---------------------------------------------------------------------------

@router.post("/{session_id}/refresh-qr", response_model=SessionOut)
def refresh_qr(
    session_id: int,
    current_user: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s or s.status != SessionStatus.active:
        raise HTTPException(status_code=400, detail="Session is not active.")
    if current_user.role != UserRole.admin and s.faculty_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    s.qr_token = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(s)
    return s


# ---------------------------------------------------------------------------
# Delete session (admin only)
# ---------------------------------------------------------------------------

@router.delete("/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    _: User = Depends(require_roles(UserRole.admin)),
    db: DBSession = Depends(get_db),
):
    s = db.query(Session).filter(Session.id == session_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Session not found.")
    db.delete(s)
    db.commit()
