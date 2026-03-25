"""Database engine and session factory."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite for development – swap for PostgreSQL in production:
# DATABASE_URL = "postgresql://user:password@localhost/attendance_db"
DATABASE_URL = "sqlite:///./attendance.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency – yields a DB session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
