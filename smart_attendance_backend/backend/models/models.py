import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Enum as SAEnum, Date, Time, Text
)
from sqlalchemy.orm import relationship
from database import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class AttendanceStatus(enum.Enum):
    PRESENT = "present"
    ABSENT  = "absent"
    LATE    = "late"
    EXCUSED = "excused"


class UserRole(enum.Enum):
    ADMIN   = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


# ─── Models ───────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student       = relationship("Student", back_populates="user", uselist=False)
    teacher       = relationship("Teacher", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = "students"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    roll_number   = Column(String(20), unique=True, nullable=False)
    department    = Column(String(100))
    semester      = Column(Integer)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user          = relationship("User", back_populates="student")
    attendances   = relationship("Attendance", back_populates="student")
    enrollments   = relationship("Enrollment", back_populates="student")


class Teacher(Base):
    __tablename__ = "teachers"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    employee_id   = Column(String(20), unique=True, nullable=False)
    department    = Column(String(100))
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user          = relationship("User", back_populates="teacher")
    subjects      = relationship("Subject", back_populates="teacher")


class Subject(Base):
    __tablename__ = "subjects"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(150), nullable=False)
    code          = Column(String(20), unique=True, nullable=False)
    teacher_id    = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    department    = Column(String(100))
    semester      = Column(Integer)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    teacher       = relationship("Teacher", back_populates="subjects")
    sessions      = relationship("AttendanceSession", back_populates="subject")
    enrollments   = relationship("Enrollment", back_populates="subject")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id            = Column(Integer, primary_key=True, index=True)
    student_id    = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id    = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    enrolled_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student       = relationship("Student", back_populates="enrollments")
    subject       = relationship("Subject", back_populates="enrollments")


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"

    id            = Column(Integer, primary_key=True, index=True)
    subject_id    = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    session_date  = Column(Date, nullable=False)
    start_time    = Column(Time, nullable=False)
    end_time      = Column(Time, nullable=True)
    notes         = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subject       = relationship("Subject", back_populates="sessions")
    attendances   = relationship("Attendance", back_populates="session")


class Attendance(Base):
    __tablename__ = "attendances"

    id            = Column(Integer, primary_key=True, index=True)
    session_id    = Column(Integer, ForeignKey("attendance_sessions.id"), nullable=False)
    student_id    = Column(Integer, ForeignKey("students.id"), nullable=False)
    status        = Column(SAEnum(AttendanceStatus), default=AttendanceStatus.ABSENT, nullable=False)
    marked_at     = Column(DateTime, default=datetime.utcnow)
    remarks       = Column(Text, nullable=True)

    # Relationships
    session       = relationship("AttendanceSession", back_populates="attendances")
    student       = relationship("Student", back_populates="attendances")
