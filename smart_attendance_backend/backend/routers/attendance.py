"""Attendance routes: mark via QR, facial, manual; view history."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession

from core.security import get_current_user, require_roles
from db.database import get_db
from models.models import (
    AttendanceMethod, AttendanceRecord, AttendanceStatus,
    Session, SessionStatus, User, UserRole,
)
from schemas.schemas import (
    AttendanceListOut, AttendanceMarkManual, AttendanceMarkQR, AttendanceOut,
)

router = APIRouter()


def _compute_status(session: Session) -> AttendanceStatus:
    """Mark student as late if they scan after the grace window."""
    if session.started_at:
        cutoff = session.started_at + timedelta(minutes=session.grace_minutes)
        if datetime.utcnow() > cutoff:
            return AttendanceStatus.late
    return AttendanceStatus.present


# ---------------------------------------------------------------------------
# Mark attendance via QR scan
# ---------------------------------------------------------------------------

@router.post("/qr", response_model=AttendanceOut, status_code=201)
def mark_by_qr(
    payload: AttendanceMarkQR,
    db: DBSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Student scans QR code on the scan page.
    - Validate token → find active session.
    - Prevent duplicate records.
    - Auto-detect late arrival.
    """
    session = db.query(Session).filter(
        Session.qr_token == payload.qr_token,
        Session.status   == SessionStatus.active,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Invalid or expired QR code.")

    # Use authenticated user instead of payload student_id for security
    student_id = current_user.id

    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.student_id == student_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already marked for this session.")

    record = AttendanceRecord(
        session_id = session.id,
        student_id = student_id,
        method     = AttendanceMethod.qr,
        status     = _compute_status(session),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Mark attendance via facial recognition
# ---------------------------------------------------------------------------

@router.post("/facial", response_model=AttendanceOut, status_code=201)
def mark_by_facial(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """
    Called after the frontend facial recognition library confirms identity.
    The backend records the event; actual face-match logic runs client-side
    (or a dedicated face-service can POST here after matching).
    """
    session = db.query(Session).filter(
        Session.id     == session_id,
        Session.status == SessionStatus.active,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not active.")

    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == session.id,
        AttendanceRecord.student_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Attendance already marked.")

    record = AttendanceRecord(
        session_id = session.id,
        student_id = current_user.id,
        method     = AttendanceMethod.facial,
        status     = _compute_status(session),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# Manual mark (faculty / admin)
# ---------------------------------------------------------------------------

@router.post("/manual", response_model=AttendanceOut, status_code=201)
def mark_manual(
    payload: AttendanceMarkManual,
    current_user: User = Depends(require_roles(UserRole.faculty, UserRole.admin)),
    db: DBSession = Depends(get_db),
):
    session = db.query(Session).filter(Session.id == payload.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.session_id == payload.session_id,
        AttendanceRecord.student_id == payload.student_id,
    ).first()
    if existing:
        # Update instead of duplicate
        existing.status = payload.status
        existing.method = AttendanceMethod.manual
        existing.notes  = payload.notes
        db.commit()
        db.refresh(existing)
        return existing

    record = AttendanceRecord(
        session_id = payload.session_id,
        student_id = payload.student_id,
        method     = AttendanceMethod.manual,
        status     = payload.status,
        notes      = payload.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# ---------------------------------------------------------------------------
# List attendance records for a session
# ---------------------------------------------------------------------------

@router.get("/session/{session_id}", response_model=AttendanceListOut)
def session_attendance(
    session_id: int,
    _: User = Depends(require_roles(UserRole.faculty, UserRole.admin)),
    db: DBSession = Depends(get_db),
):
    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.session_id == session_id)
        .all()
    )
    return {"total": len(records), "records": records}


# ---------------------------------------------------------------------------
# Student attendance history
# ---------------------------------------------------------------------------

@router.get("/student/{student_id}", response_model=AttendanceListOut)
def student_history(
    student_id:  int,
    course_id:   Optional[int] = None,
    skip:        int = 0,
    limit:       int = 100,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    # Students can only view their own history
    if current_user.role == UserRole.student and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    q = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
    if course_id:
        q = (
            q.join(Session, AttendanceRecord.session_id == Session.id)
             .filter(Session.course_id == course_id)
        )
    total = q.count()
    records = q.order_by(AttendanceRecord.marked_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "records": records}


# ---------------------------------------------------------------------------
# Delete a record (admin only)
# ---------------------------------------------------------------------------

@router.delete("/{record_id}", status_code=204)
def delete_record(
    record_id: int,
    _: User = Depends(require_roles(UserRole.admin)),
    db: DBSession = Depends(get_db),
):
    record = db.query(AttendanceRecord).filter(AttendanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    db.delete(record)
    db.commit()
