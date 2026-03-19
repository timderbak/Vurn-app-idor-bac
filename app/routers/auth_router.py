from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    # VULNERABILITY B9: Mass assignment — role field is accepted in registration
    role: str = "patient"
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    role: str
    api_key: Optional[str]


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    role: str
    api_key: Optional[str]

    class Config:
        from_attributes = True


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password. Returns JWT token."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(data={"sub": user.id, "role": user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        role=user.role,
        api_key=user.api_key,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    VULNERABILITY B9 (Mass Assignment - Easy):
    The 'role' field is accepted directly from user input.
    An attacker can register as admin/doctor by including role in the request body.
    """
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # VULNERABLE: role is taken directly from user input without validation
    import secrets
    api_key = f"pk_{request.role}_{request.name.split()[0].lower()}_{secrets.token_hex(4)}"

    user = User(
        email=request.email,
        name=request.name,
        hashed_password=get_password_hash(request.password),
        role=request.role,  # VULNERABLE: should be hardcoded to "patient"
        api_key=api_key,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh JWT token."""
    access_token = create_access_token(data={"sub": current_user.id, "role": current_user.role})
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=current_user.id,
        role=current_user.role,
        api_key=current_user.api_key,
    )
