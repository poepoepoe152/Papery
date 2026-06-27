"""Shared service helpers used across routers."""
from sqlalchemy.orm import Session

from . import schemas
from .models import Company, License, LicenseStatus, User


def get_license_info(db: Session, company_id) -> schemas.LicenseInfo | None:
    """Return the most relevant license summary for a company, or None."""
    if not company_id:
        return None
    lic = (
        db.query(License)
        .filter(License.company_id == company_id)
        .order_by(License.created_at.desc())
        .first()
    )
    if lic is None:
        return schemas.LicenseInfo(status=LicenseStatus.UNACTIVATED)
    return schemas.LicenseInfo(
        status=lic.status,
        plan_name=lic.plan.name if lic.plan else None,
        expires_at=lic.expires_at,
        monthly_document_limit=lic.plan.monthly_document_limit if lic.plan else None,
        max_users=lic.plan.max_users if lic.plan else None,
    )


def build_user_info(db: Session, user: User) -> schemas.UserInfo:
    company_info = None
    if user.company is not None:
        company_info = schemas.CompanyInfo(
            id=user.company.id, name=user.company.name, status=user.company.status
        )
    return schemas.UserInfo(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
        company=company_info,
        license=get_license_info(db, user.company_id),
    )
