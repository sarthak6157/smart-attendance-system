"""
Import students from two XLSX files, merge their data, filter out those 
without enrollment numbers, and set dynamic passwords.

Run: python import_students.py
"""

import pandas as pd
import sys
import os

# Ensure we can import backend modules
sys.path.insert(0, os.path.dirname(__file__))

from db.database import SessionLocal
from models.models import User, UserRole, UserStatus
from core.security import hash_password

def import_real_students(file1_path, file2_path):
    db = SessionLocal()
    
    print("Loading and merging Excel files...")
    
    try:
        # Use read_excel for .xlsx files
        df1 = pd.read_excel(file1_path)
        df2 = pd.read_excel(file2_path)
    except FileNotFoundError as e:
        print(f"❌ Error: Could not find the file. {e}")
        return
    except Exception as e:
        print(f"❌ Error reading Excel file (did you run 'pip install openpyxl'?): {e}")
        return

    # Clean the "No." column to ensure they match perfectly
    df1['No.'] = df1['No.'].astype(str).str.strip()
    df2['No.'] = df2['No.'].astype(str).str.strip()

    # Merge the two dataframes based on the "No." column
    df = pd.merge(df1, df2, on="No.", how="inner", suffixes=('_f1', '_f2'))
    
    # FILTER 1: Only keep rows where 'Enrollment No.' is not empty/NaN
    df = df[df['Enrollment No.'].notna()]
    df = df[df['Enrollment No.'].astype(str).str.strip() != 'nan']
    df = df[df['Enrollment No.'].astype(str).str.strip() != '']
    
    added_count = 0
    skipped_count = 0
    
    print(f"Found {len(df)} valid students with Enrollment Numbers. Processing...\n")

    for index, row in df.iterrows():
        enrollment_no = str(row['Enrollment No.']).strip()
        
        # Use Student Name from the first file
        name = str(row['Student Name_f1']).strip() 
        
        # --- PASSWORD GENERATION ---
        raw_mobile = str(row['Mobile Number']).replace('.0', '').strip()
        last_3_digits = raw_mobile[-3:] if len(raw_mobile) >= 3 else "123"
        raw_password = f"password{last_3_digits}"
        
        # --- EMAIL HANDLING ---
        email = str(row['E-Mail Address']).strip()
        if email.lower() == 'nan' or not email:
            email = f"{enrollment_no.lower()}@univ.edu"
            
        # --- DEPARTMENT HANDLING ---
        department = str(row.get('Course Name', 'B.Tech')).strip()
        if department.lower() == 'nan':
            department = "B.Tech"

        # Check if student already exists in database
        existing = db.query(User).filter(
            (User.email == email) | (User.inst_id == enrollment_no)
        ).first()
        
        if existing:
            print(f"⏭️  Skipped {name} ({enrollment_no}) - Already in database.")
            skipped_count += 1
            continue
            
        # Create new student record
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
        print(f"✅ Added {name} ({enrollment_no}) | Generated Pass: {raw_password}")

    # Save to database
    db.commit()
    db.close()
    
    print("\n" + "="*40)
    print(f"🎉 Import Complete!")
    print(f"Successfully added: {added_count}")
    print(f"Skipped (already existed): {skipped_count}")
    print("="*40)

if __name__ == "__main__":
    # Update these filenames to match EXACTLY what they are named on your computer
    file1 = "Student List till 22-08-2025_VS.xlsx"
    file2 = "Student List with enrollment No. Session 2025-26.xlsx"
    
    import_real_students(file1, file2)
