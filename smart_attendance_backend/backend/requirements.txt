"""Pydantic schemas – request bodies and response models."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator

from models.models import AttendanceMethod, AttendanceStatus, SessionStatus, UserRole, UserStatus


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    credential: str   # inst_id or email
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    full_name: str
    inst_id: str
    email: EmailStr
    role: UserRole = UserRole.student
    password: str
    department: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters.")
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None

class UserStatusUpdate(BaseModel):
    status: UserStatus

class UserOut(BaseModel):
    id: int
    full_name: str
    inst_id: str
    email: str
    role: UserRole
    status: UserStatus
    department: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True

class UserListOut(BaseModel):
    total: int
    users: List[UserOut]


# ---------------------------------------------------------------------------
# Biometrics
# ---------------------------------------------------------------------------

class BiometricEnrollRequest(BaseModel):
    """Client sends the image as base64 string."""
    image_base64: str

class BiometricOut(BaseModel):
    user_id: int
    enrolled_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

class CourseCreate(BaseModel):
    code: str
    name: str
    department: Optional[str] = None
    credits: int = 3

class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    department: Optional[str]
    credits: int

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

class SessionCreate(BaseModel):
    course_id: int
    title: Optional[str] = None
    location: Optional[str] = None
    scheduled_at: datetime
    grace_minutes: int = 15

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    grace_minutes: Optional[int] = None

class SessionOut(BaseModel):
    id: int
    course_id: int
    faculty_id: int
    title: Optional[str]
    qr_token: Optional[str]
    location: Optional[str]
    status: SessionStatus
    scheduled_at: datetime
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    grace_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True

class SessionListOut(BaseModel):
    total: int
    sessions: List[SessionOut]


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

class AttendanceMarkQR(BaseModel):
    qr_token: str
    student_id: int  # In production, derive from JWT

class AttendanceMarkManual(BaseModel):
    session_id: int
    student_id: int
    status: AttendanceStatus = AttendanceStatus.present
    notes: Optional[str] = None

class AttendanceOut(BaseModel):
    id: int
    session_id: int
    student_id: int
    method: AttendanceMethod
    status: AttendanceStatus
    marked_at: datetime
    notes: Optional[str]

    class Config:
        from_attributes = True

class AttendanceListOut(BaseModel):
    total: int
    records: List[AttendanceOut]


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

class AttendanceSummary(BaseModel):
    student_id: int
    student_name: str
    inst_id: str
    total_sessions: int
    present: int
    absent: int
    late: int
    percentage: float

class CourseAttendanceReport(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    total_sessions: int
    summaries: List[AttendanceSummary]


# Allow forward references
TokenResponse.model_rebuild()
