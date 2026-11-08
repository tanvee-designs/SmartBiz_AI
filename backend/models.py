from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float

from database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    company = Column(String(150), nullable=True)
    message = Column(Text, nullable=True)
    source = Column(String(50), default="website")
    interest = Column(String(200), nullable=True)
    value = Column(Float, default=0)
    status = Column(String(30), default="new")
    last_contacted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    company = Column(String(150), nullable=True)
    total_deals = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), default="ai_report")
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    insights = Column(Text, default="[]")
    recommendations = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String(255), nullable=False)
    is_read = Column(String(10), default="false")
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    to_email = Column(String(150), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    generated_by = Column(String(50), default="ai")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)
    channel = Column(String(30), default="email")
    note = Column(Text, nullable=True)
    status = Column(String(20), default="sent")
    created_at = Column(DateTime, default=datetime.utcnow)