"""
Smart Attendance System – FastAPI Backend
==========================================
Run:  uvicorn main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.database import Base, engine
from routers import auth, users, sessions, attendance, reports, biometrics, courses

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Attendance System API",
    version="1.0.0",
    description="Hybrid (QR + Facial Recognition) Attendance Management System",
)

# Allow requests from the frontend served on any port during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the existing frontend as static files (optional convenience)
# app.mount("/frontend", StaticFiles(directory="../frontend"), name="frontend")

# Register routers
app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(sessions.router,    prefix="/api/sessions",    tags=["Sessions"])
app.include_router(attendance.router,  prefix="/api/attendance",  tags=["Attendance"])
app.include_router(reports.router,     prefix="/api/reports",     tags=["Reports"])
app.include_router(biometrics.router,  prefix="/api/biometrics",  tags=["Biometrics"])
app.include_router(courses.router,     prefix="/api/courses",     tags=["Courses"])


@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Smart Attendance System"}
