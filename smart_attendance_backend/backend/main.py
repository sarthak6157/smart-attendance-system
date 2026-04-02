import sys
import os
sys.path.append(os.path.dirname(__file__))
```

**OR** the better fix — update your `database.py` import style everywhere.

The real issue is likely your **folder structure on Render**. Tell me:

1. What is your `main.py` location? Is it inside a subfolder like `backend/` or at the root?
2. What does your Render **Start Command** look like?

The most common cause is that your start command is:
```
uvicorn main:app ...
```
but `main.py` is inside a folder like `backend/`, so Python can't find `database.py` sitting next to it.

**Quick fix — change your Render Start Command to:**
```
cd smart_attendance_backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Or if your structure is `backend/main.py`:
```
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
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
