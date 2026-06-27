"""Platform admin endpoints (SUPER_ADMIN only)."""
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles

router = APIRouter(prefix="/admin", tags=["admin"])

_super = require_roles(models.UserRole.SUPER_ADMIN)


@router.get("/stats", response_model=schemas.AdminStats)
def stats(_: models.User = Depends(_super), db: Session = Depends(get_db)):
    companies = db.query(func.count(models.Company.id)).scalar() or 0
    active = (
        db.query(func.count(models.Company.id))
        .filter(models.Company.status == models.CompanyStatus.ACTIVE)
        .scalar()
        or 0
    )
    users = db.query(func.count(models.User.id)).scalar() or 0
    verifications = db.query(func.count(models.Verification.id)).scalar() or 0
    docs = db.query(func.count(models.Document.id)).scalar() or 0

    # MRR = sum of plan prices for companies with an active license.
    mrr = (
        db.query(func.coalesce(func.sum(models.Plan.price_cents), 0))
        .select_from(models.License)
        .join(models.Plan, models.License.plan_id == models.Plan.id)
        .filter(models.License.status == models.LicenseStatus.ACTIVE)
        .scalar()
        or 0
    )
    return schemas.AdminStats(
        companies=companies, active_companies=active, users=users,
        verifications=verifications, documents_processed=docs, mrr_cents=int(mrr),
    )


@router.get("/companies", response_model=list[schemas.AdminCompany])
def list_companies(_: models.User = Depends(_super), db: Session = Depends(get_db)):
    out = []
    for c in db.query(models.Company).order_by(models.Company.created_at.desc()).all():
        lic = (
            db.query(models.License)
            .filter(models.License.company_id == c.id)
            .order_by(models.License.created_at.desc())
            .first()
        )
        user_count = (
            db.query(func.count(models.User.id))
            .filter(models.User.company_id == c.id)
            .scalar()
            or 0
        )
        docs_used = (
            db.query(func.coalesce(func.sum(models.UsageCounter.documents_used), 0))
            .filter(models.UsageCounter.company_id == c.id)
            .scalar()
            or 0
        )
        out.append(schemas.AdminCompany(
            id=c.id, name=c.name, status=c.status,
            plan_name=lic.plan.name if lic and lic.plan else None,
            license_status=lic.status if lic else None,
            expires_at=lic.expires_at if lic else None,
            user_count=user_count, documents_used=int(docs_used),
        ))
    return out


@router.patch("/companies/{company_id}", response_model=schemas.MessageResponse)
def set_company_status(
    company_id: str,
    status: str,
    _: models.User = Depends(_super),
    db: Session = Depends(get_db),
):
    valid = {
        models.CompanyStatus.ACTIVE,
        models.CompanyStatus.SUSPENDED,
        models.CompanyStatus.EXPIRED,
    }
    if status not in valid:
        raise HTTPException(status_code=400, detail="Invalid status")
    c = db.query(models.Company).filter(models.Company.id == company_id).first()
    if c is None:
        raise HTTPException(status_code=404, detail="Company not found")
    c.status = status
    # Suspending a company suspends its active licenses too.
    if status == models.CompanyStatus.SUSPENDED:
        for lic in db.query(models.License).filter(models.License.company_id == c.id):
            if lic.status == models.LicenseStatus.ACTIVE:
                lic.status = models.LicenseStatus.SUSPENDED
    elif status == models.CompanyStatus.ACTIVE:
        for lic in db.query(models.License).filter(models.License.company_id == c.id):
            if lic.status == models.LicenseStatus.SUSPENDED:
                lic.status = models.LicenseStatus.ACTIVE
    db.commit()
    return schemas.MessageResponse(message="Updated")


@router.get("/plans", response_model=list[schemas.AdminPlanInfo])
def list_plans(_: models.User = Depends(_super), db: Session = Depends(get_db)):
    return db.query(models.Plan).order_by(models.Plan.price_cents).all()


@router.get("/licenses", response_model=list[schemas.AdminLicenseInfo])
def list_licenses(_: models.User = Depends(_super), db: Session = Depends(get_db)):
    out = []
    for lic in db.query(models.License).order_by(models.License.created_at.desc()).all():
        out.append(schemas.AdminLicenseInfo(
            id=lic.id, license_key=lic.license_key,
            plan_name=lic.plan.name if lic.plan else None, status=lic.status,
            company_name=lic.company.name if lic.company else None,
            expires_at=lic.expires_at,
        ))
    return out


@router.post("/licenses", response_model=schemas.AdminLicenseInfo, status_code=201)
def create_license(
    body: schemas.AdminLicenseCreate,
    _: models.User = Depends(_super),
    db: Session = Depends(get_db),
):
    plan = db.query(models.Plan).filter(models.Plan.id == body.plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    key = (body.license_key or "").strip().upper()
    if not key:
        prefix = "".join(ch for ch in plan.name.upper() if ch.isalnum())[:4]
        key = f"PAPERY-{prefix}-{secrets.token_hex(4).upper()}"
    if db.query(models.License).filter(models.License.license_key == key).first():
        raise HTTPException(status_code=409, detail="License key already exists")
    lic = models.License(
        license_key=key, plan_id=plan.id,
        status=models.LicenseStatus.UNACTIVATED, company_id=None,
    )
    db.add(lic)
    db.commit()
    db.refresh(lic)
    return schemas.AdminLicenseInfo(
        id=lic.id, license_key=lic.license_key, plan_name=plan.name,
        status=lic.status, company_name=None, expires_at=None,
    )
