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
