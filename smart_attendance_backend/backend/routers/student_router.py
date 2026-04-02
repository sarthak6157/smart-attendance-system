from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.models import Student
from schemas import StudentCreate, StudentResponse
from auth import get_current_user

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.post("/", response_model=StudentResponse, status_code=201)
def create_student(data: StudentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = db.query(Student).filter(Student.roll_number == data.roll_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Roll number already exists")
    student = Student(**data.dict())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/", response_model=List[StudentResponse])
def list_students(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Student).all()


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.delete("/{student_id}", status_code=204)
def delete_student(student_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
