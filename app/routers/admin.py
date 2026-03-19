from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user, get_current_user_optional, require_role_weak
from ..database import get_db
from ..models import User, Appointment, Prescription, MedicalRecord, PatientProfile

router = APIRouter(prefix="/api/admin", tags=["Admin"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class UserAdminResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    api_key: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class StatsResponse(BaseModel):
    total_users: int
    total_patients: int
    total_doctors: int
    total_nurses: int
    total_receptionists: int
    total_admins: int
    total_appointments: int
    total_prescriptions: int
    total_records: int


@router.get("/users", response_model=List[UserAdminResponse])
def list_users(
    db: Session = Depends(get_db),
):
    """
    List all users in the system.

    VULNERABILITY B3 (Forced browsing - Easy):
    This admin endpoint has NO authentication at all.
    Anyone who knows the URL can access it.
    Exposes all user data including API keys.
    """
    # VULNERABLE: No authentication dependency — completely open
    users = db.query(User).all()
    return [
        UserAdminResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            api_key=u.api_key,
            created_at=str(u.created_at) if u.created_at else None,
        )
        for u in users
    ]


@router.get("/users/{user_id}", response_model=UserAdminResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific user by ID.

    VULNERABILITY I10 (Vertical IDOR - Easy):
    Requires authentication but does NOT check if the user is an admin.
    Any authenticated user (patient, nurse, etc.) can view any user's details
    including other users' API keys.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # VULNERABLE: No role check — any authenticated user can access admin endpoints
    return UserAdminResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        api_key=user.api_key,
        created_at=str(user.created_at) if user.created_at else None,
    )


@router.put("/users/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: int,
    update: UserUpdateRequest,
    current_user: User = Depends(require_role_weak(["admin"])),
    db: Session = Depends(get_db),
):
    """
    Update a user (admin only).

    VULNERABILITY B12 (Partial protection - Medium):
    Uses require_role_weak which has a logic flaw in case comparison.
    The middleware checks the role but the implementation has a bypass
    where case-insensitive matching lets non-admin users through.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return UserAdminResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        api_key=user.api_key,
        created_at=str(user.created_at) if user.created_at else None,
    )


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a user.
    This endpoint is correctly protected — checks admin role.
    Provided for contrast with vulnerable endpoints.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    db.delete(user)
    db.commit()
    return {"detail": "User deleted", "id": user_id}


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db),
):
    """
    Get system statistics.

    VULNERABILITY B4 (Forced browsing with API Key - Medium):
    Requires an API key, but accepts ANY valid API key from any user.
    Should require an admin API key, but checks only that the key exists
    in the database (belongs to any user).
    """
    # VULNERABLE: Accepts any valid API key, not just admin's
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")

    user = db.query(User).filter(User.api_key == api_key).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # No check if user.role == "admin"!
    return StatsResponse(
        total_users=db.query(User).count(),
        total_patients=db.query(User).filter(User.role == "patient").count(),
        total_doctors=db.query(User).filter(User.role == "doctor").count(),
        total_nurses=db.query(User).filter(User.role == "nurse").count(),
        total_receptionists=db.query(User).filter(User.role == "receptionist").count(),
        total_admins=db.query(User).filter(User.role == "admin").count(),
        total_appointments=db.query(Appointment).count(),
        total_prescriptions=db.query(Prescription).count(),
        total_records=db.query(MedicalRecord).count(),
    )
