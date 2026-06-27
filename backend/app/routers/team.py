"""Team management endpoints (role-based)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas, security, services
from ..database import get_db
from ..deps import require_roles

router = APIRouter(prefix="/team", tags=["team"])

_ASSIGNABLE_ROLES = {models.UserRole.ADMIN, models.UserRole.MANAGER, models.UserRole.STAFF}
_NEW_MEMBER_ROLES = {models.UserRole.MANAGER, models.UserRole.STAFF}
_VALID_STATUSES = {models.UserStatus.ACTIVE, models.UserStatus.DISABLED}


@router.get("/members", response_model=list[schemas.MemberInfo])
def list_members(
    current_user: models.User = Depends(
        require_roles(models.UserRole.ADMIN, models.UserRole.MANAGER)
    ),
    db: Session = Depends(get_db),
):
    return (
        db.query(models.User)
        .filter(models.User.company_id == current_user.company_id)
        .order_by(models.User.created_at)
        .all()
    )


@router.post("/members", response_model=schemas.MemberInfo, status_code=201)
def create_member(
    body: schemas.CreateMemberRequest,
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    if body.role not in _NEW_MEMBER_ROLES:
        raise HTTPException(status_code=400, detail="Role must be MANAGER or STAFF")

    # Enforce plan seat limit.
    info = services.get_license_info(db, current_user.company_id)
    if info and info.max_users is not None:
        active_count = (
            db.query(models.User)
            .filter(
                models.User.company_id == current_user.company_id,
                models.User.status != models.UserStatus.DISABLED,
            )
            .count()
        )
        if active_count >= info.max_users:
            raise HTTPException(
                status_code=409, detail="Maximum number of users for your plan reached"
            )

    email = body.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    member = models.User(
        company_id=current_user.company_id,
        email=email,
        password_hash=security.hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        status=models.UserStatus.ACTIVE,
        email_verified=True,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.patch("/members/{member_id}", response_model=schemas.MemberInfo)
def update_member(
    member_id: str,
    body: schemas.UpdateMemberRequest,
    current_user: models.User = Depends(require_roles(models.UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    member = (
        db.query(models.User)
        .filter(
            models.User.id == member_id,
            models.User.company_id == current_user.company_id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot modify your own account")

    if body.role is not None:
        if body.role not in _ASSIGNABLE_ROLES:
            raise HTTPException(status_code=400, detail="Invalid role")
        member.role = body.role
    if body.status is not None:
        if body.status not in _VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status")
        member.status = body.status

    db.commit()
    db.refresh(member)
    return member
