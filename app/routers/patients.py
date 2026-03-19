from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User, PatientProfile

router = APIRouter(prefix="/api/patients", tags=["Patients"])


class PatientProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: str
    date_of_birth: Optional[str]
    blood_type: Optional[str]
    allergies: Optional[str]
    insurance_number: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    emergency_contact: Optional[str]

    class Config:
        from_attributes = True


class PatientUpdateRequest(BaseModel):
    date_of_birth: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    insurance_number: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None


@router.get("/", response_model=List[PatientProfileResponse])
def list_patients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all patient profiles."""

    profiles = db.query(PatientProfile).all()
    result = []
    for p in profiles:
        user = db.query(User).filter(User.id == p.user_id).first()
        result.append(PatientProfileResponse(
            id=p.id,
            user_id=p.user_id,
            name=user.name if user else "Unknown",
            email=user.email if user else "Unknown",
            date_of_birth=p.date_of_birth,
            blood_type=p.blood_type,
            allergies=p.allergies,
            insurance_number=p.insurance_number,
            phone=p.phone,
            address=p.address,
            emergency_contact=p.emergency_contact,
        ))
    return result


@router.get("/{patient_id}", response_model=PatientProfileResponse)
def get_patient(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific patient profile by ID."""
    profile = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")

    user = db.query(User).filter(User.id == profile.user_id).first()
    return PatientProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=user.name if user else "Unknown",
        email=user.email if user else "Unknown",
        date_of_birth=profile.date_of_birth,
        blood_type=profile.blood_type,
        allergies=profile.allergies,
        insurance_number=profile.insurance_number,
        phone=profile.phone,
        address=profile.address,
        emergency_contact=profile.emergency_contact,
    )


@router.put("/{patient_id}", response_model=PatientProfileResponse)
def update_patient(
    patient_id: int,
    update: PatientUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a patient profile."""
    profile = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = update.model_dump(exclude_unset=True)

    if "role" in update_data and update_data["role"]:
        user = db.query(User).filter(User.id == profile.user_id).first()
        if user:
            user.role = update_data["role"]

    if "user_id" in update_data and update_data["user_id"]:
        profile.user_id = update_data["user_id"]

    for field in ["date_of_birth", "blood_type", "allergies", "insurance_number", "phone", "address", "emergency_contact"]:
        if field in update_data and update_data[field] is not None:
            setattr(profile, field, update_data[field])

    db.commit()
    db.refresh(profile)

    user = db.query(User).filter(User.id == profile.user_id).first()
    return PatientProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        name=user.name if user else "Unknown",
        email=user.email if user else "Unknown",
        date_of_birth=profile.date_of_birth,
        blood_type=profile.blood_type,
        allergies=profile.allergies,
        insurance_number=profile.insurance_number,
        phone=profile.phone,
        address=profile.address,
        emergency_contact=profile.emergency_contact,
    )
