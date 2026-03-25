"""Database engine and session factory for Production/Local."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Get DB URL from environment, default to SQLite for local testing
DATABASE_URL = "postgresql://neondb_owner:npg_BC1xWYptXrc5@ep-frosty-pond-a4jh189q-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
# Render provides 'postgres://' but SQLAlchemy 1.4+ requires 'postgresql://'
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite requires specific connect args, Postgres does not
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency – yields a DB session, then closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
