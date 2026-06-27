"""Pydantic request/response schemas."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Auth ---
class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# --- License / Company ---
class LicenseInfo(BaseModel):
    status: str
    plan_name: Optional[str] = None
    expires_at: Optional[datetime] = None
    monthly_document_limit: Optional[int] = None
    max_users: Optional[int] = None


class CompanyInfo(BaseModel):
    id: uuid.UUID
    name: str
    status: str


class ActivateRequest(BaseModel):
    license_key: str = Field(min_length=4, max_length=100)


# --- User ---
class UserInfo(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    status: str
    company: Optional[CompanyInfo] = None
    license: Optional[LicenseInfo] = None


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo


# --- Team ---
class CreateMemberRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str  # MANAGER | STAFF


class UpdateMemberRequest(BaseModel):
    role: Optional[str] = None
    status: Optional[str] = None


class MemberInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: str
    status: str
    last_login_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    message: str


# --- Files ---
class FileInfo(BaseModel):
    id: uuid.UUID
    original_name: str
    size_bytes: Optional[int] = None
    mime_type: Optional[str] = None


# --- Verifications ---
class VerificationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    reference_file_ids: list[uuid.UUID] = Field(min_length=1)
    target_file_ids: list[uuid.UUID] = Field(min_length=1)


class DocumentInfo(BaseModel):
    id: uuid.UUID
    role: str
    original_name: Optional[str] = None
    doc_type: Optional[str] = None
    doc_type_label: Optional[str] = None
    doc_type_confidence: Optional[float] = None
    page_count: Optional[int] = None
    fields: Optional[dict] = None
    text: Optional[str] = None


class FindingInfo(BaseModel):
    id: uuid.UUID
    field_key: str
    field_label: Optional[str] = None
    reference_value: Optional[str] = None
    detected_value: Optional[str] = None
    match_type: str
    severity: str
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    suggested_fix: Optional[str] = None
    status: str


class VerificationSummary(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    stage: Optional[str] = None
    overall_result: Optional[str] = None
    critical_count: int
    major_count: int
    minor_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    created_by_name: Optional[str] = None
    doc_types: list[str] = []


class VerificationDetail(VerificationSummary):
    documents: list[DocumentInfo] = []
    findings: list[FindingInfo] = []
    error_message: Optional[str] = None


class FindingUpdate(BaseModel):
    status: Optional[str] = None  # ACCEPTED | DISMISSED | CORRECTED
    corrected_value: Optional[str] = None


class ReportInfo(BaseModel):
    id: uuid.UUID
    fmt: str
    created_at: datetime


# --- Admin ---
class AdminCompany(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    plan_name: Optional[str] = None
    license_status: Optional[str] = None
    expires_at: Optional[datetime] = None
    user_count: int = 0
    documents_used: int = 0


class AdminLicenseCreate(BaseModel):
    plan_id: uuid.UUID
    license_key: Optional[str] = None  # auto-generated when omitted


class AdminLicenseInfo(BaseModel):
    id: uuid.UUID
    license_key: str
    plan_name: Optional[str] = None
    status: str
    company_name: Optional[str] = None
    expires_at: Optional[datetime] = None


class AdminPlanInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    monthly_document_limit: int
    max_users: int
    price_cents: int
    is_active: bool


class AdminStats(BaseModel):
    companies: int
    active_companies: int
    users: int
    verifications: int
    documents_processed: int
    mrr_cents: int
