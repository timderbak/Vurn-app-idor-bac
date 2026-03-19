import os
import shutil
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User, File

router = APIRouter(prefix="/api/files", tags=["Files"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class FileResponse_(BaseModel):
    id: int
    owner_id: int
    filename: str
    original_name: str
    file_type: Optional[str]
    uploaded_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[FileResponse_])
def list_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List files. Correctly filtered by role:
    - Patients see only their own files
    - Staff see all files
    """
    if current_user.role == "patient":
        files = db.query(File).filter(File.owner_id == current_user.id).all()
    else:
        files = db.query(File).all()

    return [
        FileResponse_(
            id=f.id,
            owner_id=f.owner_id,
            filename=f.filename,
            original_name=f.original_name,
            file_type=f.file_type,
            uploaded_at=str(f.uploaded_at) if f.uploaded_at else None,
        )
        for f in files
    ]


@router.get("/{file_id}", response_model=FileResponse_)
def get_file_info(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get file info by ID.

    VULNERABILITY I6 (IDOR in files - Easy):
    Any authenticated user can access info about any file by changing the file_id.
    No ownership check is performed.
    """
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # VULNERABLE: No ownership check
    return FileResponse_(
        id=file.id,
        owner_id=file.owner_id,
        filename=file.filename,
        original_name=file.original_name,
        file_type=file.file_type,
        uploaded_at=str(file.uploaded_at) if file.uploaded_at else None,
    )


@router.get("/download/{filename}")
def download_file(
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """
    Download a file by filename.

    VULNERABILITY I7 (IDOR via filename - Medium):
    Files are accessed by filename, and there's no check if the current user
    owns the file. An attacker can guess/enumerate filenames to download
    other users' files. Filenames are leaked through the list endpoint for staff.
    """
    file_path = UPLOAD_DIR / filename

    # VULNERABLE: No ownership check — any authenticated user can download any file by name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(file_path), filename=filename)


@router.post("/upload", response_model=FileResponse_)
def upload_file(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a file. Uses current user as owner — this endpoint is correctly implemented.
    """
    # Generate a unique filename
    import secrets
    ext = Path(file.filename).suffix if file.filename else ""
    unique_name = f"{current_user.id}_{secrets.token_hex(8)}{ext}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    db_file = File(
        owner_id=current_user.id,
        filename=unique_name,
        original_name=file.filename or "unknown",
        file_path=str(file_path),
        file_type=file.content_type,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    return FileResponse_(
        id=db_file.id,
        owner_id=db_file.owner_id,
        filename=db_file.filename,
        original_name=db_file.original_name,
        file_type=db_file.file_type,
        uploaded_at=str(db_file.uploaded_at) if db_file.uploaded_at else None,
    )


@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a file.

    VULNERABILITY (Vertical IDOR variant):
    Any authenticated user can delete any file.
    Should check ownership (file.owner_id == current_user.id) or admin role.
    """
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    # VULNERABLE: No ownership check — any user can delete any file
    file_path = Path(file.file_path)
    if file_path.exists():
        file_path.unlink()

    db.delete(file)
    db.commit()
    return {"detail": "File deleted", "id": file_id}
