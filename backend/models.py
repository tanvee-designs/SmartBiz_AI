from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from database import Base


# ============================================================
# LEAD
# ============================================================
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
    value = Column(Integer, default=0)
    status = Column(String(30), default="new")
    last_contacted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# CUSTOMER
# ============================================================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), nullable=False, index=True)
    phone = Column(String(30), nullable=True)
    company = Column(String(150), nullable=True)
    total_deals = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# FOLLOW-UP
# ============================================================
class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)
    channel = Column(String(30), default="email", index=True)   # email / sms / call
    status = Column(String(30), default="sent")                 # sent / failed / opened
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ============================================================
# REPORT
# ============================================================
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False, default="ai_report")
    title = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)
    insights = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# NOTIFICATION
# ============================================================
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String(255), nullable=False)
    is_read = Column(String(10), default="false")
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# EMAIL LOG
# ============================================================
class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, nullable=False, index=True)
    to_email = Column(String(150), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    generated_by = Column(String(50), default="template")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)