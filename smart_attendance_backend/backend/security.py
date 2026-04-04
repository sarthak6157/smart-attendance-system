"""
seed.py - Seeds the database with admin user and students from Excel files.
Runs automatically on every server startup via main.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Safe pandas import - server still starts even if pandas missing
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("WARNING: pandas not installed. Student Excel import disabled.")

from db.database import SessionLocal
from models.models import User, UserRole, UserStatus
from core.security import hash_password


def main():
    db = SessionLocal()
    added_count = 0
    skipped_count = 0

    print("\n========== SEED STARTING ==========")

    # 1. ADMIN USER - only add if not exists
    try:
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
            print("Admin user created. Login: admin1 / Pass@123")
        else:
            print("Admin already exists. Skipping.")
    except Exception as e:
        print(f"Admin seed error (non-fatal): {e}")
        db.rollback()

    # 2. IMPORT STUDENTS FROM EXCEL FILES
    if not PANDAS_AVAILABLE:
        print("Skipping Excel import - pandas not available.")
        print("========== SEED COMPLETE ==========\n")
        db.close()
        return

    file1 = "Student List till 22-08-2025_VS.xlsx"
    file2 = "Student List with enrollment No. Session 2025-26.xlsx"

    if not os.path.exists(file1) or not os.path.exists(file2):
        print(f"WARNING: Excel files not found. Students will NOT be imported.")
        print(f"  File 1 ({file1}) exists: {os.path.exists(file1)}")
        print(f"  File 2 ({file2}) exists: {os.path.exists(file2)}")
        print("========== SEED COMPLETE ==========\n")
        db.close()
        return

    try:
        print("Found both Excel files. Merging data...")

        df1 = pd.read_excel(file1)
        df2 = pd.read_excel(file2)

        df1['No.'] = df1['No.'].astype(str).str.strip()
        df2['No.'] = df2['No.'].astype(str).str.strip()

        df = pd.merge(df2, df1, on="No.", how="left", suffixes=('_f2', '_f1'))

        df = df[df['Enrollment No.'].notna()]
        df = df[df['Enrollment No.'].astype(str).str.strip().str.lower() != 'nan']
        df = df[df['Enrollment No.'].astype(str).str.strip() != '']

        print(f"Found {len(df)} students. Importing...\n")

        for _, row in df.iterrows():
            try:
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
                print(f"Added: {name} ({enrollment_no}) | Password: {raw_password}")

            except Exception as row_err:
                print(f"Skipping row due to error: {row_err}")
                db.rollback()
                continue

        db.commit()

    except Exception as e:
        print(f"Excel import error (non-fatal): {e}")
        db.rollback()

    db.close()

    print("\n========== SEED COMPLETE ==========")
    print(f"Students added:   {added_count}")
    print(f"Students skipped: {skipped_count} (already existed)")
    print("====================================\n")


if __name__ == "__main__":
    main()
