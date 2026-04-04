"""Reports routes: per-course summaries, analytics, CSV export."""

from io import StringIO
import csv
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from core.security import get_current_user, require_roles
from db.database import get_db
from models.models import AttendanceRecord, AttendanceStatus, Course, Session, User, UserRole
from schemas.schemas import AttendanceSummary, CourseAttendanceReport

router = APIRouter()

FacultyOrAdmin = require_roles(UserRole.faculty, UserRole.admin)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_summary(student: User, records, total_sessions: int) -> AttendanceSummary:
    present = sum(1 for r in records if r.status == AttendanceStatus.present)
    late    = sum(1 for r in records if r.status == AttendanceStatus.late)
    absent  = total_sessions - present - late
    pct     = round((present + late) / total_sessions * 100, 1) if total_sessions else 0.0
    return AttendanceSummary(
        student_id     = student.id,
        student_name   = student.full_name,
        inst_id        = student.inst_id,
        total_sessions = total_sessions,
        present        = present,
        late           = late,
        absent         = max(absent, 0),
        percentage     = pct,
    )


# ---------------------------------------------------------------------------
# Course-level attendance report
# ---------------------------------------------------------------------------

@router.get("/course/{course_id}", response_model=CourseAttendanceReport)
def course_report(
    course_id: int,
    _: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    sessions = db.query(Session).filter(Session.course_id == course_id).all()
    total_sessions = len(sessions)
    session_ids = [s.id for s in sessions]

    # All unique students who have any record in these sessions
    student_ids = (
        db.query(AttendanceRecord.student_id)
        .filter(AttendanceRecord.session_id.in_(session_ids))
        .distinct()
        .all()
    )
    student_ids = [sid for (sid,) in student_ids]

    summaries = []
    for sid in student_ids:
        student = db.query(User).filter(User.id == sid).first()
        if not student:
            continue
        records = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.student_id == sid,
                AttendanceRecord.session_id.in_(session_ids),
            )
            .all()
        )
        summaries.append(_build_summary(student, records, total_sessions))

    return CourseAttendanceReport(
        course_id      = course.id,
        course_code    = course.code,
        course_name    = course.name,
        total_sessions = total_sessions,
        summaries      = summaries,
    )


# ---------------------------------------------------------------------------
# Student summary across all courses
# ---------------------------------------------------------------------------

@router.get("/student/{student_id}")
def student_summary(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if current_user.role == UserRole.student and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")

    records = (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.student_id == student_id)
        .all()
    )

    session_ids = list({r.session_id for r in records})
    sessions = db.query(Session).filter(Session.id.in_(session_ids)).all()
    course_ids = list({s.course_id for s in sessions})

    result = []
    for cid in course_ids:
        course = db.query(Course).filter(Course.id == cid).first()
        c_sessions = [s for s in sessions if s.course_id == cid]
        c_session_ids = [s.id for s in c_sessions]
        c_records = [r for r in records if r.session_id in c_session_ids]
        summary = _build_summary(student, c_records, len(c_sessions))
        result.append({
            "course_id":   cid,
            "course_code": course.code if course else "",
            "course_name": course.name if course else "",
            **summary.model_dump(),
        })

    return {"student": student.full_name, "courses": result}


# ---------------------------------------------------------------------------
# Admin dashboard stats
# ---------------------------------------------------------------------------

@router.get("/overview")
def overview(
    _: User = Depends(require_roles(UserRole.admin)),
    db: DBSession = Depends(get_db),
):
    from models.models import UserStatus
    return {
        "total_students":  db.query(User).filter(User.role == UserRole.student).count(),
        "total_faculty":   db.query(User).filter(User.role == UserRole.faculty).count(),
        "pending_approvals": db.query(User).filter(User.status == UserStatus.pending).count(),
        "total_sessions":  db.query(Session).count(),
        "active_sessions": db.query(Session).filter(Session.status == "active").count(),
        "total_records":   db.query(AttendanceRecord).count(),
    }


# ---------------------------------------------------------------------------
# CSV export for a course
# ---------------------------------------------------------------------------

@router.get("/course/{course_id}/export")
def export_csv(
    course_id: int,
    _: User = Depends(FacultyOrAdmin),
    db: DBSession = Depends(get_db),
):
    report = course_report(course_id, _, db)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student Name", "ID", "Total Sessions", "Present", "Late", "Absent", "Percentage"])
    for s in report.summaries:
        writer.writerow([s.student_name, s.inst_id, s.total_sessions, s.present, s.late, s.absent, f"{s.percentage}%"])

    output.seek(0)
    filename = f"attendance_{report.course_code}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
