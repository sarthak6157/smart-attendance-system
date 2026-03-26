"""
Seed the database with data from CSV and demo records.
"""

from datetime import datetime, timedelta
import sys
import os
import csv

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
    users_list = []
    
    # 1. Add Default Admin and Faculty
    users_list.append(User(
        full_name="Admin User",
        inst_id="admin1",
        email="admin@smartattendance.com",
        role=UserRole.admin,
        status=UserStatus.active,
        hashed_password=hash_password("Pass@123"),
        department="Administration",
    ))
    
    users_list.append(User(
        full_name="Prof. Frank Miller",
        inst_id="faculty1",
        email="faculty1@univ.edu",
        role=UserRole.faculty,
        status=UserStatus.active,
        hashed_password=hash_password("Pass@123"),
        department="Computer Science",
    ))

    # 2. Import Students from CSV
    csv_filename = "Student List with enrollment No. Session 2025-26.xlsx - Sheet2.csv"
    if os.path.exists(csv_filename):
        print(f"--> Found {csv_filename}: Importing students...")
        with open(csv_filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Password logic: password + last 3 digits of mobile
                mobile = str(row.get('Mobile Number', '')).strip()
                last_three = mobile[-3:] if len(mobile) >= 3 else "000"
                
                users_list.append(User(
                    full_name=row.get('Student Name', 'Unknown').strip(),
                    inst_id=row.get('Enrollment ID', '').strip(),
                    email=row.get('Email', '').strip() or f"{row.get('Enrollment ID')}@temp.com",
                    role=UserRole.student,
                    status=UserStatus.facial_required,
                    hashed_password=hash_password(f"password{last_three}"),
                    department=row.get('Department', 'General').strip()
                ))
    else:
        print(f"--> WARNING: {csv_filename} not found. Only default users created.")

    for u in users_list:
        db.add(u)
    db.commit()
    print(f"  Successfully seeded {len(users_list)} users.")
    return {u.inst_id: u for u in users_list}


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
    # Check if faculty1 exists (required for sessions)
    faculty1 = users.get("faculty1")
    if not faculty1:
        return []

    cs101 = courses["CS101"]
    now = datetime.utcnow()

    sessions = [
        Session(
            course_id=cs101.id, faculty_id=faculty1.id,
            title="CS101 – Week 3 (Live)",
            location="Room A-101", status=SessionStatus.active,
            scheduled_at=now - timedelta(minutes=20),
            started_at=now - timedelta(minutes=20),
            grace_minutes=15,
            qr_token="DEMO_QR_TOKEN_LIVE_SESSION",
        )
    ]

    for s in sessions:
        db.add(s)
    db.commit()
    print(f"  Seeded {len(sessions)} sessions.")
    return sessions


def main():
    print("\n🌱 Auto-Synchronizing Smart Attendance database…\n")
    clear()
    users = seed_users()
    courses = seed_courses()
    seed_sessions(users, courses)
    db.close()
    print("\n✅ Synchronization Complete.")


if __name__ == "__main__":
    main()
