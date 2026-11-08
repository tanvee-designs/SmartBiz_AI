import json
from datetime import datetime, timedelta
from typing import List, Literal, Optional

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas

from database import Base, engine, get_db
from generate_email import generate_welcome_email
from n8n_client import send_lead_to_n8n

# Member 3's AI report module is optional: the server still starts without it
try:
    from generate_report import generate_business_report
except Exception:
    generate_business_report = None


# ---------------- DATABASE SETUP ----------------

Base.metadata.create_all(bind=engine)


# ---------------- FASTAPI APP ----------------

app = FastAPI(
    title="SmartBiz_AI Backend",
    description="SmartBiz_AI CRM Backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# HOME AND HEALTH
# ==================================================

@app.get("/")
def home():
    return {
        "message": "SmartBiz_AI Backend is running",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Backend is healthy",
    }


# ==================================================
# LEAD APIs
# ==================================================

@app.post(
    "/api/leads",
    response_model=schemas.LeadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Lead with this email already exists"}},
)
def create_lead(
    lead: schemas.LeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    email = str(lead.email).lower()

    existing = (
        db.query(models.Lead)
        .filter(func.lower(models.Lead.email) == email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead with this email already exists",
        )

    new_lead = models.Lead(
        name=lead.name.strip(),
        email=email,
        phone=lead.phone,
        company=lead.company,
        message=lead.message,
        source=lead.source,
        interest=lead.interest,
        value=lead.value,
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    lead_data = (
        schemas.LeadResponse
        .model_validate(new_lead)
        .model_dump(mode="json")
    )
    background_tasks.add_task(send_lead_to_n8n, lead_data)

    return new_lead


@app.get("/api/leads/export")
def export_leads(db: Session = Depends(get_db)):
    leads = db.query(models.Lead).order_by(models.Lead.created_at.desc()).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "email": item.email,
            "phone": item.phone or "",
            "company": item.company or "",
            "source": item.source,
            "interest": item.interest or "",
            "value": item.value or 0,
            "status": item.status,
            "last_contacted_at": (
                item.last_contacted_at.isoformat()
                if item.last_contacted_at
                else ""
            ),
            "created_at": item.created_at.isoformat(),
        }
        for item in leads
    ]


@app.get("/api/leads", response_model=List[schemas.LeadResponse])
def list_leads(
    lead_status: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Lead)
    if lead_status:
        query = query.filter(models.Lead.status == lead_status)
    return query.order_by(models.Lead.created_at.desc()).all()


@app.get(
    "/api/leads/{lead_id}",
    response_model=schemas.LeadResponse,
    responses={404: {"description": "Lead not found"}},
)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )
    return lead


@app.patch(
    "/api/leads/{lead_id}",
    response_model=schemas.LeadResponse,
    responses={404: {"description": "Lead not found"}},
)
@app.patch(
    "/api/leads/{lead_id}/status",
    response_model=schemas.LeadResponse,
    include_in_schema=False,
)
def update_lead_status(
    lead_id: int,
    payload: schemas.LeadStatusUpdate,
    db: Session = Depends(get_db),
):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    lead.status = payload.status
    db.commit()
    db.refresh(lead)

    return lead


# ==================================================
# CUSTOMER APIs
# ==================================================

@app.post(
    "/api/customers",
    response_model=schemas.CustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
):
    email = str(customer.email).lower()

    existing = (
        db.query(models.Customer)
        .filter(func.lower(models.Customer.email) == email)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer with this email already exists",
        )

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
    return (
        db.query(models.Customer)
        .order_by(models.Customer.created_at.desc())
        .all()
    )


# ==================================================
# REPORT APIs
# ==================================================

@app.post(
    "/api/reports",
    response_model=schemas.ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    report: schemas.ReportCreate,
    db: Session = Depends(get_db),
):
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


@app.post(
    "/api/reports/generate",
    response_model=schemas.ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_ai_report(db: Session = Depends(get_db)):
    """Creates an AI business report (Member 3's module) and saves it."""
    if generate_business_report is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="generate_report module not found",
        )

    leads = db.query(models.Lead).all()
    logs = db.query(models.EmailLog).all()

    try:
        result = generate_business_report(leads, logs)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {error}",
        )

    new_report = models.Report(
        report_type="ai_report",
        title=result.get("title") or "AI Business Report",
        summary=result.get("summary") or "",
        insights=json.dumps(result.get("insights", []), ensure_ascii=False),
        recommendations=json.dumps(
            result.get("recommendations", []), ensure_ascii=False
        ),
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report


# ==================================================
# NOTIFICATION APIs
# ==================================================

@app.post(
    "/api/notifications",
    response_model=schemas.NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
):
    new_notification = models.Notification(
        message=notification.message.strip(),
        is_read="false",
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)

    return new_notification


@app.get(
    "/api/notifications",
    response_model=List[schemas.NotificationResponse],
)
def list_notifications(db: Session = Depends(get_db)):
    return (
        db.query(models.Notification)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@app.patch(
    "/api/notifications/{notification_id}/read",
    response_model=schemas.NotificationResponse,
    responses={404: {"description": "Notification not found"}},
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
):
    notification = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id)
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = "true"
    db.commit()
    db.refresh(notification)

    return notification


# ==================================================
# WELCOME EMAIL AUTOMATION
# ==================================================

@app.post(
    "/automation/welcome-email/{lead_id}",
    responses={404: {"description": "Lead not found"}},
)
def create_welcome_email(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    result = generate_welcome_email(
        {
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "phone": lead.phone,
        }
    )

    log = models.EmailLog(
        lead_id=lead.id,
        to_email=lead.email,
        subject=result["subject"],
        body=result["body"],
        generated_by=result["source"],
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {
        "log_id": log.id,
        "to": lead.email,
        **result,
    }


# ==================================================
# EMAIL LOG APIs
# ==================================================

@app.patch(
    "/email-logs/{log_id}/status",
    response_model=schemas.EmailLogResponse,
    responses={404: {"description": "Log not found"}},
)
def update_email_status(
    log_id: int,
    new_status: Literal["pending", "sent", "failed"] = Query(alias="status"),
    db: Session = Depends(get_db),
):
    log = db.query(models.EmailLog).filter(models.EmailLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )

    log.status = new_status
    db.commit()
    db.refresh(log)

    return log


@app.get("/email-logs", response_model=List[schemas.EmailLogResponse])
def list_email_logs(db: Session = Depends(get_db)):
    return (
        db.query(models.EmailLog)
        .order_by(models.EmailLog.created_at.desc())
        .all()
    )


# ==================================================
# CUSTOMER FOLLOW-UP APIs
# ==================================================

FOLLOW_UP_INTERVAL_DAYS = 3


def get_last_contact(db: Session, lead: models.Lead) -> datetime:
    """Newest sent email, sent follow-up or last_contacted_at, else created_at."""
    times = [lead.created_at]

    if lead.last_contacted_at:
        times.append(lead.last_contacted_at)

    last_email = (
        db.query(func.max(models.EmailLog.created_at))
        .filter(
            models.EmailLog.lead_id == lead.id,
            models.EmailLog.status == "sent",
        )
        .scalar()
    )
    last_follow_up = (
        db.query(func.max(models.FollowUp.created_at))
        .filter(
            models.FollowUp.lead_id == lead.id,
            models.FollowUp.status == "sent",
        )
        .scalar()
    )

    for value in (last_email, last_follow_up):
        if value:
            times.append(value)

    return max(times)


@app.get(
    "/api/follow-ups/due",
    response_model=List[schemas.DueFollowUpResponse],
)
def list_due_follow_ups(
    days: int = Query(default=FOLLOW_UP_INTERVAL_DAYS, ge=0, le=90),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    leads = (
        db.query(models.Lead)
        .filter(models.Lead.status == "contacted")
        .all()
    )

    due = []
    for lead in leads:
        last_contact = get_last_contact(db, lead)
        if now - last_contact >= timedelta(days=days):
            item = schemas.LeadResponse.model_validate(lead).model_dump()
            item["last_contact_at"] = last_contact
            item["days_since_contact"] = (now - last_contact).days
            due.append(item)

    due.sort(key=lambda entry: entry["last_contact_at"])
    return due


@app.post(
    "/api/follow-ups",
    response_model=schemas.FollowUpResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"description": "Lead not found"},
        409: {"description": "A follow-up was already sent recently"},
    },
)
def create_follow_up(
    payload: schemas.FollowUpCreate,
    db: Session = Depends(get_db),
):
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == payload.lead_id)
        .first()
    )
    if not lead:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    if payload.status == "sent":
        window_start = datetime.utcnow() - timedelta(days=FOLLOW_UP_INTERVAL_DAYS)
        recent = (
            db.query(models.FollowUp)
            .filter(
                models.FollowUp.lead_id == lead.id,
                models.FollowUp.status == "sent",
                models.FollowUp.created_at >= window_start,
            )
            .first()
        )
        if recent:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A follow-up was already sent to this lead recently",
            )

    follow_up = models.FollowUp(
        lead_id=lead.id,
        channel=payload.channel,
        note=payload.note,
        status=payload.status,
    )
    db.add(follow_up)

    if payload.status == "sent":
        lead.last_contacted_at = datetime.utcnow()
        db.add(
            models.Notification(
                message=f"Follow-up ({payload.channel}) sent to {lead.name}",
                is_read="false",
            )
        )

    db.commit()
    db.refresh(follow_up)

    return follow_up


@app.get(
    "/api/follow-ups",
    response_model=List[schemas.FollowUpResponse],
)
def list_follow_ups(
    lead_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.FollowUp)
    if lead_id is not None:
        query = query.filter(models.FollowUp.lead_id == lead_id)
    return query.order_by(models.FollowUp.created_at.desc()).all()


# ==================================================
# STATISTICS API (data for AI reports and Dashboard)
# ==================================================

@app.get("/api/stats/summary")
def stats_summary(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    leads_by_status = {
        "new": 0,
        "contacted": 0,
        "qualified": 0,
        "converted": 0,
        "lost": 0,
    }
    for lead_status, count in (
        db.query(models.Lead.status, func.count(models.Lead.id))
        .group_by(models.Lead.status)
        .all()
    ):
        leads_by_status[lead_status] = count

    leads_by_source = {
        "website": 0,
        "facebook": 0,
        "google_forms": 0,
        "linkedin": 0,
        "referral": 0,
        "email": 0,
        "other": 0,
    }
    for lead_source, count in (
        db.query(models.Lead.source, func.count(models.Lead.id))
        .group_by(models.Lead.source)
        .all()
    ):
        leads_by_source[lead_source or "other"] = count

    total_leads = db.query(func.count(models.Lead.id)).scalar() or 0

    total_value = (
        db.query(func.coalesce(func.sum(models.Lead.value), 0)).scalar() or 0
    )
    converted_value = (
        db.query(func.coalesce(func.sum(models.Lead.value), 0))
        .filter(models.Lead.status == "converted")
        .scalar()
        or 0
    )

    new_leads_last_7_days = (
        db.query(func.count(models.Lead.id))
        .filter(models.Lead.created_at >= week_ago)
        .scalar()
        or 0
    )

    total_customers = db.query(func.count(models.Customer.id)).scalar() or 0

    emails = {"total": 0, "pending": 0, "sent": 0, "failed": 0}
    for email_status, count in (
        db.query(models.EmailLog.status, func.count(models.EmailLog.id))
        .group_by(models.EmailLog.status)
        .all()
    ):
        emails[email_status] = count
        emails["total"] += count

    follow_ups = {"total": 0, "sent": 0, "failed": 0}
    for follow_up_status, count in (
        db.query(models.FollowUp.status, func.count(models.FollowUp.id))
        .group_by(models.FollowUp.status)
        .all()
    ):
        follow_ups[follow_up_status] = count
        follow_ups["total"] += count

    return {
        "total_leads": total_leads,
        "leads_by_status": leads_by_status,
        "leads_by_source": leads_by_source,
        "total_value": float(total_value),
        "converted_value": float(converted_value),
        "new_leads_last_7_days": new_leads_last_7_days,
        "total_customers": total_customers,
        "emails": emails,
        "follow_ups": follow_ups,
        "generated_at": now.isoformat(),
    }