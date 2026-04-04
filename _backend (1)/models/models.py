"""SQLAlchemy ORM models for the Smart Attendance System."""

from datetime import datetime
import enum

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from db.database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class UserRole(str, enum.Enum):
    student  = "student"
    faculty  = "faculty"
    admin    = "admin"
    scanner  = "scanner"


class UserStatus(str, enum.Enum):
    pending  = "pending"     # awaiting admin approval
    active   = "active"
    inactive = "inactive"
    facial_required = "facial_required"  # registered but face not enrolled yet


class AttendanceMethod(str, enum.Enum):
    qr      = "qr"
    facial  = "facial"
    manual  = "manual"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent  = "absent"
    late    = "late"


class SessionStatus(str, enum.Enum):
    scheduled = "scheduled"
    active    = "active"
    closed    = "closed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    full_name   = Column(String(120), nullable=False)
    inst_id     = Column(String(50), unique=True, nullable=False, index=True)  # student/faculty ID
    email       = Column(String(150), unique=True, nullable=False, index=True)
    role        = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    status      = Column(Enum(UserStatus), default=UserStatus.pending, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    avatar_url  = Column(String(300), nullable=True)
    department  = Column(String(100), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login  = Column(DateTime, nullable=True)

    # Relationships
    biometric       = relationship("BiometricData", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sessions_taught = relationship("Session", back_populates="faculty")
    attendance_records = relationship("AttendanceRecord", back_populates="student", foreign_keys="AttendanceRecord.student_id")

    def __repr__(self):
        return f"<User {self.inst_id} ({self.role})>"


class BiometricData(Base):
    """Stores facial embeddings (base64 or path to embedding file)."""
    __tablename__ = "biometric_data"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    embedding   = Column(Text, nullable=True)      # JSON-serialised float list or file path
    image_path  = Column(String(300), nullable=True)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="biometric")


class Course(Base):
    __tablename__ = "courses"

    id          = Column(Integer, primary_key=True, index=True)
    code        = Column(String(20), unique=True, nullable=False)
    name        = Column(String(150), nullable=False)
    department  = Column(String(100), nullable=True)
    credits     = Column(Integer, default=3)
    created_at  = Column(DateTime, default=datetime.utcnow)

    sessions    = relationship("Session", back_populates="course")


class Session(Base):
    """A single class / lecture session."""
    __tablename__ = "sessions"

    id              = Column(Integer, primary_key=True, index=True)
    course_id       = Column(Integer, ForeignKey("courses.id"), nullable=False)
    faculty_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    title           = Column(String(200), nullable=True)
    qr_token        = Column(String(200), unique=True, nullable=True)   # scanned by students
    location        = Column(String(200), nullable=True)
    status          = Column(Enum(SessionStatus), default=SessionStatus.scheduled)
    scheduled_at    = Column(DateTime, nullable=False)
    started_at      = Column(DateTime, nullable=True)
    ended_at        = Column(DateTime, nullable=True)
    grace_minutes   = Column(Integer, default=15)   # window before a student is marked "late"
    created_at      = Column(DateTime, default=datetime.utcnow)

    course          = relationship("Course", back_populates="sessions")
    faculty         = relationship("User", back_populates="sessions_taught")
    attendance      = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student"),
    )

    id          = Column(Integer, primary_key=True, index=True)
    session_id  = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    student_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    method      = Column(Enum(AttendanceMethod), default=AttendanceMethod.qr)
    status      = Column(Enum(AttendanceStatus), default=AttendanceStatus.present)
    marked_at   = Column(DateTime, default=datetime.utcnow)
    notes       = Column(String(300), nullable=True)

    session     = relationship("Session", back_populates="attendance")
    student     = relationship("User", back_populates="attendance_records", foreign_keys=[student_id])
