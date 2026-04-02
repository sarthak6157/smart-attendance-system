from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.models import Attendance, AttendanceSession, AttendanceStatus, Student
from schemas import (
    AttendanceCreate, AttendanceResponse, AttendanceUpdate,
    AttendanceBulkCreate, AttendanceSessionCreate, AttendanceSessionResponse
)
from auth import get_current_user

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


# ─── Sessions ─────────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=AttendanceSessionResponse, status_code=201)
def create_session(
    data: AttendanceSessionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    session = AttendanceSession(**data.dict())
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=List[AttendanceSessionResponse])
def list_sessions(
    subject_id: int = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(AttendanceSession)
    if subject_id:
        q = q.filter(AttendanceSession.subject_id == subject_id)
    return q.all()


@router.get("/sessions/{session_id}", response_model=AttendanceSessionResponse)
def get_session(session_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    session = db.query(AttendanceSession).filter(AttendanceSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# ─── Attendance Records ────────────────────────────────────────────────────────

@router.post("/mark", response_model=AttendanceResponse, status_code=201)
def mark_attendance(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    existing = db.query(Attendance).filter(
        Attendance.session_id == data.session_id,
        Attendance.student_id == data.student_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this student in this session")

    record = Attendance(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/mark/bulk", status_code=201)
def mark_bulk_attendance(
    data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    created = []
    for rec in data.records:
        existing = db.query(Attendance).filter(
            Attendance.session_id == data.session_id,
            Attendance.student_id == rec["student_id"]
        ).first()
        if existing:
            continue
        status_val = AttendanceStatus(rec.get("status", "present"))
        attendance = Attendance(
            session_id=data.session_id,
            student_id=rec["student_id"],
            status=status_val,
            remarks=rec.get("remarks")
        )
        db.add(attendance)
        created.append(attendance)

    db.commit()
    return {"message": f"{len(created)} attendance records created"}


@router.get("/session/{session_id}/records", response_model=List[AttendanceResponse])
def get_session_records(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(Attendance).filter(Attendance.session_id == session_id).all()


@router.get("/student/{student_id}", response_model=List[AttendanceResponse])
def get_student_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return db.query(Attendance).filter(Attendance.student_id == student_id).all()


@router.patch("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    attendance_id: int,
    data: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    record.status = data.status
    record.remarks = data.remarks
    db.commit()
    db.refresh(record)
    return record


@router.get("/student/{student_id}/summary")
def attendance_summary(
    student_id: int,
    subject_id: int = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    q = db.query(Attendance).filter(Attendance.student_id == student_id)
    if subject_id:
        q = q.join(AttendanceSession).filter(AttendanceSession.subject_id == subject_id)

    records = q.all()
    total = len(records)
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    absent  = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    late    = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    excused = sum(1 for r in records if r.status == AttendanceStatus.EXCUSED)

    return {
        "student_id": student_id,
        "total_sessions": total,
        "present": present,
        "absent": absent,
        "late": late,
        "excused": excused,
        "attendance_percentage": round((present / total) * 100, 2) if total else 0
    }
