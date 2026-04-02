"""
seed.py - Seeds the database with admin user and students from Excel files.
Runs automatically on every server startup via main.py.
"""

import os
import pandas as pd
from db.database import SessionLocal
from models.models import User, UserRole, UserStatus
from core.security import hash_password


def main():
    db = SessionLocal()
    added_count = 0
    skipped_count = 0

    print("\n========== SEED STARTING ==========")

    # ─────────────────────────────────────────
    # 1. ADMIN USER (only add if not exists)
    # ─────────────────────────────────────────
    existing_admin = db.query(User).filter(User.inst_id == "admin1").first()
    if not existing_admin:
        admin = User(
            full_name="System Admin",
            inst_id="admin1",
            email="admin@smartattendance.com",
            role=UserRole.admin,
            status=UserStatus.active,
            hashed_password=hash_password("Pass@123"),
            department="Administration",
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created. Login: admin1 / Pass@123")
    else:
        print("⏭️  Admin already exists. Skipping.")

    # ─────────────────────────────────────────
    # 2. IMPORT STUDENTS FROM EXCEL FILES
    # ─────────────────────────────────────────
    file1 = "Student List till 22-08-2025_VS.xlsx"
    file2 = "Student List with enrollment No. Session 2025-26.xlsx"

    if not os.path.exists(file1) or not os.path.exists(file2):
        print(f"⚠️  WARNING: One or both Excel files not found!")
        print(f"   File 1 exists: {os.path.exists(file1)}")
        print(f"   File 2 exists: {os.path.exists(file2)}")
        print("   Students will NOT be imported.")
        print("========== SEED COMPLETE ==========\n")
        db.close()
        return

    print(f"📂 Found both Excel files. Merging data...")

    df1 = pd.read_excel(file1)
    df2 = pd.read_excel(file2)

    df1['No.'] = df1['No.'].astype(str).str.strip()
    df2['No.'] = df2['No.'].astype(str).str.strip()

    df = pd.merge(df2, df1, on="No.", how="left", suffixes=('_f2', '_f1'))

    df = df[df['Enrollment No.'].notna()]
    df = df[df['Enrollment No.'].astype(str).str.strip().str.lower() != 'nan']
    df = df[df['Enrollment No.'].astype(str).str.strip() != '']

    print(f"📋 Found {len(df)} students. Importing...\n")

    for _, row in df.iterrows():
        enrollment_no = str(row['Enrollment No.']).strip()

        existing = db.query(User).filter(User.inst_id == enrollment_no).first()
        if existing:
            skipped_count += 1
            continue

        name = str(row.get('Student Name_f2', row.get('Student Name', 'Unknown'))).strip()

        mobile = str(row.get('Mobile Number', '')).replace('.0', '').strip()
        last_three = mobile[-3:] if len(mobile) >= 3 else "000"
        raw_password = f"pass{last_three}"

        email = str(row.get('E-Mail Address', '')).strip()
        if not email or email.lower() == 'nan':
            email = f"{enrollment_no.lower()}@temp.edu"

        department = str(row.get('Course Name', 'B.Tech')).strip()
        if department.lower() == 'nan':
            department = "B.Tech"

        new_student = User(
            full_name=name,
            inst_id=enrollment_no,
            email=email,
            role=UserRole.student,
            status=UserStatus.facial_required,
            hashed_password=hash_password(raw_password),
            department=department,
        )
        db.add(new_student)
        added_count += 1
        print(f"✅ Added: {name} ({enrollment_no}) | Password: {raw_password}")

    db.commit()
    db.close()

    print("\n========== SEED COMPLETE ==========")
    print(f"✅ Students added:   {added_count}")
    print(f"⏭️  Students skipped: {skipped_count} (already existed)")
    print("====================================\n")


if __name__ == "__main__":
  
    main()
    """Seed the database with CSV data and 'Section' division logic."""
import csv
import os
import sys

# Ensure the script can find your local modules
sys.path.insert(0, os.path.dirname(__file__))

from db.database import Base, SessionLocal, engine
from models.models import User, UserRole, UserStatus, AttendanceRecord, BiometricData, Session, Course
from core.security import hash_password

db = SessionLocal()

def clear():
    """Wipe existing data to prevent duplicate primary key errors when re-seeding."""
    try:
        db.query(AttendanceRecord).delete()
        db.query(BiometricData).delete()
        db.query(Session).delete()
        db.query(Course).delete()
        db.query(User).delete()
        db.commit()
        print("✅ Cleared existing data for fresh sync.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ Clear failed: {e}")

def seed_users():
    csv_filename = "Student List with enrollment No. Session 2025-26.xlsx"
    sections = ["Section A", "Section B", "Section C"]
    users_list = []
    
    # 1. Admin Setup
    users_list.append(User(
        full_name="Admin User", inst_id="admin1", email="admin@smartattendance.com",
        role=UserRole.admin, status=UserStatus.active,
        hashed_password=hash_password("Pass@123"), department="Administration",
        section="None"
    ))

    # 2. Students with Section Logic
    if os.path.exists(csv_filename):
        print(f"--> Found {csv_filename}: Importing and dividing into sections...")
        with open(csv_filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                # Rotates between A, B, and C
                assigned_section = sections[i % 3]
                
                mobile = str(row.get('Mobile Number', '')).strip()
                last_three = mobile[-3:] if len(mobile) >= 3 else "000"
                
                users_list.append(User(
                    full_name=row.get('Student Name', 'Unknown').strip(),
                    inst_id=row.get('Enrollment ID', '').strip(),
                    email=row.get('Email', '').strip() or f"{row.get('Enrollment ID')}@temp.com",
                    role=UserRole.student,
                    status=UserStatus.facial_required,
                    hashed_password=hash_password(f"pass{last_three}"),
                    department=row.get('Department', 'General').strip(),
                    section=assigned_section 
                ))
    
    try:
        for u in users_list:
            db.add(u)
        db.commit()
        print(f"✅ Successfully seeded {len(users_list)} users into 3 sections.")
    except Exception as e:
        db.rollback()
        print(f"❌ Seed failed: {e}")

def main():
    clear() # Important to wipe old data before applying new section logic
    seed_users()
    db.close()

if __name__ == "__main__":
    main()
