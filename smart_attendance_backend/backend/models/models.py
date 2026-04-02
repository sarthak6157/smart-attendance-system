from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from db.database import Base

class UserRole(enum.Enum):
    admin = "admin"
    faculty = "faculty"
    student = "student"

class UserStatus(enum.Enum):
    pending = "pending"          # Student registered, needs admin approval
    facial_required = "facial_required" # Approved, but needs to enroll face
    active = "active"            # Fully ready
    inactive = "inactive"        # Suspended/Blocked

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    inst_id = Column(String, unique=True, index=True, nullable=False) # Enrollment No / Employee ID
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.student)
    status = Column(Enum(UserStatus), default=UserStatus.pending)
    department = Column(String)
    
    # --- NEW FIELD ADDED HERE ---
    section = Column(String, nullable=True) 
    
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    biometrics = relationship("BiometricData", back_populates="user", cascade="all, delete-orphan")
    attendance = relationship("AttendanceRecord", back_populates="user")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True) # e.g. CS101
    name = Column(String)
    department = Column(String)

    sessions = relationship("Session", back_populates="course")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    faculty_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    room = Column(String)
    is_active = Column(Boolean, default=True)
    qr_code_data = Column(String, unique=True)

    course = relationship("Course", back_populates="sessions")
    faculty = relationship("User")
    attendance = relationship("AttendanceRecord", back_populates="session")

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    method = Column(String) # "QR" or "Face"
    status = Column(String, default="present") # present, late

    session = relationship("Session", back_populates="attendance")
    user = relationship("User", back_populates="attendance")

class BiometricData(Base):
    __tablename__ = "biometric_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    face_encoding = Column(Text) # JSON string of the vector
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="biometrics")
