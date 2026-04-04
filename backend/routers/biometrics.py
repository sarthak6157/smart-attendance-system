"""Biometrics routes: enroll face, check enrollment status, delete."""

import base64
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session as DBSession

from core.security import get_current_user, require_roles
from db.database import get_db
from models.models import BiometricData, User, UserRole, UserStatus
from schemas.schemas import BiometricEnrollRequest, BiometricOut

router = APIRouter()

# Where face images are stored on disk
FACE_STORE = Path("face_data")
FACE_STORE.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Enroll face (base64 image from webcam)
# ---------------------------------------------------------------------------

@router.post("/users/{user_id}/biometrics", response_model=BiometricOut, status_code=201)
def enroll_face(
    user_id: int,
    payload: BiometricEnrollRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """
    Accepts a base64-encoded face image captured in the browser.
    Saves the raw image to disk; in production replace this with
    a call to your face-recognition service to generate an embedding.
    """
    # Only the user themselves or an admin can enrol
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Decode base64 → raw bytes
    try:
        header, _, b64data = payload.image_base64.partition(",")
        img_bytes = base64.b64decode(b64data if b64data else payload.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data.")

    # Save image to disk
    img_path = FACE_STORE / f"user_{user_id}.jpg"
    img_path.write_bytes(img_bytes)

    # Upsert BiometricData row
    bio = db.query(BiometricData).filter(BiometricData.user_id == user_id).first()
    if bio:
        bio.image_path = str(img_path)
        bio.updated_at = datetime.utcnow()
        # embedding would be set by a real face-recognition service here
    else:
        bio = BiometricData(
            user_id    = user_id,
            image_path = str(img_path),
        )
        db.add(bio)

    # Activate the user once face is enrolled
    if user.status == UserStatus.facial_required:
        user.status = UserStatus.active

    db.commit()
    db.refresh(bio)
    return bio


# ---------------------------------------------------------------------------
# Upload face via multipart/form-data (alternative endpoint)
# ---------------------------------------------------------------------------

@router.post("/users/{user_id}/biometrics/upload", response_model=BiometricOut, status_code=201)
async def enroll_face_upload(
    user_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, or WebP images are accepted.")

    img_bytes = await file.read()
    img_path  = FACE_STORE / f"user_{user_id}.jpg"
    img_path.write_bytes(img_bytes)

    bio = db.query(BiometricData).filter(BiometricData.user_id == user_id).first()
    if bio:
        bio.image_path = str(img_path)
        bio.updated_at = datetime.utcnow()
    else:
        bio = BiometricData(user_id=user_id, image_path=str(img_path))
        db.add(bio)

    if user.status == UserStatus.facial_required:
        user.status = UserStatus.active

    db.commit()
    db.refresh(bio)
    return bio


# ---------------------------------------------------------------------------
# Check enrollment status
# ---------------------------------------------------------------------------

@router.get("/users/{user_id}/biometrics", response_model=BiometricOut)
def get_biometric_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    bio = db.query(BiometricData).filter(BiometricData.user_id == user_id).first()
    if not bio:
        raise HTTPException(status_code=404, detail="No biometric data enrolled for this user.")
    return bio


# ---------------------------------------------------------------------------
# Delete biometric data
# ---------------------------------------------------------------------------

@router.delete("/users/{user_id}/biometrics", status_code=204)
def delete_biometrics(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied.")
    bio = db.query(BiometricData).filter(BiometricData.user_id == user_id).first()
    if not bio:
        raise HTTPException(status_code=404, detail="No biometric data found.")

    # Remove image file from disk
    if bio.image_path and os.path.exists(bio.image_path):
        os.remove(bio.image_path)

    db.delete(bio)

    # Revert user status so they are prompted to re-enrol
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.status == UserStatus.active:
        user.status = UserStatus.facial_required

    db.commit()
