"""Smart Attendance System – FastAPI Backend"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import seed 
from db.database import Base, engine
from routers import auth, users, sessions, attendance, reports, biometrics, courses

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Attendance System API", version="1.0.0")

@app.on_event("startup")
async def startup_event():
    print("🚀 App starting: Running database synchronization...")
    try:
        seed.main()
        print("✅ Database synchronization complete.")
    except Exception as e:
        print(f"❌ Seed failed: {e}")

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

app.include_router(auth.router,       prefix="/api/auth",       tags=["Auth"])
app.include_router(users.router,      prefix="/api/users",      tags=["Users"])
app.include_router(sessions.router,   prefix="/api/sessions",   tags=["Sessions"])
app.include_router(attendance.router, prefix="/api/attendance", tags=["Attendance"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["Reports"])
app.include_router(biometrics.router, prefix="/api/biometrics", tags=["Biometrics"])
app.include_router(courses.router,     prefix="/api/courses",    tags=["Courses"])

@app.get("/api/health")
def health():
    return {"status": "ok"}
