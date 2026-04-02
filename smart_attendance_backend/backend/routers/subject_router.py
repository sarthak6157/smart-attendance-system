from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models.models import Subject, Enrollment
from schemas import SubjectCreate, SubjectResponse, EnrollmentCreate, EnrollmentResponse
from auth import get_current_user

router = APIRouter(prefix="/api/subjects", tags=["Subjects"])


@router.post("/", response_model=SubjectResponse, status_code=201)
def create_subject(data: SubjectCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = db.query(Subject).filter(Subject.code == data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Subject code already exists")
    subject = Subject(**data.dict())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/", response_model=List[SubjectResponse])
def list_subjects(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(Subject).all()


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(subject_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.post("/enroll", response_model=EnrollmentResponse, status_code=201)
def enroll_student(data: EnrollmentCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    existing = db.query(Enrollment).filter(
        Enrollment.student_id == data.student_id,
        Enrollment.subject_id == data.subject_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Student already enrolled in this subject")
    enrollment = Enrollment(**data.dict())
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment
