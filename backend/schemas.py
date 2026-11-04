
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


LeadStatus = Literal["new", "contacted", "qualified", "converted", "lost"]


# ---------------- LEAD SCHEMAS ----------------

class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    company: Optional[str] = Field(default=None, max_length=150)
    message: Optional[str] = None
    source: Optional[str] = Field(default="website", max_length=50)


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    source: Optional[str] = None
    status: str
    created_at: datetime


# ---------------- CUSTOMER SCHEMAS ----------------

class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    company: Optional[str] = Field(default=None, max_length=150)
    total_deals: int = Field(default=0, ge=0)


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    total_deals: int
    created_at: datetime


# ---------------- REPORT SCHEMAS ----------------

class ReportCreate(BaseModel):
    report_type: str = Field(min_length=2, max_length=50)
    content: str = Field(min_length=1)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: str
    content: str
    created_at: datetime


# ---------------- NOTIFICATION SCHEMAS ----------------

class NotificationCreate(BaseModel):
    message: str = Field(min_length=1, max_length=255)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    is_read: str
    created_at: datetime


# ---------------- EMAIL LOG SCHEMAS ----------------

class EmailLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    to_email: str
    subject: str
    body: str
    generated_by: str
    status: str
    created_at: datetime
