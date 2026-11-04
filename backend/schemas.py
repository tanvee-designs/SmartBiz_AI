from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

LeadStatus = Literal["new", "contacted", "qualified", "converted", "lost"]


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