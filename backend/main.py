import sys
import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Literal

# ai_module / generate_report / n8n_client import-এর জন্য path fix
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import Base, engine, get_db
import models
import schemas


# ============================================================
# Optional imports — না থাকলে server চলবে, endpoint 500 দেবে
# ============================================================
try:
    from generate_report import generate_business_report
except Exception:
    generate_business_report = None

try:
    from n8n_client import send_lead_to_n8n
except Exception:
    send_lead_to_n8n = None


# ============================================================
# App init
# ============================================================
app = FastAPI(title="SmartBiz_AI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# ============================================================
# Health / Root
# ============================================================
@app.get("/")
def home():
    return {"message": "SmartBiz_AI Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ============================================================
# LEAD
# ============================================================
@app.post("/api/leads", response_model=schemas.LeadResponse, status_code=201)
def create_lead(lead: schemas.LeadCreate, db: Session = Depends(get_db)):
    new_lead = models.Lead(**lead.model_dump())
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    # Optional: n8n-এ পাঠাও
    if send_lead_to_n8n:
        try:
            send_lead_to_n8n(new_lead)
        except Exception:
            pass

    return new_lead


@app.get("/api/leads/export")
def export_leads(db: Session = Depends(get_db)):
    leads = db.query(models.Lead).order_by(models.Lead.created_at.desc()).all()
    return [
        {
            "id": l.id,
            "name": l.name,
            "email": l.email,
            "phone": l.phone or "",
            "company": l.company or "",
            "source": l.source,
            "status": l.status,
            "last_contacted_at": l.last_contacted_at.isoformat() if l.last_contacted_at else "",
            "created_at": l.created_at.isoformat(),
        }
        for l in leads
    ]


@app.get("/api/leads", response_model=List[schemas.LeadResponse])
def list_leads(db: Session = Depends(get_db)):
    return db.query(models.Lead).order_by(models.Lead.created_at.desc()).all()


@app.get("/api/leads/{lead_id}", response_model=schemas.LeadResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@app.patch("/api/leads/{lead_id}/status", response_model=schemas.LeadResponse)
def update_lead_status(
    lead_id: int,
    payload: schemas.LeadStatusUpdate,
    db: Session = Depends(get_db),
):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")
    lead.status = payload.status
    db.commit()
    db.refresh(lead)
    return lead


# ============================================================
# CUSTOMER
# ============================================================
@app.post("/api/customers", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    email = str(customer.email).lower()
    existing = (
        db.query(models.Customer)
        .filter(func.lower(models.Customer.email) == email)
        .first()
    )
    if existing:
        raise HTTPException(409, "Customer with this email already exists")

    new_customer = models.Customer(
        name=customer.name.strip(),
        email=email,
        phone=customer.phone,
        company=customer.company,
        total_deals=customer.total_deals,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


@app.get("/api/customers", response_model=List[schemas.CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).order_by(models.Customer.created_at.desc()).all()


# ============================================================
# REPORT
# ============================================================
@app.post("/api/reports", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(report: schemas.ReportCreate, db: Session = Depends(get_db)):
    new_report = models.Report(
        report_type=(report.report_type or "ai_report").strip(),
        title=report.title.strip(),
        summary=report.summary,
        insights=json.dumps(report.insights, ensure_ascii=False),
        recommendations=json.dumps(report.recommendations, ensure_ascii=False),
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


@app.get("/api/reports", response_model=List[schemas.ReportResponse])
def list_reports(db: Session = Depends(get_db)):
    return db.query(models.Report).order_by(models.Report.created_at.desc()).all()


@app.post("/api/reports/generate", response_model=schemas.ReportResponse, status_code=status.HTTP_201_CREATED)
def generate_ai_report(db: Session = Depends(get_db)):
    """AI দিয়ে Business Report বানিয়ে reports টেবিলে save করে।"""
    if generate_business_report is None:
        raise HTTPException(500, "generate_report module not found")

    leads = db.query(models.Lead).all()
    logs = db.query(models.EmailLog).all()

    try:
        result = generate_business_report(leads, logs)
    except Exception as e:
        raise HTTPException(500, f"Report generation failed: {e}")

    new_report = models.Report(
        report_type="ai_report",
        title=result.get("title"),
        summary=result.get("summary"),
        insights=json.dumps(result.get("insights", []), ensure_ascii=False),
        recommendations=json.dumps(result.get("recommendations", []), ensure_ascii=False),
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


# ============================================================
# NOTIFICATION
# ============================================================
@app.post("/api/notifications", response_model=schemas.NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    new_notification = models.Notification(
        message=notification.message.strip(),
        is_read="false",
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)
    return new_notification


@app.get("/api/notifications", response_model=List[schemas.NotificationResponse])
def list_notifications(db: Session = Depends(get_db)):
    return db.query(models.Notification).order_by(models.Notification.created_at.desc()).all()


@app.patch("/api/notifications/{notification_id}/read", response_model=schemas.NotificationResponse)
def mark_notification_as_read(notification_id: int, db: Session = Depends(get_db)):
    notification = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id)
        .first()
    )
    if not notification:
        raise HTTPException(404, "Notification not found")
    notification.is_read = "true"
    db.commit()
    db.refresh(notification)
    return notification


# ============================================================
# EMAIL LOG
# ============================================================
@app.patch("/email-logs/{log_id}/status", response_model=schemas.EmailLogResponse)
def update_email_status(
    log_id: int,
    new_status: Literal["pending", "sent", "failed"] = Query(alias="status"),
    db: Session = Depends(get_db),
):
    log = db.query(models.EmailLog).filter(models.EmailLog.id == log_id).first()
    if not log:
        raise HTTPException(404, "Log not found")
    log.status = new_status
    db.commit()
    db.refresh(log)
    return log


@app.get("/email-logs", response_model=List[schemas.EmailLogResponse])
def list_email_logs(db: Session = Depends(get_db)):
    return db.query(models.EmailLog).order_by(models.EmailLog.created_at.desc()).all()


# ============================================================
# CUSTOMER FOLLOW-UP (Day 4 logic + Member 3-এর EmailLog)
# ============================================================
FOLLOW_UP_INTERVAL_DAYS = 3


def get_last_contact(db: Session, lead: models.Lead) -> datetime:
    """Newest sent email / follow-up / last_contacted_at / created_at।"""
    times = [lead.created_at]

    last_email = (
        db.query(func.max(models.EmailLog.created_at))
        .filter(
            models.EmailLog.lead_id == lead.id,
            models.EmailLog.status == "sent",
        )
        .scalar()
    )
    if last_email:
        times.append(last_email)

    last_follow_up = (
        db.query(func.max(models.FollowUp.created_at))
        .filter(models.FollowUp.lead_id == lead.id)
        .scalar()
    )
    if last_follow_up:
        times.append(last_follow_up)

    if lead.last_contacted_at:
        times.append(lead.last_contacted_at)

    return max(times)


@app.get("/api/follow-ups/due")
def list_due_follow_ups(
    days: int = FOLLOW_UP_INTERVAL_DAYS,
    db: Session = Depends(get_db),
):
    """যে lead-গুলো follow-up-এর জন্য due (n8n poll করে)।"""
    cutoff = datetime.utcnow() - timedelta(days=days)

    candidates = (
        db.query(models.Lead)
        .filter(models.Lead.status.in_(["new", "contacted"]))
        .all()
    )

    due = []
    for lead in candidates:
        last_contact = get_last_contact(db, lead)
        if last_contact <= cutoff:
            due.append({
                "lead_id": lead.id,
                "name": lead.name,
                "email": lead.email,
                "company": lead.company,
                "status": lead.status,
                "created_at": lead.created_at.isoformat(),
                "last_contacted_at": (
                    lead.last_contacted_at.isoformat()
                    if lead.last_contacted_at else None
                ),
                "last_follow_up": last_contact.isoformat(),
                "days_since_contact": (datetime.utcnow() - last_contact).days,
            })

    return {"count": len(due), "days": days, "leads": due}


@app.post("/api/follow-ups", response_model=schemas.FollowUpResponse, status_code=201)
def create_follow_up(payload: schemas.FollowUpCreate, db: Session = Depends(get_db)):
    """Follow-up log + duplicate prevention + lead auto-update।"""
    lead = db.query(models.Lead).filter(models.Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    # Duplicate prevention: ২৪ ঘণ্টার ভিতরে একই lead + channel
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    duplicate = (
        db.query(models.FollowUp)
        .filter(
            models.FollowUp.lead_id == payload.lead_id,
            models.FollowUp.channel == payload.channel,
            models.FollowUp.status == "sent",
            models.FollowUp.created_at >= recent_cutoff,
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            409,
            f"Duplicate follow-up: {payload.channel} already sent to lead {payload.lead_id} within 24 hours",
        )

    follow_up = models.FollowUp(**payload.model_dump())
    db.add(follow_up)

    if payload.status == "sent":
        lead.last_contacted_at = datetime.utcnow()
        if lead.status == "new":
            lead.status = "contacted"

    db.add(models.Notification(
        message=f"Follow-up ({payload.channel}) sent to {lead.name} ({lead.email})"
    ))

    db.commit()
    db.refresh(follow_up)
    return follow_up


@app.get("/api/follow-ups", response_model=List[schemas.FollowUpResponse])
def list_follow_ups(
    lead_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    q = db.query(models.FollowUp)
    if lead_id is not None:
        q = q.filter(models.FollowUp.lead_id == lead_id)
    return q.order_by(models.FollowUp.created_at.desc()).limit(limit).all()


# ============================================================
# WELCOME EMAIL AUTOMATION (Member 3-এর feature)
# ============================================================
@app.post("/automation/welcome-email/{lead_id}")
def create_welcome_email(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    try:
        from generate_email import generate_welcome_email
    except Exception as e:
        raise HTTPException(500, f"email_generator module not found: {e}")

    result = generate_welcome_email({
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "phone": lead.phone,
    })

    log = models.EmailLog(
        lead_id=lead.id,
        to_email=lead.email,
        subject=result["subject"],
        body=result["body"],
        generated_by=result.get("source", "template"),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {"log_id": log.id, "to": lead.email, **result}