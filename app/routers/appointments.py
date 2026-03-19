from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User, Appointment

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    date: str
    time: str
    status: str
    notes: Optional[str]
    diagnosis: Optional[str]

    class Config:
        from_attributes = True


class AppointmentCreateRequest(BaseModel):
    patient_id: int
    doctor_id: int
    date: str
    time: str
    notes: Optional[str] = None


class AppointmentUpdateRequest(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None


def _enrich_appointment(appt: Appointment, db: Session) -> AppointmentResponse:
    patient = db.query(User).filter(User.id == appt.patient_id).first()
    doctor = db.query(User).filter(User.id == appt.doctor_id).first()
    return AppointmentResponse(
        id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        patient_name=patient.name if patient else None,
        doctor_name=doctor.name if doctor else None,
        date=appt.date,
        time=appt.time,
        status=appt.status,
        notes=appt.notes,
        diagnosis=appt.diagnosis,
    )


@router.get("/", response_model=List[AppointmentResponse])
def list_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List appointments."""
    appointments = db.query(Appointment).all()
    return [_enrich_appointment(a, db) for a in appointments]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    return _enrich_appointment(appointment, db)


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    request: AppointmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new appointment."""
    doctor = db.query(User).filter(User.id == request.doctor_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=400, detail="Invalid doctor_id")

    appointment = Appointment(
        patient_id=request.patient_id,
        doctor_id=request.doctor_id,
        date=request.date,
        time=request.time,
        notes=request.notes,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return _enrich_appointment(appointment, db)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    update: AppointmentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)
    return _enrich_appointment(appointment, db)


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
):
    """Delete an appointment."""
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db.delete(appointment)
    db.commit()
    return {"detail": "Appointment deleted", "id": appointment_id}
