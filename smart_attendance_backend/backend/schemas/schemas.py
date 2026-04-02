from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
from models.models import AttendanceStatus, UserRole


# ─── User Schemas ─────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.STUDENT


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Student Schemas ──────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    user_id: int
    roll_number: str
    department: Optional[str] = None
    semester: Optional[int] = None


class StudentResponse(BaseModel):
    id: int
    roll_number: str
    department: Optional[str]
    semester: Optional[int]
    user: UserResponse

    class Config:
        from_attributes = True


# ─── Teacher Schemas ──────────────────────────────────────────────────────────

class TeacherCreate(BaseModel):
    user_id: int
    employee_id: str
    department: Optional[str] = None


class TeacherResponse(BaseModel):
    id: int
    employee_id: str
    department: Optional[str]
    user: UserResponse

    class Config:
        from_attributes = True


# ─── Subject Schemas ──────────────────────────────────────────────────────────

class SubjectCreate(BaseModel):
    name: str
    code: str
    teacher_id: int
    department: Optional[str] = None
    semester: Optional[int] = None


class SubjectResponse(BaseModel):
    id: int
    name: str
    code: str
    department: Optional[str]
    semester: Optional[int]
    teacher: TeacherResponse

    class Config:
        from_attributes = True


# ─── Enrollment Schemas ───────────────────────────────────────────────────────

class EnrollmentCreate(BaseModel):
    student_id: int
    subject_id: int


class EnrollmentResponse(BaseModel):
    id: int
    student_id: int
    subject_id: int
    enrolled_at: datetime

    class Config:
        from_attributes = True


# ─── Attendance Session Schemas ───────────────────────────────────────────────

class AttendanceSessionCreate(BaseModel):
    subject_id: int
    session_date: date
    start_time: time
    end_time: Optional[time] = None
    notes: Optional[str] = None


class AttendanceSessionResponse(BaseModel):
    id: int
    subject_id: int
    session_date: date
    start_time: time
    end_time: Optional[time]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Attendance Schemas ───────────────────────────────────────────────────────

class AttendanceCreate(BaseModel):
    session_id: int
    student_id: int
    status: AttendanceStatus = AttendanceStatus.PRESENT
    remarks: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    session_id: int
    records: List[dict]  # [{"student_id": 1, "status": "present"}, ...]


class AttendanceUpdate(BaseModel):
    status: AttendanceStatus
    remarks: Optional[str] = None


class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: AttendanceStatus
    marked_at: datetime
    remarks: Optional[str]

    class Config:
        from_attributes = True


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
