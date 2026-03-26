"""
Seed the database with data from CSV and 'passXXX' logic.
"""

from datetime import datetime, timedelta
import sys
import os
import csv

# Make sure we can import the app modules
sys.path.insert(0, os.path.dirname(__file__))

from db.database import Base, SessionLocal, engine
from models.models import (
    AttendanceRecord, BiometricData, Course, Session, User, UserRole, UserStatus,
)
from core.security import hash_password

# 1. Initialize Database Session
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def clear():
    """Wipe existing data to prevent duplicate primary key errors on restart."""
    try:
        db.query(AttendanceRecord).delete()
        db.query(BiometricData).delete()
        db.query(Session).delete()
        db.query(Course).delete()
        db.query(User).delete()
        db.commit()
        print("✅ Cleared existing data.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Clear failed: {e}")

def seed_users():
    # MUST match your filename on GitHub exactly
    csv_filename = "Student List with enrollment No. Session 2025-26.xlsx - Sheet2.csv"
    users_list = []
    
    # 1. Add Default Admin
    users_list.append(User(
        full_name="Admin User",
        inst_id="admin1",
        email="admin@smartattendance.com",
        role=UserRole.admin,
        status=UserStatus.active,
        hashed_password=hash_password("Pass@123"),
        department="Administration",
    ))

    # 2. Import Students with NEW 'passXXX' logic
    if os.path.exists(csv_filename):
        print(f"--> Found {csv_filename}: Importing students...")
        with open(csv_filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Password logic: 'pass' + last 3 digits of mobile
                mobile = str(row.get('Mobile Number', '')).strip()
                last_three = mobile[-3:] if len(mobile) >= 3 else "000"
                
                users_list.append(User(
                    full_name=row.get('Student Name', 'Unknown').strip(),
                    inst_id=row.get('Enrollment ID', '').strip(),
                    email=row.get('Email', '').strip() or f"{row.get('Enrollment ID')}@temp.com",
                    role=UserRole.student,
                    status=UserStatus.facial_required,
                    hashed_password=hash_password(f"pass{last_three}"),
                    department=row.get('Department', 'General').strip()
                ))
    else:
        print(f"--> WARNING: {csv_filename} not found.")

    try:
        for u in users_list:
            db.add(u)
        db.commit()
        print(f"✅ Successfully seeded {len(users_list)} users.")
    except Exception as e:
        db.rollback()
        print(f"❌ User seeding failed: {e}")

    return {u.inst_id: u for u in users_list}

def main():
    print("\n🌱 Starting Database Synchronization...\n")
    clear()
    seed_users()
    db.close()
    print("\n✅ Synchronization Complete.")

if __name__ == "__main__":
    main()
