
import json
import re

from datetime import datetime, timezone, timedelta
from typing import List, Literal, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    field_serializer,
)


LeadStatus = Literal["new", "contacted", "qualified", "converted", "lost"]

LeadSource = Literal[
    "website",
    "facebook",
    "google_forms",
    "manual",
    "linkedin",
    "referral",
    "email",
    "other",
]

BST = timezone(timedelta(hours=6))


# ---------------- PHONE NORMALIZATION ----------------

def normalize_bd_phone(value):
    if value is None:
        return None

    phone = re.sub(r"[\s()-]", "", str(value))

    if not phone:
        return None

    if re.fullmatch(r"01[3-9]\d{8}", phone):
        return "+88" + phone

    if re.fullmatch(r"\+8801[3-9]\d{8}", phone):
        return phone

    raise ValueError(
        "Enter a valid Bangladesh mobile number: "
        "01XXXXXXXXX or +8801XXXXXXXXX."
    )


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

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value):
        return normalize_bd_phone(value)


class LeadStatusUpdate(BaseModel):
    status: LeadStatus


class LeadUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    company: Optional[str] = Field(default=None, max_length=150)
    message: Optional[str] = None
    source: Optional[LeadSource] = None
    interest: Optional[str] = Field(default=None, max_length=200)
    value: Optional[float] = Field(default=None, ge=0)
    status: Optional[LeadStatus] = None

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value):
        return normalize_bd_phone(value)


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
    last_contacted_at: Optional[datetime] = None
    created_at: datetime

    @field_serializer("created_at", "last_contacted_at")
    def serialize_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(BST).isoformat()


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

    @field_serializer("created_at")
    def serialize_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(BST).isoformat()


# ---------------- REPORT SCHEMAS ----------------

class ReportCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    summary: str = Field(min_length=1)
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    report_type: Optional[str] = Field(default="ai_report", max_length=50)
    content: Optional[str] = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_type: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    insights: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    content: Optional[str] = None
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

    @field_serializer("created_at")
    def serialize_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(BST).isoformat()


# ---------------- NOTIFICATION SCHEMAS ----------------

class NotificationCreate(BaseModel):
    message: str = Field(min_length=1, max_length=255)


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message: str
    is_read: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(BST).isoformat()


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

    @field_serializer("created_at")
    def serialize_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(BST).isoformat()


# ---------------- FOLLOW-UP SCHEMAS ----------------

class FollowUpCreate(BaseModel):
    lead_id: int
    channel: str = Field(default="email", max_length=30)
    note: Optional[str] = None
    message: Optional[str] = None
    status: Literal["sent", "failed"] = "sent"


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lead_id: int
    channel: str
    note: Optional[str] = None
    message: Optional[str] = None
    status: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(BST).isoformat()


class DueFollowUpResponse(LeadResponse):
    lead_id: Optional[int] = None
    last_contact_at: datetime
    days_since_contact: int


class DueFollowUpList(BaseModel):
    count: int
    days: int
    leads: List[DueFollowUpResponse] = Field(default_factory=list)


# ---------------- EXECUTION LOG SCHEMAS ----------------

class ExecutionLogCreate(BaseModel):
    execution_id: str = Field(min_length=1, max_length=100)
    workflow_name: str = Field(min_length=1, max_length=150)
    workflow_id: Optional[str] = Field(default=None, max_length=100)
    status: Literal["success", "error"]
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


class ExecutionLogResponse(ExecutionLogCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "started_at", "finished_at")
    def serialize_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(BST).isoformat()


# ---------------- N8N WEBHOOK SCHEMAS ----------------

N8nEvent = Literal[
    "ping",
    "email_sent",
    "email_failed",
    "lead_status_changed",
]


class N8nWebhookPayload(BaseModel):
    event: N8nEvent
    lead_id: Optional[int] = None
    email_log_id: Optional[int] = None
    status: Optional[LeadStatus] = None
    message: Optional[str] = Field(default=None, max_length=255)
