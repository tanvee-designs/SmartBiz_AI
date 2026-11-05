import json
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


LeadStatus = Literal["new", "contacted", "qualified", "converted", "lost"]
LeadSource = Literal[
    "website",
    "facebook",
    "google_forms",
    "linkedin",
    "referral",
    "email",
    "other",
]


# ---------------- LEAD SCHEMAS ----------------

class LeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    company: Optional[str] = Field(default=None, max_length=150)
    message: Optional[str] = None
    source: LeadSource = "website"
    interest: Optional[str] = Field(default=None, max_length=200)
    value: float = Field(default=0, ge=0)


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
    interest: Optional[str] = None
    value: Optional[float] = 0
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
    title: str = Field(min_length=2, max_length=200)
    summary: str = Field(min_length=1)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    report_type: Optional[str] = Field(default="ai_report", max_length=50)


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: Optional[str] = None
    title: str
    summary: str
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime

    @field_validator("insights", "recommendations", mode="before")
    @classmethod
    def parse_json_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except ValueError:
                return [value] if value.strip() else []
            return parsed if isinstance(parsed, list) else [str(parsed)]
        return value


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


# ---------------- FOLLOW-UP SCHEMAS ----------------

class FollowUpCreate(BaseModel):
    lead_id: int
    channel: str = Field(default="email", max_length=20)
    note: Optional[str] = None
    status: Literal["sent", "failed"] = "sent"


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    channel: str
    note: Optional[str] = None
    status: str
    created_at: datetime


class DueFollowUpResponse(LeadResponse):
    last_contact_at: datetime
    days_since_contact: int