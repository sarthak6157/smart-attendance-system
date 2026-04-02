from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import auth_router, attendance_router, student_router, subject_router

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Attendance System API",
    description="API for managing student attendance",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router.router)
app.include_router(student_router.router)
app.include_router(subject_router.router)
app.include_router(attendance_router.router)


@app.get("/")
def root():
    return {"message": "Smart Attendance System API is running ✅"}


@app.get("/health")
def health():
    return {"status": "ok"}
