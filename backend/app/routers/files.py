"""File upload endpoint (local storage; S3 is the production target)."""
import os

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from .. import audit, models, schemas, storage
from ..config import settings
from ..database import get_db
from ..deps import require_active_license

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=schemas.FileInfo, status_code=201)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(require_active_license),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in storage.ALLOWED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: PDF, DOCX, PNG, JPG, JPEG, TIFF",
        )

    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit"
        )
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    saved = storage.save_upload(current_user.company_id, file.filename, data)
    obj = models.FileObject(
        company_id=current_user.company_id,
        uploaded_by=current_user.id,
        storage_path=saved["storage_path"],
        original_name=file.filename,
        mime_type=file.content_type,
        size_bytes=saved["size_bytes"],
        checksum=saved["checksum"],
    )
    db.add(obj)
    audit.log(
        db,
        action="UPLOAD",
        user=current_user,
        entity_type="file",
        entity_id=obj.id,
        meta={"name": file.filename},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(obj)
    return schemas.FileInfo(
        id=obj.id,
        original_name=obj.original_name,
        size_bytes=obj.size_bytes,
        mime_type=obj.mime_type,
    )
