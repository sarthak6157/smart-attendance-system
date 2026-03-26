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

    # 2. Import Students from CSV
    if os.path.exists(csv_filename):
        print(f"--> [CSV] Found file: {csv_filename}. Starting import...")
        with open(csv_filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            student_count = 0
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
                student_count += 1
        print(f"--> [CSV] Successfully read {student_count} students from the file.")
    else:
        print(f"--> [WARNING] {csv_filename} not found in the directory!")

    # 3. Commit to Database
    try:
        for u in users_list:
            db.add(u)
        db.commit()
        # FINAL SUCCESS LOG
        print(f"✅ [DATABASE] SUCCESS: Total of {len(users_list)} users (1 Admin + {len(users_list)-1} Students) are now live.")
    except Exception as e:
        db.rollback()
        print(f"❌ [DATABASE] ERROR: User seeding failed: {e}")

    return {u.inst_id: u for u in users_list}
