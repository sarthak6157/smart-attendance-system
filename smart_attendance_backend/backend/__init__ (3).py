"""Smart Attendance System - FastAPI Backend"""

import sys
import os

# FIX: Ensure the backend directory is always on the Python path
# This fixes ModuleNotFoundError on Render
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import Base, engine
from routers import auth, users, sessions, attendance, reports, biometrics, courses

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Attendance System API", version="1.0.0")


@app.on_event("startup")
async def startup_event():
    print("App starting: Running database synchronization...")
    try:
        import seed
        seed.main()
        print("Database synchronization complete.")
    except Exception as e:
        print(f"Seed failed (non-fatal, server still runs): {e}")


origins = [
    "https://smart-attendance-portal.onrender.com",
    "https://smart-attendance-portal.onrender.com/",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,      prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,   prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["Reports"])
app.include_router(biometrics.router, prefix="/api/biometrics", tags=["Biometrics"])
app.include_router(courses.router,    prefix="/api/courses",    tags=["Courses"])


@app.get("/api/health")
def health():
    return {"status": "ok", "message": "Smart Attendance API is running"}
