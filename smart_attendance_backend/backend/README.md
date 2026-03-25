# Smart Attendance System – Backend

A FastAPI backend for the Hybrid (QR + Facial Recognition) Attendance Management System.

---

## Quick Start

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Seed demo data
```bash
python seed.py
```
This creates `attendance.db` (SQLite) with all demo accounts, courses, sessions, and attendance records.

### 3. Run the server
```bash
uvicorn main:app --reload --port 8000
```

### 4. Open API docs
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**:      http://localhost:8000/redoc

---

## Demo Accounts

| Username       | Password  | Role                            |
|----------------|-----------|---------------------------------|
| `student1`     | Pass@123  | Student (active)                |
| `student2`     | Pass@123  | Student (active)                |
| `student3`     | Pass@123  | Student (active)                |
| `pending_user` | Pass@123  | Student (pending approval)      |
| `facial_user`  | Pass@123  | Student (facial enrolment req.) |
| `faculty1`     | Pass@123  | Faculty                         |
| `faculty2`     | Pass@123  | Faculty                         |
| `admin1`       | Pass@123  | Administrator                   |
| `scanner_user` | Pass@123  | Scanner Operator                |

---

## Project Structure

```
backend/
├── main.py              ← App entry point & router registration
├── seed.py              ← Demo data seeder
├── requirements.txt
├── db/
│   └── database.py      ← SQLAlchemy engine, SessionLocal, get_db()
├── models/
│   └── models.py        ← ORM: User, Session, AttendanceRecord, Course, BiometricData
├── schemas/
│   └── schemas.py       ← Pydantic request/response models
├── core/
│   └── security.py      ← JWT auth, password hashing, role guards
└── routers/
    ├── auth.py          ← /api/auth/*
    ├── users.py         ← /api/users/*
    ├── sessions.py      ← /api/sessions/*
    ├── attendance.py    ← /api/attendance/*
    ├── reports.py       ← /api/reports/*
    ├── biometrics.py    ← /api/biometrics/*
    └── courses.py       ← /api/courses/*
```

---

## API Reference

### Auth  `/api/auth`
| Method | Path                | Description                        |
|--------|---------------------|------------------------------------|
| POST   | `/register`         | Register new user                  |
| POST   | `/login`            | Login → JWT token                  |
| GET    | `/me`               | Get current user                   |
| POST   | `/change-password`  | Change own password                |
| POST   | `/forgot-password`  | Request password reset email       |

### Users  `/api/users`
| Method | Path                    | Roles           |
|--------|-------------------------|-----------------|
| GET    | `/`                     | Admin, Faculty  |
| GET    | `/{id}`                 | Self or Admin   |
| PATCH  | `/{id}`                 | Self or Admin   |
| PATCH  | `/{id}/status`          | Admin           |
| DELETE | `/{id}`                 | Admin           |
| GET    | `/pending/list`         | Admin           |
| POST   | `/bulk-approve`         | Admin           |

### Sessions  `/api/sessions`
| Method | Path                     | Roles           |
|--------|--------------------------|-----------------|
| POST   | `/`                      | Faculty, Admin  |
| GET    | `/`                      | All auth        |
| GET    | `/{id}`                  | All auth        |
| PATCH  | `/{id}`                  | Owner or Admin  |
| POST   | `/{id}/start`            | Owner or Admin  |
| POST   | `/{id}/end`              | Owner or Admin  |
| POST   | `/{id}/refresh-qr`       | Owner or Admin  |
| DELETE | `/{id}`                  | Admin           |

### Attendance  `/api/attendance`
| Method | Path                       | Description                          |
|--------|----------------------------|--------------------------------------|
| POST   | `/qr`                      | Mark present via QR token            |
| POST   | `/facial`                  | Mark present via facial recognition  |
| POST   | `/manual`                  | Manual mark (Faculty / Admin)        |
| GET    | `/session/{session_id}`    | All records for a session            |
| GET    | `/student/{student_id}`    | History for a student                |
| DELETE | `/{record_id}`             | Delete record (Admin)                |

### Reports  `/api/reports`
| Method | Path                          | Description                  |
|--------|-------------------------------|------------------------------|
| GET    | `/overview`                   | Admin dashboard stats        |
| GET    | `/course/{course_id}`         | Course attendance report     |
| GET    | `/course/{course_id}/export`  | Download CSV                 |
| GET    | `/student/{student_id}`       | Student summary              |

### Biometrics  `/api/biometrics`
| Method | Path                              | Description             |
|--------|-----------------------------------|-------------------------|
| POST   | `/users/{id}/biometrics`          | Enrol face (base64)     |
| POST   | `/users/{id}/biometrics/upload`   | Enrol face (file upload)|
| GET    | `/users/{id}/biometrics`          | Check enrolment status  |
| DELETE | `/users/{id}/biometrics`          | Delete biometric data   |

### Courses  `/api/courses`
| Method | Path          | Roles   |
|--------|---------------|---------|
| GET    | `/`           | All     |
| POST   | `/`           | Admin   |
| GET    | `/{id}`       | All     |
| DELETE | `/{id}`       | Admin   |

---

## Connecting the Frontend

Replace the hardcoded JS accounts in `login_page.html` with real API calls.

### Login
```javascript
const res = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ credential, password })
});
const { access_token, user } = await res.json();
localStorage.setItem('token', access_token);
localStorage.setItem('user', JSON.stringify(user));

// Redirect based on role
const redirects = {
  student: './student_dashboard.html',
  faculty: './faculty_dashboard.html',
  admin:   './admin_dashboard.html',
  scanner: './scan_page.html',
};
window.location.href = redirects[user.role];
```

### Authenticated requests
```javascript
const token = localStorage.getItem('token');
const res = await fetch('http://localhost:8000/api/sessions', {
  headers: { 'Authorization': `Bearer ${token}` }
});
```

### QR Attendance
```javascript
// student scans QR → reads the qr_token value → POST
await fetch('http://localhost:8000/api/attendance/qr', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ qr_token: scannedValue, student_id: user.id })
});
```

### Facial Enrolment
```javascript
// Capture webcam frame as base64, then POST
await fetch(`http://localhost:8000/api/biometrics/users/${user.id}/biometrics`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ image_base64: canvas.toDataURL('image/jpeg') })
});
```

---

## Switching to PostgreSQL

In `db/database.py`, replace the SQLite URL:
```python
DATABASE_URL = "postgresql://user:password@localhost/attendance_db"
```
And remove `connect_args={"check_same_thread": False}`.

---

## Production Checklist
- [ ] Change `SECRET_KEY` in `core/security.py` to a long random string
- [ ] Switch `DATABASE_URL` to PostgreSQL
- [ ] Set `allow_origins` in CORS to your frontend domain only
- [ ] Use environment variables (python-dotenv) for all secrets
- [ ] Integrate a real face-recognition service (e.g., face_recognition lib, AWS Rekognition)
- [ ] Add email sending for password reset (e.g., FastAPI-Mail)
- [ ] Run behind a reverse proxy (nginx) with HTTPS
