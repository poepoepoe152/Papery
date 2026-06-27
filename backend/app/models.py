"""SQLAlchemy ORM models.

Implements the tenancy, auth, files, verification, comparison, reporting,
learning, and audit contexts from the architecture document.
"""
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .database import Base


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


# --- Enumerated string constants ---
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


class DocumentRole:
    REFERENCE = "REFERENCE"
    TARGET = "TARGET"


class VerificationStatus:
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class OverallResult:
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class Severity:
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class MatchType:
    EXACT = "EXACT"
    NORMALIZED = "NORMALIZED"
    FUZZY = "FUZZY"
    SEMANTIC = "SEMANTIC"
    MISMATCH = "MISMATCH"
    MISSING = "MISSING"
    EXTRA = "EXTRA"


class FindingStatus:
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    DISMISSED = "DISMISSED"
    CORRECTED = "CORRECTED"


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# ===== Tenancy =====
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


class UsageCounter(Base, TimestampMixin):
    __tablename__ = "usage_counters"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    period_start = Column(Date, nullable=False)
    documents_used = Column(Integer, nullable=False, default=0)


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


# ===== Files & Verification =====
class FileObject(Base, TimestampMixin):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    storage_path = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(BigInteger, nullable=True)
    page_count = Column(Integer, nullable=True)
    checksum = Column(String, nullable=True)


class Verification(Base, TimestampMixin):
    __tablename__ = "verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default=VerificationStatus.QUEUED)
    stage = Column(String, nullable=True)
    overall_result = Column(String, nullable=True)
    critical_count = Column(Integer, nullable=False, default=0)
    major_count = Column(Integer, nullable=False, default=0)
    minor_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    creator = relationship("User")
    documents = relationship(
        "Document", back_populates="verification", cascade="all, delete-orphan"
    )
    findings = relationship(
        "Finding", back_populates="verification", cascade="all, delete-orphan"
    )


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    verification_id = Column(
        UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False
    )
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    role = Column(String, nullable=False)  # REFERENCE | TARGET
    doc_type = Column(String, nullable=True)
    doc_type_confidence = Column(Numeric, nullable=True)
    language = Column(String, nullable=True)
    page_count = Column(Integer, nullable=True)
    text = Column(Text, nullable=True)
    fields = Column(JSONB, nullable=True)  # {field_key: {raw, normalized, confidence}}
    original_name = Column(String, nullable=True)

    verification = relationship("Verification", back_populates="documents")
    file = relationship("FileObject")


class Finding(Base, TimestampMixin):
    __tablename__ = "findings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    verification_id = Column(
        UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False
    )
    field_key = Column(String, nullable=False)
    field_label = Column(String, nullable=True)
    reference_value = Column(Text, nullable=True)
    detected_value = Column(Text, nullable=True)
    match_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(Numeric, nullable=True)
    used_llm = Column(Boolean, nullable=False, default=False)
    explanation = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=FindingStatus.OPEN)

    verification = relationship("Verification", back_populates="findings")


class Report(Base, TimestampMixin):
    __tablename__ = "reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    verification_id = Column(
        UUID(as_uuid=True), ForeignKey("verifications.id"), nullable=False
    )
    fmt = Column(String, nullable=False)  # PDF | XLSX | JSON
    storage_path = Column(String, nullable=False)
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


# ===== Learning & Audit =====
class Feedback(Base, TimestampMixin):
    __tablename__ = "feedback"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=True)
    field_key = Column(String, nullable=True)
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=True)
    correction_type = Column(String, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_status = Column(String, nullable=False, default="PENDING")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(UUID(as_uuid=True), nullable=True)
    meta = Column(JSONB, nullable=True)
    ip_address = Column(String, nullable=True)
