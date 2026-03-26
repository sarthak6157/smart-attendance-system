"""
Smart Attendance System – FastAPI Backend
==========================================
Run:  uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 1. Import seed to enable auto-synchronization
import seed 

from db.database import Base, engine
from routers import auth, users, sessions, attendance, reports, biometrics, courses

# 2. Create database tables
Base.metadata.create_all(bind=engine)

# 3. Initialize the FastAPI app
app = FastAPI(
    title="Smart Attendance System API",
    version="1.0.0",
    description="Hybrid (QR + Facial Recognition) Attendance Management System",
)

# 4. Auto-Sync Logic on Startup
# This ensures your 187 students are imported every time the server starts
@app.on_event("startup")
async def startup_event():
    print("🚀 App starting: Running database synchronization...")
    try:
        # This calls the main() function in your seed.py file
        seed.main()
        print("✅ Database synchronization complete.")
    except Exception as e:
        print(f"❌ Seed failed: {e}")

# 5. Configure CORS
# Ensure your frontend URL is listed here correctly
origins = [
    "https://smart-attendance-portal.onrender.com",
    "https://smart-attendance-portal.onrender.com/",
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

# 6. Register routers
app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,      prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,   prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["Reports"])
app.include_router(biometrics.router, prefix="/api/biometrics", tags=["Biometrics"])
app.include_router(courses.router,     prefix="/api/courses",    tags=["Courses"])

# 7. Health Check Endpoint
@app.get("/api/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "Smart Attendance System"}
