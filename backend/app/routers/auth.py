"""Authentication endpoints: register, login, refresh, me, logout, password reset."""
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import email as email_service
from .. import models, schemas, security, services
from ..config import settings
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.AuthResponse, status_code=201)
def register(body: schemas.RegisterRequest, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    company = models.Company(name=body.company_name, status=models.CompanyStatus.PENDING)
    db.add(company)
    db.flush()

    user = models.User(
        company_id=company.id,
        email=email,
        password_hash=security.hash_password(body.password),
        full_name=body.full_name,
        role=models.UserRole.ADMIN,
        status=models.UserStatus.ACTIVE,
        email_verified=True,  # email verification arrives in a later phase
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return schemas.AuthResponse(
        access_token=security.create_access_token(user),
        refresh_token=security.create_refresh_token(user),
        user=services.build_user_info(db, user),
    )


@router.post("/login", response_model=schemas.AuthResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = body.email.lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None or not security.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if user.status == models.UserStatus.DISABLED:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return schemas.AuthResponse(
        access_token=security.create_access_token(user),
        refresh_token=security.create_refresh_token(user),
        user=services.build_user_info(db, user),
    )


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh(body: schemas.RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = security.decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("invalid token type")
        user_id = payload["sub"]
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None or user.status == models.UserStatus.DISABLED:
        raise HTTPException(status_code=401, detail="User not found or disabled")

    return schemas.TokenResponse(
        access_token=security.create_access_token(user),
        refresh_token=security.create_refresh_token(user),
    )


@router.get("/me", response_model=schemas.UserInfo)
def me(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return services.build_user_info(db, current_user)


@router.post("/logout", response_model=schemas.MessageResponse)
def logout(current_user: models.User = Depends(get_current_user)):
    # Stateless JWTs: client discards tokens. Server-side revocation list is a
    # later-phase enhancement.
    return schemas.MessageResponse(message="Logged out")


_GENERIC_RESET_MSG = "If that email is registered, a reset link has been sent."


@router.post("/forgot-password", response_model=schemas.MessageResponse)
def forgot_password(body: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Always return the same message so the endpoint can't be used to probe
    # which emails exist.
    email = body.email.lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is not None:
        token = secrets.token_urlsafe(32)
        reset = models.PasswordReset(
            user_id=user.id,
            token_hash=security.hash_token(token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
            used=False,
        )
        db.add(reset)
        db.commit()
        link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        email_service.send_email(
            email,
            "Reset your Papery password",
            f"Hi {user.full_name},\n\n"
            f"We received a request to reset your Papery password. "
            f"Use the link below within "
            f"{settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes:\n\n{link}\n\n"
            f"If you didn't request this, you can ignore this email.",
        )
    return schemas.MessageResponse(message=_GENERIC_RESET_MSG)


@router.post("/reset-password", response_model=schemas.MessageResponse)
def reset_password(body: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    token_hash = security.hash_token(body.token)
    reset = (
        db.query(models.PasswordReset)
        .filter(
            models.PasswordReset.token_hash == token_hash,
            models.PasswordReset.used.is_(False),
        )
        .first()
    )
    now = datetime.now(timezone.utc)
    if reset is None or reset.expires_at < now:
        raise HTTPException(
            status_code=400, detail="This reset link is invalid or has expired."
        )
    user = db.query(models.User).filter(models.User.id == reset.user_id).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Account no longer exists.")

    user.password_hash = security.hash_password(body.new_password)
    reset.used = True
    # Invalidate any other outstanding reset tokens for this user.
    db.query(models.PasswordReset).filter(
        models.PasswordReset.user_id == user.id,
        models.PasswordReset.used.is_(False),
    ).update({"used": True})
    db.commit()
    return schemas.MessageResponse(message="Password updated. You can now log in.")
