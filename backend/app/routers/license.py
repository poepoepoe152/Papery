"""Company license endpoints: view + activate."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, services
from ..config import settings
from ..database import get_db
from ..deps import get_current_user, require_roles

router = APIRouter(prefix="/license", tags=["license"])


@router.get("", response_model=schemas.LicenseInfo)
def get_license(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    info = services.get_license_info(db, current_user.company_id)
    if info is None:
        return schemas.LicenseInfo(status=models.LicenseStatus.UNACTIVATED)
    return info


@router.post("/activate", response_model=schemas.LicenseInfo)
def activate_license(
    body: schemas.ActivateRequest,
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated with account")

    key = body.license_key.strip().upper()
    lic = db.query(models.License).filter(models.License.license_key == key).first()
    if lic is None:
        raise HTTPException(status_code=404, detail="Invalid license key")

    # Reject keys already bound to a different company.
    if lic.company_id and lic.company_id != current_user.company_id:
        raise HTTPException(status_code=409, detail="License key is already in use")
    if lic.status in (models.LicenseStatus.SUSPENDED, models.LicenseStatus.EXPIRED):
        raise HTTPException(status_code=409, detail=f"License is {lic.status.lower()}")

    now = datetime.now(timezone.utc)
    lic.company_id = current_user.company_id
    lic.status = models.LicenseStatus.ACTIVE
    lic.activated_at = now
    lic.expires_at = now + timedelta(days=settings.LICENSE_DURATION_DAYS)

    company = db.query(models.Company).filter(
        models.Company.id == current_user.company_id
    ).first()
    if company is not None:
        company.status = models.CompanyStatus.ACTIVE

    db.commit()
    return services.get_license_info(db, current_user.company_id)
