"""Audit trail helper."""
from sqlalchemy.orm import Session

from . import models


def log(
    db: Session,
    *,
    action: str,
    user: models.User | None = None,
    company_id=None,
    entity_type: str | None = None,
    entity_id=None,
    meta: dict | None = None,
    ip_address: str | None = None,
) -> None:
    entry = models.AuditLog(
        company_id=company_id or (user.company_id if user else None),
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta=meta,
        ip_address=ip_address,
    )
    db.add(entry)
