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
    """
    List prescriptions.
    This endpoint has PARTIAL protection: filters by role.
    - Patients see only their own prescriptions.
    - Doctors/nurses see all prescriptions.
    - This is intentionally "correct" to provide contrast with vulnerable endpoints.
    """
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
    """
    Get a specific prescription by UUID.

    VULNERABILITY I4 (Horizontal IDOR with UUID - Medium):
    Although using UUIDs (harder to enumerate than sequential IDs),
    a patient can still access other patients' prescriptions if they
    obtain the UUID (e.g., from the listing endpoint which leaks all IDs
    for non-patient roles, or from other information disclosure).
    No ownership check is performed.
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # VULNERABLE: No ownership check — any authenticated user can access any prescription
    return _enrich_prescription(prescription, db)


@router.get("/patient/{patient_id}", response_model=List[PrescriptionResponse])
def get_patient_prescriptions(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all prescriptions for a specific patient.

    VULNERABILITY I12-variant (Parameter Tampering / Horizontal IDOR - Medium):
    A patient can change the patient_id to view another patient's prescriptions.
    Partial protection: checks if user is patient role, but uses the URL param
    instead of current_user.id.
    """
    # VULNERABLE: Checks the role but uses URL parameter instead of current_user.id
    if current_user.role == "patient":
        # BUG: Should check `patient_id == current_user.id` but doesn't
        pass

    prescriptions = db.query(Prescription).filter(Prescription.patient_id == patient_id).all()
    return [_enrich_prescription(rx, db) for rx in prescriptions]


@router.post("/", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_prescription(
    request: PrescriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new prescription.

    VULNERABILITY I9 (Vertical IDOR - Medium):
    This endpoint should be restricted to doctors only.
    But it only checks that the user is authenticated, not their role.
    A nurse or even a patient can create prescriptions.
    """
    # VULNERABLE: No role check — should require role == "doctor"
    prescription = Prescription(
        id=str(uuid.uuid4()),
        patient_id=request.patient_id,
        doctor_id=current_user.id,  # Uses current user as doctor, but doesn't verify they're actually a doctor
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
    """
    Update a prescription.

    VULNERABILITY B6 (Missing object-level AC - Medium):
    Checks that the user is a doctor, but does NOT verify that
    the doctor is the one who created the prescription (ownership check).
    Any doctor can modify any other doctor's prescriptions.
    """
    prescription = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    # Partial protection: checks role...
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(status_code=403, detail="Only doctors can update prescriptions")

    # VULNERABLE B6: ...but does NOT check ownership (prescription.doctor_id == current_user.id)
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(prescription, field, value)

    db.commit()
    db.refresh(prescription)
    return _enrich_prescription(prescription, db)
