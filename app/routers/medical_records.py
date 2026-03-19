from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user, get_current_user_optional
from ..database import get_db
from ..models import User, MedicalRecord

router = APIRouter(prefix="/api/records", tags=["Medical Records"])


class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    record_type: str
    result: Optional[str]
    notes: Optional[str]
    file_path: Optional[str]

    class Config:
        from_attributes = True


class MedicalRecordCreateRequest(BaseModel):
    patient_id: int
    record_type: str  # blood_test, xray, mri, general_checkup
    result: Optional[str] = None
    notes: Optional[str] = None
    file_path: Optional[str] = None


def _enrich_record(rec: MedicalRecord, db: Session) -> MedicalRecordResponse:
    patient = db.query(User).filter(User.id == rec.patient_id).first()
    doctor = db.query(User).filter(User.id == rec.doctor_id).first()
    return MedicalRecordResponse(
        id=rec.id,
        patient_id=rec.patient_id,
        doctor_id=rec.doctor_id,
        patient_name=patient.name if patient else None,
        doctor_name=doctor.name if doctor else None,
        record_type=rec.record_type,
        result=rec.result,
        notes=rec.notes,
        file_path=rec.file_path,
    )


@router.get("/", response_model=List[MedicalRecordResponse])
def list_records(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List medical records.
    This endpoint has CORRECT protection for contrast:
    - Patients see only their own records
    - Doctors see records of their patients
    - Admins see all
    """
    if current_user.role == "patient":
        records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == current_user.id).all()
    elif current_user.role == "doctor":
        records = db.query(MedicalRecord).filter(MedicalRecord.doctor_id == current_user.id).all()
    else:
        records = db.query(MedicalRecord).all()
    return [_enrich_record(r, db) for r in records]


@router.get("/{record_id}", response_model=MedicalRecordResponse)
def get_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific medical record.

    VULNERABILITY I5 (Horizontal IDOR - Easy):
    Patient can view any patient's medical records by changing the ID.
    Authentication is required, but no ownership check.
    """
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    # VULNERABLE: No ownership check
    return _enrich_record(record, db)


@router.get("/patient/{patient_id}", response_model=List[MedicalRecordResponse])
def get_patient_records(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all medical records for a specific patient.

    VULNERABILITY I12 (Parameter Tampering - Medium):
    Patient can change patient_id in the URL to view another patient's records.
    Has partial protection: checks if user is a patient, but then uses URL param.
    """
    if current_user.role == "patient":
        # VULNERABLE: Should check patient_id == current_user.id, but doesn't enforce it
        # The intent was to filter, but the developer forgot the actual check
        pass

    records = db.query(MedicalRecord).filter(MedicalRecord.patient_id == patient_id).all()
    return [_enrich_record(r, db) for r in records]


@router.post("/", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    request: MedicalRecordCreateRequest,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Create a new medical record.

    VULNERABILITY B5 (Forced browsing - Medium):
    This endpoint uses get_current_user_optional instead of get_current_user.
    It accepts unauthenticated requests — no auth required at all.
    Also no role check — anyone (or no one) can create medical records.
    """
    # VULNERABLE: Uses optional auth — works even without authentication
    doctor_id = current_user.id if current_user else 0

    record = MedicalRecord(
        patient_id=request.patient_id,
        doctor_id=doctor_id,
        record_type=request.record_type,
        result=request.result,
        notes=request.notes,
        file_path=request.file_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _enrich_record(record, db)


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a medical record.

    VULNERABILITY B8 (Method-based bypass - Medium):
    GET /{record_id} requires authentication.
    DELETE /{record_id} does NOT require authentication at all.
    Compare the two endpoints — GET has Depends(get_current_user), DELETE doesn't.
    """
    # VULNERABLE: No authentication at all
    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    db.delete(record)
    db.commit()
    return {"detail": "Medical record deleted", "id": record_id}
