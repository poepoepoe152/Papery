"""Seed baseline data: subscription plans, platform super-admin, demo licenses.

Idempotent — safe to run on every startup.
"""
from . import models, security
from .config import settings
from .database import SessionLocal

PLANS = [
    {"name": "Free", "monthly_document_limit": 50, "max_users": 3, "price_cents": 0},
    {"name": "Pro", "monthly_document_limit": 500, "max_users": 10, "price_cents": 9900},
    {
        "name": "Enterprise",
        "monthly_document_limit": 5000,
        "max_users": 100,
        "price_cents": 49900,
    },
]

# Demo license keys (unbound, UNACTIVATED) so the activation flow is testable.
DEMO_LICENSES = [
    {"key": "PAPERY-FREE-DEMO-2026", "plan": "Free"},
    {"key": "PAPERY-PRO-DEMO-2026", "plan": "Pro"},
    {"key": "PAPERY-ENT-DEMO-2026", "plan": "Enterprise"},
]


def seed_data() -> None:
    db = SessionLocal()
    try:
        plan_map: dict[str, models.Plan] = {}
        for p in PLANS:
            plan = db.query(models.Plan).filter_by(name=p["name"]).first()
            if plan is None:
                plan = models.Plan(**p)
                db.add(plan)
                db.flush()
            plan_map[p["name"]] = plan

        # Platform super-admin (no company).
        sa_email = settings.SUPER_ADMIN_EMAIL.lower()
        if db.query(models.User).filter_by(email=sa_email).first() is None:
            db.add(
                models.User(
                    company_id=None,
                    email=sa_email,
                    password_hash=security.hash_password(settings.SUPER_ADMIN_PASSWORD),
                    full_name="Papery Platform Admin",
                    role=models.UserRole.SUPER_ADMIN,
                    status=models.UserStatus.ACTIVE,
                    email_verified=True,
                )
            )

        for lic in DEMO_LICENSES:
            if (
                db.query(models.License)
                .filter_by(license_key=lic["key"])
                .first()
                is None
            ):
                db.add(
                    models.License(
                        license_key=lic["key"],
                        plan_id=plan_map[lic["plan"]].id,
                        status=models.LicenseStatus.UNACTIVATED,
                        company_id=None,
                    )
                )

        db.commit()
    finally:
        db.close()
