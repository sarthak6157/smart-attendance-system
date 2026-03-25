"""
Seed the database with demo data matching the frontend test accounts.

Run:
    python seed.py

Creates all tables and inserts demo users, courses, sessions, and
attendance records so the dashboards have data to display on first launch.
"""

from datetime import datetime, timedelta
import sys
import os

# Make sure we can import the app modules
sys.path.insert(0, os.path.dirname(__file__))

from db.database import Base, SessionLocal, engine
from models.models import (
    AttendanceMethod, AttendanceRecord, AttendanceStatus,
    BiometricData, Course, Session, SessionStatus, User, UserRole, UserStatus,
)
from core.security import hash_password

# ---------------------------------------------------------------------------
# Create tables
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)
db = SessionLocal()


def clear():
    """Wipe existing seed data (idempotent re-runs)."""
    db.query(AttendanceRecord).delete()
    db.query(BiometricData).delete()
    db.query(Session).delete()
    db.query(Course).delete()
    db.query(User).delete()
    db.commit()
    print("Cleared existing data.")


def seed_users():
    users = [
        # --- Students ---
        User(
            full_name="Alice Johnson",
            inst_id="student1",
            email="student1@univ.edu",
            role=UserRole.student,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Computer Science",
        ),
        User(
            full_name="Bob Williams",
            inst_id="student2",
            email="student2@univ.edu",
            role=UserRole.student,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Electrical Engineering",
        ),
        User(
            full_name="Carol Davis",
            inst_id="student3",
            email="student3@univ.edu",
            role=UserRole.student,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Computer Science",
        ),
        # Pending approval user
        User(
            full_name="David Pending",
            inst_id="pending_user",
            email="pending_user@univ.edu",
            role=UserRole.student,
            status=UserStatus.pending,
            hashed_password=hash_password("Pass@123"),
            department="Mathematics",
        ),
        # Facial registration required
        User(
            full_name="Eve Facial",
            inst_id="facial_user",
            email="facial_user@univ.edu",
            role=UserRole.student,
            status=UserStatus.facial_required,
            hashed_password=hash_password("Pass@123"),
            department="Physics",
        ),
        # --- Faculty ---
        User(
            full_name="Prof. Frank Miller",
            inst_id="faculty1",
            email="faculty1@univ.edu",
            role=UserRole.faculty,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Computer Science",
        ),
        User(
            full_name="Dr. Grace Lee",
            inst_id="faculty2",
            email="faculty2@univ.edu",
            role=UserRole.faculty,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Electrical Engineering",
        ),
        # --- Admin ---
        User(
            full_name="Admin User",
            inst_id="admin1",
            email="admin1@univ.edu",
            role=UserRole.admin,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Administration",
        ),
        # --- Scanner operator ---
        User(
            full_name="Scanner Operator",
            inst_id="scanner_user",
            email="scanner_user@univ.edu",
            role=UserRole.scanner,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Administration",
        ),
    ]
    for u in users:
        db.add(u)
    db.commit()
    print(f"  Seeded {len(users)} users.")
    return {u.inst_id: u for u in users}


def seed_courses():
    courses = [
        Course(code="CS101",  name="Introduction to Programming",    department="Computer Science",      credits=4),
        Course(code="CS202",  name="Data Structures & Algorithms",   department="Computer Science",      credits=4),
        Course(code="EE101",  name="Circuit Analysis",               department="Electrical Engineering",credits=3),
        Course(code="MATH201",name="Discrete Mathematics",           department="Mathematics",           credits=3),
        Course(code="CS301",  name="Database Systems",               department="Computer Science",      credits=3),
    ]
    for c in courses:
        db.add(c)
    db.commit()
    print(f"  Seeded {len(courses)} courses.")
    return {c.code: c for c in courses}


def seed_sessions(users: dict, courses: dict):
    faculty1 = users["faculty1"]
    faculty2 = users["faculty2"]
    cs101    = courses["CS101"]
    cs202    = courses["CS202"]
    ee101    = courses["EE101"]
    cs301    = courses["CS301"]

    now = datetime.utcnow()

    sessions = [
        # Past closed sessions
        Session(
            course_id=cs101.id, faculty_id=faculty1.id,
            title="CS101 – Week 1 Lecture",
            location="Room A-101", status=SessionStatus.closed,
            scheduled_at=now - timedelta(days=14),
            started_at=now - timedelta(days=14),
            ended_at=now - timedelta(days=14, hours=-2),
            grace_minutes=15,
        ),
        Session(
            course_id=cs101.id, faculty_id=faculty1.id,
            title="CS101 – Week 2 Lecture",
            location="Room A-101", status=SessionStatus.closed,
            scheduled_at=now - timedelta(days=7),
            started_at=now - timedelta(days=7),
            ended_at=now - timedelta(days=7, hours=-2),
            grace_minutes=15,
        ),
        Session(
            course_id=cs202.id, faculty_id=faculty1.id,
            title="CS202 – Sorting Algorithms",
            location="Room B-203", status=SessionStatus.closed,
            scheduled_at=now - timedelta(days=10),
            started_at=now - timedelta(days=10),
            ended_at=now - timedelta(days=10, hours=-1.5),
            grace_minutes=10,
        ),
        Session(
            course_id=ee101.id, faculty_id=faculty2.id,
            title="EE101 – Ohm's Law Lab",
            location="Lab 1", status=SessionStatus.closed,
            scheduled_at=now - timedelta(days=5),
            started_at=now - timedelta(days=5),
            ended_at=now - timedelta(days=5, hours=-3),
            grace_minutes=20,
        ),
        Session(
            course_id=cs301.id, faculty_id=faculty1.id,
            title="CS301 – SQL Joins",
            location="Room C-102", status=SessionStatus.closed,
            scheduled_at=now - timedelta(days=3),
            started_at=now - timedelta(days=3),
            ended_at=now - timedelta(days=3, hours=-1.5),
            grace_minutes=15,
        ),
        # Currently active session
        Session(
            course_id=cs101.id, faculty_id=faculty1.id,
            title="CS101 – Week 3 (Live)",
            location="Room A-101", status=SessionStatus.active,
            scheduled_at=now - timedelta(minutes=20),
            started_at=now - timedelta(minutes=20),
            grace_minutes=15,
            qr_token="DEMO_QR_TOKEN_LIVE_SESSION",
        ),
        # Upcoming scheduled session
        Session(
            course_id=cs202.id, faculty_id=faculty1.id,
            title="CS202 – Graph Algorithms",
            location="Room B-203", status=SessionStatus.scheduled,
            scheduled_at=now + timedelta(days=1),
            grace_minutes=10,
        ),
    ]

    for s in sessions:
        db.add(s)
    db.commit()
    print(f"  Seeded {len(sessions)} sessions.")
    return sessions


def seed_attendance(users: dict, sessions: list):
    student1 = users["student1"]
    student2 = users["student2"]
    student3 = users["student3"]

    closed = [s for s in sessions if s.status == SessionStatus.closed]

    records = []
    for i, session in enumerate(closed):
        # student1 – perfect attendance
        records.append(AttendanceRecord(
            session_id=session.id, student_id=student1.id,
            method=AttendanceMethod.qr, status=AttendanceStatus.present,
            marked_at=session.started_at + timedelta(minutes=5),
        ))
        # student2 – occasionally late or absent
        if i % 3 == 2:
            records.append(AttendanceRecord(
                session_id=session.id, student_id=student2.id,
                method=AttendanceMethod.manual, status=AttendanceStatus.absent,
                notes="Did not show up",
            ))
        elif i % 3 == 1:
            records.append(AttendanceRecord(
                session_id=session.id, student_id=student2.id,
                method=AttendanceMethod.facial, status=AttendanceStatus.late,
                marked_at=session.started_at + timedelta(minutes=25),
            ))
        else:
            records.append(AttendanceRecord(
                session_id=session.id, student_id=student2.id,
                method=AttendanceMethod.qr, status=AttendanceStatus.present,
                marked_at=session.started_at + timedelta(minutes=3),
            ))
        # student3 – good attendance, one absence
        if i == 1:
            pass  # absent (no record)
        else:
            records.append(AttendanceRecord(
                session_id=session.id, student_id=student3.id,
                method=AttendanceMethod.qr, status=AttendanceStatus.present,
                marked_at=session.started_at + timedelta(minutes=8),
            ))

    for r in records:
        db.add(r)
    db.commit()
    print(f"  Seeded {len(records)} attendance records.")


def main():
    print("\n🌱 Seeding Smart Attendance database…\n")
    clear()
    print("Seeding users…")
    users = seed_users()
    print("Seeding courses…")
    courses = seed_courses()
    print("Seeding sessions…")
    sessions = seed_sessions(users, courses)
    print("Seeding attendance records…")
    seed_attendance(users, sessions)
    db.close()
    print("\n✅ Done! You can now start the server:\n")
    print("   uvicorn main:app --reload --port 8000\n")
    print("   Swagger docs → http://localhost:8000/docs\n")
    print("Demo login credentials:")
    print("   student1 / Pass@123    → Student dashboard")
    print("   faculty1 / Pass@123    → Faculty dashboard")
    print("   admin1   / Pass@123    → Admin dashboard")
    print("   scanner_user / Pass@123 → Scan page\n")


if __name__ == "__main__":
    main()
