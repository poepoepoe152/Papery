"""FastAPI dependencies for authentication and role-based access control."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, UserStatus
from .security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise ValueError("invalid token type")
        user_id = payload["sub"]
    except Exception:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or user.status == UserStatus.DISABLED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    return user


def require_roles(*roles: str):
    """Dependency factory enforcing that the current user has one of `roles`."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return checker


def require_active_license(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    """Ensure the user's company has an ACTIVE, unexpired license."""
    from datetime import datetime, timezone

    from .models import License, LicenseStatus

    if not user.company_id:
        raise HTTPException(status_code=403, detail="No company associated with account")
    lic = (
        db.query(License)
        .filter(License.company_id == user.company_id)
        .order_by(License.created_at.desc())
        .first()
    )
    if lic is None or lic.status != LicenseStatus.ACTIVE:
        raise HTTPException(status_code=402, detail="Active license required")
    if lic.expires_at and lic.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=402, detail="License expired")
    return user
