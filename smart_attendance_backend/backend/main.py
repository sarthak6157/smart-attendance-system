"""
Smart Attendance System – FastAPI Backend
==========================================
Run:  uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.database import Base, engine
from routers import auth, users, sessions, attendance, reports, biometrics, courses

# 1. Create database tables
Base.metadata.create_all(bind=engine)

# 2. Initialize the FastAPI app FIRST
app = FastAPI(
    title="Smart Attendance System API",
    version="1.0.0",
    description="Hybrid (QR + Facial Recognition) Attendance Management System",
)

# 3. Configure CORS - Make sure to include both versions (with and without a slash)
origins = [
    "https://smart-attendance-portal.onrender.com",
    "https://smart-attendance-portal.onrender.com/", # Added trailing slash just in case
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Register routers
app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(users.router,       prefix="/api/users",       tags=["Users"])
app.include_router(sessions.router,    prefix="/api/sessions",    tags=["Sessions"])
app.include_router(attendance.router,  prefix="/api/attendance",  tags=["Attendance"])
app.include_router(reports.router,     prefix="/api/reports",     tags=["Reports"])
app.include_router(biometrics.router,  prefix="/api/biometrics",  tags=["Biometrics"])
app.include_router(courses.router,     prefix="/api/courses",     tags=["Courses"])

# 5. Health Check Endpoint
@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Smart Attendance System"}
