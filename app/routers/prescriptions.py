import uuid

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User, Prescription

router = APIRouter(prefix="/api/prescriptions", tags=["Prescriptions"])


class PrescriptionResponse(BaseModel):
    id: str
    patient_id: int
    doctor_id: int
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    medication: str
    dosage: str
    frequency: str
    duration: Optional[str]
    notes: Optional[str]
    status: str

    class Config:
        from_attributes = True


class PrescriptionCreateRequest(BaseModel):
    patient_id: int
    medication: str
    dosage: str
    frequency: str
    duration: Optional[str] = None
    notes: Optional[str] = None


class PrescriptionUpdateRequest(BaseModel):
    medication: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


def _enrich_prescription(rx: Prescription, db: Session) -> PrescriptionResponse:
    patient = db.query(User).filter(User.id == rx.patient_id).first()
    doctor = db.query(User).filter(User.id == rx.doctor_id).first()
    return PrescriptionResponse(
        id=rx.id,
        patient_id=rx.patient_id,
        doctor_id=rx.doctor_id,
        patient_name=patient.name if patient else None,
        doctor_name=doctor.name if doctor else None,
        medication=rx.medication,
        dosage=rx.dosage,
        frequency=rx.frequency,
        duration=rx.duration,
        notes=rx.notes,
        status=rx.status,
    )


@router.get("/", response_model=List[PrescriptionResponse])
def list_prescriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List prescriptions."""
    if current_user.role == "patient":
        prescriptions = db.query(Prescription).filter(Prescription.patient_id == current_user.id).all()
    else:
        prescriptions = db.query(Prescription).all()
    return [_enrich_prescription(rx, db) for rx in prescriptions]


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
def get_prescription(
    prescription_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific prescription by UUID."""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return _enrich_prescription(prescription, db)


@router.get("/patient/{patient_id}", response_model=List[PrescriptionResponse])
def get_patient_prescriptions(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all prescriptions for a specific patient."""
    if current_user.role == "patient":
        pass

    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).all()
    return [_enrich_prescription(rx, db) for rx in prescriptions]


@router.post("/", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(
    request: PrescriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new prescription."""
    prescription = Prescription(
        id=str(uuid.uuid4()),
        patient_id=request.patient_id,
        doctor_id=current_user.id,
        medication=request.medication,
        dosage=request.dosage,
        frequency=request.frequency,
        duration=request.duration,
        notes=request.notes,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return _enrich_prescription(prescription, db)


@router.put("/{prescription_id}", response_model=PrescriptionResponse)
def update_prescription(
    prescription_id: str,
    update: PrescriptionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a prescription."""
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(status_code=403, detail="Only doctors can update prescriptions")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(prescription, field, value)

    db.commit()
    db.refresh(prescription)
    return _enrich_prescription(prescription, db)
