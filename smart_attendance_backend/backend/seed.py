"""Seed the database with CSV data and new 'passXXX' logic."""
import csv
import os
from datetime import datetime
from db.database import Base, SessionLocal, engine
from models.models import User, UserRole, UserStatus
from core.security import hash_password

db = SessionLocal()

def seed_users():
    csv_filename = "Student List with enrollment No. Session 2025-26.xlsx - Sheet2.csv"
    users_list = []
    
    # 1. Add Default Admin
    users_list.append(User(
        full_name="Admin User", inst_id="admin1", email="admin@smartattendance.com",
        role=UserRole.admin, status=UserStatus.active,
        hashed_password=hash_password("Pass@123"), department="Administration"
    ))

    # 2. Import Students with NEW password logic
    if os.path.exists(csv_filename):
        with open(csv_filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mobile = str(row.get('Mobile Number', '')).strip()
                last_three = mobile[-3:] if len(mobile) >= 3 else "000"
                # NEW SUGGESTION: "pass" instead of "password"
                new_pass = f"pass{last_three}"
                
                users_list.append(User(
                    full_name=row.get('Student Name', 'Unknown').strip(),
                    inst_id=row.get('Enrollment ID', '').strip(),
                    email=row.get('Email', '').strip() or f"{row.get('Enrollment ID')}@temp.com",
                    role=UserRole.student, status=UserStatus.facial_required,
                    hashed_password=hash_password(new_pass),
                    department=row.get('Department', 'General').strip()
                ))
    
    for u in users_list:
        db.add(u)
    db.commit()
    print(f"Successfully seeded {len(users_list)} users with 'passXXX' passwords.")

if __name__ == "__main__":
    seed_users()
