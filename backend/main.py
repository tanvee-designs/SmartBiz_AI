import json
import os
import httpx
import requests
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

# Optional imports
try:
    from generate_email import generate_welcome_email
except Exception:
    generate_welcome_email = None

try:
    from generate_report import generate_business_report
except Exception:
    generate_business_report = None

try:
    from n8n_client import send_lead_to_n8n
except Exception:
    send_lead_to_n8n = None


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


# ---------------- ENV VARIABLES ----------------
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "https://smartbiz-ai-jannatun.app.n8n.cloud")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_NOTIFICATION_WEBHOOK_URL = os.getenv("N8N_NOTIFICATION_WEBHOOK_URL", "")
N8N_WEBHOOK_HEALTH_URL = os.getenv("N8N_WEBHOOK_HEALTH_URL", "https://smartbiz-ai-jannatun.app.n8n.cloud/webhook/smartbiz-new-lead")


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def send_notification_to_n8n(payload: dict):
    """
    n8n Notification Workflow-এ POST request পাঠায়।
    Background Task হিসেবে চলবে, তাই API response ব্লক করবে না।
    """
    if not N8N_NOTIFICATION_WEBHOOK_URL:
        print("⚠️ N8N_NOTIFICATION_WEBHOOK_URL is not set. Skipping.")
        return

    try:
        response = requests.post(
            N8N_NOTIFICATION_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )
        response.raise_for_status()
        print(f"✅ Notification sent to n8n for lead_id: {payload.get('lead_id')}")
    except Exception as e:
        print(f"❌ Failed to send notification to n8n: {e}")


# ==================================================
# HOME AND HEALTH
# ==================================================

@app.get("/")
def home():
    return {"message": "SmartBiz_AI Backend is running", "status": "success"}


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is healthy"}


# ==================================================
# LEAD APIs (Upsert Logic + Auto Notification)
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

    # Upsert: ডুপ্লিকেট হলে আপডেট হবে
    if existing:
        existing.name = lead.name.strip() if lead.name else existing.name
        existing.phone = lead.phone if lead.phone else existing.phone
        existing.company = lead.company if lead.company else existing.company
        existing.interest = lead.interest if lead.interest else existing.interest
        existing.value = lead.value if lead.value else existing.value
        existing.message = lead.message if lead.message else existing.message
        existing.source = lead.source if lead.source else existing.source

        db.commit()
        db.refresh(existing)
        return existing

    new_lead = models.Lead(
        name=lead.name.strip(),
        email=email,
        phone=lead.phone,
        company=lead.company,
        message=lead.message,
        source=lead.source,
        interest=lead.interest,
        value=lead.value,
        status="new",
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    # ১. Backend Notification তৈরি (Dashboard-এর জন্য)
    notification = models.Notification(
        message=f"New lead from {new_lead.source}: {new_lead.name} ({new_lead.email})",
        is_read="false",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # ২. n8n Notification Workflow Trigger (Non-blocking Background Task)
    if N8N_NOTIFICATION_WEBHOOK_URL:
        background_tasks.add_task(
            send_notification_to_n8n,
            {
                "notification_id": notification.id,
                "lead_id": new_lead.id,
                "name": new_lead.name,
                "email": new_lead.email,
                "company": new_lead.company,
                "source": new_lead.source,
                "message": notification.message,
            },
        )

    # ৩. Optional n8n Lead Automation Push (যদি কনফিগার করা থাকে)
    if send_lead_to_n8n:
        try:
            background_tasks.add_task(send_lead_to_n8n, new_lead)
        except Exception:
            pass

    return new_lead


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


# ==================================================
# CUSTOMER APIs
# ==================================================

@app.post("/api/customers", response_model=schemas.CustomerResponse, status_code=201)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    email = str(customer.email).lower()
    existing = db.query(models.Customer).filter(func.lower(models.Customer.email) == email).first()
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


# ==================================================
# REPORT APIs
# ==================================================

@app.post("/api/reports", response_model=schemas.ReportResponse, status_code=201)
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


@app.post("/api/reports/generate", response_model=schemas.ReportResponse, status_code=201)
def generate_ai_report(db: Session = Depends(get_db)):
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
        content=json.dumps(result, ensure_ascii=False, default=str),
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


# ==================================================
# NOTIFICATION APIs
# ==================================================

@app.post("/api/notifications", response_model=schemas.NotificationResponse, status_code=201)
def create_notification(notification: schemas.NotificationCreate, db: Session = Depends(get_db)):
    new_notification = models.Notification(
        message=notification.message.strip(),
        is_read="false",
    )
    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)

    # n8n Notification Webhook Trigger
    if N8N_NOTIFICATION_WEBHOOK_URL:
        try:
            requests.post(
                N8N_NOTIFICATION_WEBHOOK_URL,
                json={"id": new_notification.id, "message": new_notification.message},
                timeout=5,
            )
        except Exception as e:
            print(f"Could not send notification to n8n: {e}")

    return new_notification


@app.get("/api/notifications", response_model=List[schemas.NotificationResponse])
def list_notifications(db: Session = Depends(get_db)):
    return db.query(models.Notification).order_by(models.Notification.created_at.desc()).all()


# ==================================================
# EMAIL LOG APIs
# ==================================================

@app.get("/email-logs", response_model=List[schemas.EmailLogResponse])
def list_email_logs(db: Session = Depends(get_db)):
    return db.query(models.EmailLog).order_by(models.EmailLog.created_at.desc()).all()


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


# ==================================================
# WELCOME EMAIL AUTOMATION
# ==================================================

@app.post("/automation/welcome-email/{lead_id}")
def create_welcome_email(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    if generate_welcome_email is None:
        raise HTTPException(500, "generate_email module not found")

    try:
        result = generate_welcome_email({"name": lead.name, "email": lead.email, "company": lead.company, "phone": lead.phone})
    except Exception as e:
        raise HTTPException(500, f"Email generation failed: {e}")

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


# ==================================================
# CUSTOMER FOLLOW-UP APIs
# ==================================================

FOLLOW_UP_INTERVAL_DAYS = 3


def get_last_contact(db: Session, lead: models.Lead) -> datetime:
    times = [lead.created_at]
    last_email = db.query(func.max(models.EmailLog.created_at)).filter(models.EmailLog.lead_id == lead.id, models.EmailLog.status == "sent").scalar()
    if last_email: times.append(last_email)
    last_follow_up = db.query(func.max(models.FollowUp.created_at)).filter(models.FollowUp.lead_id == lead.id).scalar()
    if last_follow_up: times.append(last_follow_up)
    if lead.last_contacted_at: times.append(lead.last_contacted_at)
    return max(times)


@app.get("/api/follow-ups/due")
def list_due_follow_ups(days: int = Query(default=FOLLOW_UP_INTERVAL_DAYS, ge=0, le=90), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)
    leads = db.query(models.Lead).filter(models.Lead.status.in_(["new", "contacted"])).all()

    due = []
    for lead in leads:
        last_contact = get_last_contact(db, lead) or lead.created_at
        if last_contact <= cutoff:
            due.append({
                "lead_id": lead.id, "name": lead.name, "email": lead.email, "company": lead.company, "status": lead.status,
                "created_at": lead.created_at.isoformat(),
                "last_contacted_at": lead.last_contacted_at.isoformat() if lead.last_contacted_at else None,
                "last_contact_at": last_contact.isoformat(),
                "days_since_contact": (now - last_contact).days,
            })
    due.sort(key=lambda entry: entry["last_contact_at"])
    return {"count": len(due), "days": days, "leads": due}


@app.post("/api/follow-ups", response_model=schemas.FollowUpResponse, status_code=201)
def create_follow_up(payload: schemas.FollowUpCreate, db: Session = Depends(get_db)):
    lead = db.query(models.Lead).filter(models.Lead.id == payload.lead_id).first()
    if not lead:
        raise HTTPException(404, "Lead not found")

    if payload.status == "sent":
        window_start = datetime.utcnow() - timedelta(days=FOLLOW_UP_INTERVAL_DAYS)
        recent = db.query(models.FollowUp).filter(
            models.FollowUp.lead_id == lead.id, models.FollowUp.status == "sent", models.FollowUp.created_at >= window_start
        ).first()
        if recent:
            raise HTTPException(409, "A follow-up was already sent recently")

    follow_up = models.FollowUp(lead_id=payload.lead_id, channel=payload.channel, status=payload.status, message=payload.message or payload.note)
    db.add(follow_up)

    if payload.status == "sent":
        lead.last_contacted_at = datetime.utcnow()
        if lead.status == "new":
            lead.status = "contacted"

    db.add(models.Notification(message=f"Follow-up ({payload.channel}) sent to {lead.name} ({lead.email})"))
    db.commit()
    db.refresh(follow_up)
    return follow_up


@app.get("/api/follow-ups", response_model=List[schemas.FollowUpResponse])
def list_follow_ups(lead_id: Optional[int] = None, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(models.FollowUp)
    if lead_id is not None:
        q = q.filter(models.FollowUp.lead_id == lead_id)
    return q.order_by(models.FollowUp.created_at.desc()).limit(limit).all()


# ==================================================
# N8N HEALTH CHECK API (Webhook-based)
# ==================================================

@app.get("/api/integrations/n8n/health")
async def n8n_health_check():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(N8N_WEBHOOK_HEALTH_URL, headers={"ngrok-skip-browser-warning": "true"}, timeout=5.0)
            is_reachable = response.status_code < 500
    except Exception:
        is_reachable = False

    if is_reachable:
        return {"status": "connected", "message": "n8n Cloud is reachable."}
    else:
        return {"status": "unreachable", "message": "n8n Cloud is not responding."}


# ==================================================
# EXECUTION LOG APIs (n8n Webhook Callback)
# ==================================================

@app.post("/api/executions/log", response_model=schemas.ExecutionLogResponse, status_code=201)
def log_execution(payload: schemas.ExecutionLogCreate, db: Session = Depends(get_db)):
    existing = db.query(models.ExecutionLog).filter(models.ExecutionLog.execution_id == payload.execution_id).first()
    if existing:
        return existing

    new_log = models.ExecutionLog(**payload.model_dump())
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


@app.get("/api/workflows/executions")
def get_workflow_executions(db: Session = Depends(get_db)):
    logs = db.query(models.ExecutionLog).order_by(models.ExecutionLog.created_at.desc()).limit(10).all()
    return [
        {
            "id": log.execution_id,
            "workflow_name": log.workflow_name,
            "status": log.status,
            "started_at": log.started_at.isoformat() if log.started_at else None,
            "time_saved": "N/A"
        }
        for log in logs
    ]


@app.get("/api/workflows")
def get_workflows():
    return [
        {"id": 1, "name": "SmartBiz AI - Lead Automation", "active": True, "nodes": ["Webhook", "HTTP Request", "Gmail", "IF"], "connections": "Live n8n Data"},
        {"id": 2, "name": "SmartBiz AI - Customer Follow-up", "active": True, "nodes": ["Schedule", "HTTP Request", "Split Out", "Gmail"], "connections": "Live n8n Data"},
        {"id": 3, "name": "SmartBiz AI - Notification Workflow", "active": True, "nodes": ["Webhook", "HTTP Request"], "connections": "Live n8n Data"}
    ]