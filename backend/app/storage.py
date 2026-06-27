"""Local filesystem storage (S3 is the production target).

Files are stored under STORAGE_DIR, namespaced by company for isolation.
"""
import hashlib
import os
import uuid

from .config import settings

ALLOWED_EXTS = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_upload(company_id, original_name: str, data: bytes) -> dict:
    ext = os.path.splitext(original_name)[1].lower()
    company_dir = os.path.join(settings.STORAGE_DIR, str(company_id))
    ensure_dir(company_dir)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(company_dir, stored_name)
    with open(path, "wb") as fh:
        fh.write(data)
    return {
        "storage_path": path,
        "size_bytes": len(data),
        "checksum": hashlib.sha256(data).hexdigest(),
    }


def reports_dir(company_id) -> str:
    path = os.path.join(settings.STORAGE_DIR, str(company_id), "reports")
    ensure_dir(path)
    return path
