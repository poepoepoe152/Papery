"""SQLAlchemy ORM models for the Phase 2 foundation.

Implements the auth + tenancy bounded contexts from the architecture document
(plans, companies, licenses, users). OCR/extraction/comparison tables come in
later phases.
"""
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


# --- Enumerated string constants (kept as plain strings for portability) ---
class UserRole:
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    STAFF = "STAFF"


class UserStatus:
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    DISABLED = "DISABLED"


class CompanyStatus:
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"


class LicenseStatus:
    UNACTIVATED = "UNACTIVATED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Plan(Base, TimestampMixin):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String, unique=True, nullable=False)
    monthly_document_limit = Column(Integer, nullable=False, default=100)
    max_users = Column(Integer, nullable=False, default=5)
    price_cents = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, default=CompanyStatus.PENDING)

    users = relationship("User", back_populates="company")
    licenses = relationship("License", back_populates="company")


class License(Base, TimestampMixin):
    __tablename__ = "licenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    license_key = Column(String, unique=True, nullable=False, index=True)
    status = Column(String, nullable=False, default=LicenseStatus.UNACTIVATED)
    activated_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    plan = relationship("Plan")
    company = relationship("Company", back_populates="licenses")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default=UserRole.STAFF)
    status = Column(String, nullable=False, default=UserStatus.ACTIVE)
    email_verified = Column(Boolean, nullable=False, default=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="users")
