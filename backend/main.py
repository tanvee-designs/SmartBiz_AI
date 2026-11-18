
import json
import logging
import os

import httpx
import requests

from pathlib import Path
from hmac import compare_digest
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from dotenv import load_dotenv

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from sqlalchemy import func, or_, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas

from database import Base, engine, get_db


# ---------------- LOAD ENVIRONMENT ----------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from auth import (
    authenticate_admin,
    create_access_token,
    get_current_admin,
)


logger = logging.getLogger("smartbiz")


# ---------------- OPTIONAL IMPORTS ----------------

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


def migrate_execution_log_columns():
    """
    Add new nullable columns to existing execution_logs tables.
    Existing execution records are preserved.
    """

    inspector = inspect(engine)

    if "execution_logs" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("execution_logs")
    }

    migrations = {
        "workflow_id": "ALTER TABLE execution_logs ADD COLUMN workflow_id VARCHAR(100)",
        "error_message": "ALTER TABLE execution_logs ADD COLUMN error_message TEXT",
    }

    with engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))
                logger.info(
                    "Added execution_logs.%s",
                    column_name,
                )


migrate_execution_log_columns()


# ---------------- FASTAPI APP ----------------

TAGS_METADATA = [
    {"name": "Health", "description": "Server health checks."},
    {"name": "Auth", "description": "Admin login (JWT)."},
    {
        "name": "Leads",
        "description": "Lead collection and management. POST /api/leads is public.",
    },
    {"name": "Customers", "description": "Customer management."},
    {"name": "Dashboard", "description": "Dashboard statistics."},
    {"name": "Reports", "description": "AI business reports."},
    {"name": "Notifications", "description": "System notifications."},
    {"name": "Email Logs", "description": "Generated and sent email records."},
    {"name": "Automation", "description": "AI email automation."},
    {"name": "Follow-ups", "description": "Customer follow-up logic used by n8n."},
    {"name": "n8n Integration", "description": "n8n webhooks and execution logs."},
]


app = FastAPI(
    title="SmartBiz_AI Backend",
    description=(
        "SmartBiz_AI CRM Backend API.\n\n"
        "Admin endpoints use JWT Bearer authentication. "
        "n8n endpoints use the X-API-Key header. "
        "POST /api/leads is public."
    ),
    version="1.0.0",
    openapi_tags=TAGS_METADATA,
)


# ---------------- CORS ----------------

ALLOWED_ORIGINS = [
    "https://smartbiz-automation-official.netlify.app",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


# ---------------- ERROR HANDLERS ----------------

# FastAPI's built-in RequestValidationError handler is intentionally
# preserved. It returns the standard 422 format:
# {"detail": [{"loc": ["body", "field"], "msg": "..."}]}


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request, exc):
    logger.warning("Database integrity error: %s", exc)

    return JSONResponse(
        status_code=409,
        content={
            "detail": "Database conflict: duplicate value or invalid reference."
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.exception("Unhandled server error: %s", exc)

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
    )


# ---------------- ENV VARIABLES ----------------

N8N_BASE_URL = os.getenv(
    "N8N_BASE_URL",
    "https://smartbiz-ai-jannatun.app.n8n.cloud",
)

N8N_API_KEY = os.getenv("N8N_API_KEY", "")

N8N_NOTIFICATION_WEBHOOK_URL = os.getenv(
    "N8N_NOTIFICATION_WEBHOOK_URL",
    "",
)

N8N_WEBHOOK_HEALTH_URL = os.getenv(
    "N8N_WEBHOOK_HEALTH_URL",
    "https://smartbiz-ai-jannatun.app.n8n.cloud/webhook/smartbiz-new-lead",
)


# ---------------- TIMEZONE ----------------

BST = timezone(timedelta(hours=6))


def to_bst_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(BST).isoformat()


def to_utc_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Store execution timestamps as UTC-naive values because the existing
    SQLAlchemy DateTime columns are timezone-naive.
    """

    if dt is None:
        return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BST)

    return dt.astimezone(timezone.utc).replace(tzinfo=None)


# ---------------- N8N API KEY AUTHENTICATION ----------------

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
)


def verify_n8n_api_key(
    x_api_key: Optional[str] = Depends(api_key_header),
):
    if not N8N_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="n8n API key is not configured on the backend.",
        )

    if not x_api_key or not compare_digest(x_api_key, N8N_API_KEY):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing n8n API key.",
        )

    return True


# ---------------- AUTH SCHEMAS ----------------

from pydantic import BaseModel, EmailStr


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------------- HELPER FUNCTIONS ----------------

def send_notification_to_n8n(payload: dict):
    """Send a new-lead notification to the separate n8n Notification workflow."""

    if not N8N_NOTIFICATION_WEBHOOK_URL:
        print("N8N_NOTIFICATION_WEBHOOK_URL is not set. Skipping.")
        return

    try:
        response = requests.post(
            N8N_NOTIFICATION_WEBHOOK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5,
        )

        response.raise_for_status()

        print(
            "Notification sent to n8n for lead_id: "
            f"{payload.get('lead_id')}"
        )

    except Exception as exc:
        logger.error("Failed to send notification to n8n: %s", exc)


def convert_lead_to_customer(db: Session, lead: models.Lead):
    """Create or update a Customer when a lead becomes converted."""

    email = lead.email.lower()

    customer = (
        db.query(models.Customer)
        .filter(func.lower(models.Customer.email) == email)
        .first()
    )

    if customer:
        customer.total_deals = (customer.total_deals or 0) + 1
        customer.phone = customer.phone or lead.phone
        customer.company = customer.company or lead.company
    else:
        db.add(
            models.Customer(
                name=lead.name,
                email=email,
                phone=lead.phone,
                company=lead.company,
                total_deals=1,
            )
        )

    db.add(
        models.Notification(
            message=f"Lead converted to customer: {lead.name} ({lead.email})",
            is_read="false",
        )
    )


def duplicate_email_exception():
    raise HTTPException(
        status_code=409,
        detail=[
            {
                "loc": ["body", "email"],
                "msg": "email already exists",
                "type": "value_error",
            }
        ],
    )


# ==================================================
# HOME AND HEALTH
# ==================================================

@app.get("/", tags=["Health"])
def home():
    return {
        "message": "SmartBiz_AI Backend is running",
        "status": "success",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "message": "Backend is healthy",
    }


# ==================================================
# ADMIN AUTHENTICATION
# ==================================================

@app.post("/api/auth/login", tags=["Auth"])
def admin_login(payload: AdminLoginRequest):
    is_authenticated = authenticate_admin(
        payload.email,
        payload.password,
    )

    if not is_authenticated:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    access_token = create_access_token()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,
    }


# ==================================================
# LEAD APIs
# ==================================================

@app.post(
    "/api/leads",
    response_model=schemas.LeadResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Leads"],
)
def create_lead(
    lead: schemas.LeadCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create a new public lead. Duplicate email returns HTTP 409."""

    email = str(lead.email).lower()

    existing = (
        db.query(models.Lead)
        .filter(func.lower(models.Lead.email) == email)
        .first()
    )

    if existing:
        duplicate_email_exception()

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

    notification = models.Notification(
        message=(
            f"New lead from {new_lead.source}: "
            f"{new_lead.name} ({new_lead.email})"
        ),
        is_read="false",
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

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

    if send_lead_to_n8n:
        background_tasks.add_task(
            send_lead_to_n8n,
            new_lead,
        )

    return new_lead


@app.get(
    "/api/leads",
    response_model=List[schemas.LeadResponse],
    tags=["Leads"],
)
def list_leads(
    lead_status: Optional[schemas.LeadStatus] = Query(
        default=None,
        alias="status",
    ),
    source: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    query = db.query(models.Lead)

    if lead_status:
        query = query.filter(models.Lead.status == lead_status)

    if source:
        query = query.filter(models.Lead.source == source)

    if search and search.strip():
        pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                models.Lead.name.ilike(pattern),
                models.Lead.email.ilike(pattern),
                models.Lead.company.ilike(pattern),
            )
        )

    return query.order_by(models.Lead.created_at.desc()).all()


@app.get(
    "/api/leads/{lead_id}",
    response_model=schemas.LeadResponse,
    tags=["Leads"],
)
def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(404, "Lead not found")

    return lead


@app.patch(
    "/api/leads/{lead_id}/status",
    response_model=schemas.LeadResponse,
    tags=["Leads"],
)
def update_lead_status(
    lead_id: int,
    payload: schemas.LeadStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(404, "Lead not found")

    previous_status = lead.status
    lead.status = payload.status

    if payload.status == "converted" and previous_status != "converted":
        convert_lead_to_customer(db, lead)

    db.commit()
    db.refresh(lead)

    return lead


@app.put(
    "/api/leads/{lead_id}",
    response_model=schemas.LeadResponse,
    tags=["Leads"],
)
def update_lead(
    lead_id: int,
    payload: schemas.LeadUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(404, "Lead not found")

    data = {
        key: value
        for key, value in payload.model_dump(exclude_unset=True).items()
        if value is not None
    }

    if not data:
        raise HTTPException(400, "No fields to update")

    if "email" in data:
        data["email"] = str(data["email"]).lower()

        duplicate = (
            db.query(models.Lead)
            .filter(
                func.lower(models.Lead.email) == data["email"],
                models.Lead.id != lead_id,
            )
            .first()
        )

        if duplicate:
            raise HTTPException(
                409,
                detail=[
                    {
                        "loc": ["body", "email"],
                        "msg": "email already exists",
                        "type": "value_error",
                    }
                ],
            )

    if "name" in data:
        data["name"] = data["name"].strip()

    previous_status = lead.status

    for field, value in data.items():
        setattr(lead, field, value)

    if lead.status == "converted" and previous_status != "converted":
        convert_lead_to_customer(db, lead)

    db.commit()
    db.refresh(lead)

    return lead


@app.delete(
    "/api/leads/{lead_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Leads"],
)
def delete_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(404, "Lead not found")

    db.query(models.FollowUp).filter(
        models.FollowUp.lead_id == lead_id
    ).delete()

    db.query(models.EmailLog).filter(
        models.EmailLog.lead_id == lead_id
    ).delete()

    db.delete(lead)
    db.commit()

    return None


# ==================================================
# CUSTOMER APIs
# ==================================================

@app.post(
    "/api/customers",
    response_model=schemas.CustomerResponse,
    status_code=201,
    tags=["Customers"],
)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    email = str(customer.email).lower()

    existing = (
        db.query(models.Customer)
        .filter(func.lower(models.Customer.email) == email)
        .first()
    )

    if existing:
        raise HTTPException(
            409,
            "Customer with this email already exists",
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


@app.get(
    "/api/customers",
    response_model=List[schemas.CustomerResponse],
    tags=["Customers"],
)
def list_customers(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    return (
        db.query(models.Customer)
        .order_by(models.Customer.created_at.desc())
        .all()
    )


# ==================================================
# DASHBOARD APIs
# ==================================================

LEAD_STATUSES = ["new", "contacted", "qualified", "converted", "lost"]


@app.get("/api/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    total_leads = db.query(func.count(models.Lead.id)).scalar() or 0

    leads_by_status = {name: 0 for name in LEAD_STATUSES}

    status_rows = (
        db.query(models.Lead.status, func.count(models.Lead.id))
        .group_by(models.Lead.status)
        .all()
    )

    for lead_status, count in status_rows:
        leads_by_status[lead_status or "new"] = count

    leads_by_source = {}

    source_rows = (
        db.query(models.Lead.source, func.count(models.Lead.id))
        .group_by(models.Lead.source)
        .all()
    )

    for lead_source, count in source_rows:
        leads_by_source[lead_source or "other"] = count

    total_customers = (
        db.query(func.count(models.Customer.id)).scalar() or 0
    )

    converted = leads_by_status["converted"]

    conversion_rate = (
        round(converted / total_leads * 100, 1)
        if total_leads
        else 0
    )

    pipeline_value = (
        db.query(func.coalesce(func.sum(models.Lead.value), 0))
        .filter(models.Lead.status.notin_(["converted", "lost"]))
        .scalar()
    )

    converted_value = (
        db.query(func.coalesce(func.sum(models.Lead.value), 0))
        .filter(models.Lead.status == "converted")
        .scalar()
    )

    week_ago = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).replace(tzinfo=None)

    new_leads_7d = (
        db.query(func.count(models.Lead.id))
        .filter(models.Lead.created_at >= week_ago)
        .scalar()
        or 0
    )

    follow_ups_sent = (
        db.query(func.count(models.FollowUp.id))
        .filter(models.FollowUp.status == "sent")
        .scalar()
        or 0
    )

    emails_sent = (
        db.query(func.count(models.EmailLog.id))
        .filter(models.EmailLog.status == "sent")
        .scalar()
        or 0
    )

    unread_notifications = (
        db.query(func.count(models.Notification.id))
        .filter(models.Notification.is_read == "false")
        .scalar()
        or 0
    )

    return {
        "total_leads": total_leads,
        "new_leads_last_7_days": new_leads_7d,
        "leads_by_status": leads_by_status,
        "leads_by_source": leads_by_source,
        "total_customers": total_customers,
        "conversion_rate": conversion_rate,
        "pipeline_value": float(pipeline_value or 0),
        "converted_value": float(converted_value or 0),
        "follow_ups_sent": follow_ups_sent,
        "emails_sent": emails_sent,
        "unread_notifications": unread_notifications,
    }


# ==================================================
# REPORT APIs
# ==================================================

@app.post(
    "/api/reports",
    response_model=schemas.ReportResponse,
    status_code=201,
    tags=["Reports"],
)
def create_report(
    report: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    new_report = models.Report(
        report_type=(report.report_type or "ai_report").strip(),
        title=report.title.strip(),
        summary=report.summary,
        insights=json.dumps(report.insights, ensure_ascii=False),
        recommendations=json.dumps(
            report.recommendations,
            ensure_ascii=False,
        ),
        content=report.content,
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return new_report


@app.get(
    "/api/reports",
    response_model=List[schemas.ReportResponse],
    tags=["Reports"],
)
def list_reports(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    return (
        db.query(models.Report)
        .order_by(models.Report.created_at.desc())
        .all()
    )


@app.post(
    "/api/reports/generate",
    response_model=schemas.ReportResponse,
    status_code=201,
    tags=["Reports"],
)
def generate_ai_report(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    if generate_business_report is None:
        raise HTTPException(
            500,
            "generate_report module not found",
        )

    leads = db.query(models.Lead).all()
    logs = db.query(models.EmailLog).all()

    try:
        result = generate_business_report(leads, logs)
    except Exception as exc:
        logger.exception("Report generation failed")
        raise HTTPException(
            500,
            f"Report generation failed: {exc}",
        )

    new_report = models.Report(
        report_type="ai_report",
        title=result.get("title"),
        summary=result.get("summary"),
        insights=json.dumps(
            result.get("insights", []),
            ensure_ascii=False,
        ),
        recommendations=json.dumps(
            result.get("recommendations", []),
            ensure_ascii=False,
        ),
        content=json.dumps(
            result,
            ensure_ascii=False,
            default=str,
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
    status_code=201,
    tags=["Notifications"],
)
def create_notification(
    notification: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    n8n_authenticated: bool = Depends(verify_n8n_api_key),
):
    """Create a notification from n8n. This endpoint is not for dashboard use."""

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
    tags=["Notifications"],
)
def list_notifications(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    return (
        db.query(models.Notification)
        .order_by(models.Notification.created_at.desc())
        .all()
    )


@app.patch("/api/notifications/read-all", tags=["Notifications"])
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    updated = (
        db.query(models.Notification)
        .filter(models.Notification.is_read == "false")
        .update({"is_read": "true"})
    )

    db.commit()

    return {"updated": updated}


@app.patch(
    "/api/notifications/{notification_id}/read",
    response_model=schemas.NotificationResponse,
    tags=["Notifications"],
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
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


# ==================================================
# EMAIL LOG APIs
# ==================================================

@app.get(
    "/email-logs",
    response_model=List[schemas.EmailLogResponse],
    tags=["Email Logs"],
)
def list_email_logs(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    return (
        db.query(models.EmailLog)
        .order_by(models.EmailLog.created_at.desc())
        .all()
    )


@app.patch(
    "/email-logs/{log_id}/status",
    response_model=schemas.EmailLogResponse,
    tags=["Email Logs"],
)
def update_email_status(
    log_id: int,
    new_status: Literal["pending", "sent", "failed"] = Query(
        alias="status"
    ),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    log = (
        db.query(models.EmailLog)
        .filter(models.EmailLog.id == log_id)
        .first()
    )

    if not log:
        raise HTTPException(404, "Log not found")

    log.status = new_status

    db.commit()
    db.refresh(log)

    return log


# ==================================================
# WELCOME EMAIL AUTOMATION
# ==================================================

@app.post(
    "/automation/welcome-email/{lead_id}",
    tags=["Automation"],
)
def create_welcome_email(
    lead_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(404, "Lead not found")

    if generate_welcome_email is None:
        raise HTTPException(
            500,
            "generate_email module not found",
        )

    try:
        result = generate_welcome_email(
            {
                "name": lead.name,
                "email": lead.email,
                "company": lead.company,
                "phone": lead.phone,
            }
        )
    except Exception as exc:
        raise HTTPException(
            500,
            f"Email generation failed: {exc}",
        )

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

    return {
        "log_id": log.id,
        "to": lead.email,
        **result,
    }


# ==================================================
# CUSTOMER FOLLOW-UP APIs
# ==================================================

FOLLOW_UP_INTERVAL_DAYS = 3


def get_last_contact(db: Session, lead: models.Lead) -> datetime:
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


@app.get("/api/follow-ups/due", tags=["Follow-ups"])
def list_due_follow_ups(
    days: int = Query(
        default=FOLLOW_UP_INTERVAL_DAYS,
        ge=0,
        le=90,
    ),
    db: Session = Depends(get_db),
    n8n_authenticated: bool = Depends(verify_n8n_api_key),
):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    leads = (
        db.query(models.Lead)
        .filter(models.Lead.status.in_(["new", "contacted"]))
        .all()
    )

    due = []

    for lead in leads:
        last_contact = get_last_contact(db, lead) or lead.created_at

        if last_contact.tzinfo is None:
            last_contact = last_contact.replace(tzinfo=timezone.utc)

        if last_contact <= cutoff:
            due.append(
                {
                    "lead_id": lead.id,
                    "name": lead.name,
                    "email": lead.email,
                    "company": lead.company,
                    "status": lead.status,
                    "created_at": to_bst_iso(lead.created_at),
                    "last_contacted_at": to_bst_iso(
                        lead.last_contacted_at
                    ),
                    "last_contact_at": to_bst_iso(last_contact),
                    "days_since_contact": (now - last_contact).days,
                }
            )

    due.sort(key=lambda entry: entry["last_contact_at"])

    return {
        "count": len(due),
        "days": days,
        "leads": due,
    }


@app.post(
    "/api/follow-ups",
    response_model=schemas.FollowUpResponse,
    status_code=201,
    tags=["Follow-ups"],
)
def create_follow_up(
    payload: schemas.FollowUpCreate,
    db: Session = Depends(get_db),
    n8n_authenticated: bool = Depends(verify_n8n_api_key),
):
    lead = (
        db.query(models.Lead)
        .filter(models.Lead.id == payload.lead_id)
        .first()
    )

    if not lead:
        raise HTTPException(404, "Lead not found")

    if payload.status == "sent":
        window_start = (
            datetime.now(timezone.utc) - timedelta(
                days=FOLLOW_UP_INTERVAL_DAYS
            )
        ).replace(tzinfo=None)

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
                409,
                "A follow-up was already sent recently",
            )

    follow_up = models.FollowUp(
        lead_id=payload.lead_id,
        channel=payload.channel,
        status=payload.status,
        message=payload.message or payload.note,
    )

    db.add(follow_up)

    if payload.status == "sent":
        lead.last_contacted_at = datetime.now(timezone.utc)

        if lead.status == "new":
            lead.status = "contacted"

    if payload.status == "sent":
        notification_message = (
            f"Follow-up ({payload.channel}) sent to "
            f"{lead.name} ({lead.email})"
        )
    else:
        notification_message = (
            f"Follow-up ({payload.channel}) failed for "
            f"{lead.name} ({lead.email})"
        )

    db.add(
        models.Notification(
            message=notification_message,
            is_read="false",
        )
    )

    db.commit()
    db.refresh(follow_up)

    return follow_up


@app.get(
    "/api/follow-ups",
    response_model=List[schemas.FollowUpResponse],
    tags=["Follow-ups"],
)
def list_follow_ups(
    lead_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    query = db.query(models.FollowUp)

    if lead_id is not None:
        query = query.filter(models.FollowUp.lead_id == lead_id)

    return (
        query.order_by(models.FollowUp.created_at.desc())
        .limit(limit)
        .all()
    )


# ==================================================
# N8N WEBHOOK API
# ==================================================

@app.post(
    "/api/webhooks/n8n",
    tags=["n8n Integration"],
)
def n8n_webhook(
    payload: schemas.N8nWebhookPayload,
    db: Session = Depends(get_db),
    n8n_authenticated: bool = Depends(verify_n8n_api_key),
):
    if payload.event == "ping":
        return {"status": "ok", "event": "ping"}

    if payload.event in ("email_sent", "email_failed"):
        if payload.email_log_id is None:
            raise HTTPException(400, "email_log_id is required")

        log = (
            db.query(models.EmailLog)
            .filter(models.EmailLog.id == payload.email_log_id)
            .first()
        )

        if not log:
            raise HTTPException(404, "Email log not found")

        lead = (
            db.query(models.Lead)
            .filter(models.Lead.id == log.lead_id)
            .first()
        )

        if payload.event == "email_sent":
            log.status = "sent"

            if lead:
                lead.last_contacted_at = datetime.now(timezone.utc)

                if lead.status == "new":
                    lead.status = "contacted"
        else:
            log.status = "failed"

            db.add(
                models.Notification(
                    message=(
                        payload.message
                        or f"Email failed for {log.to_email}"
                    )[:255],
                    is_read="false",
                )
            )

        db.commit()

        return {
            "status": "ok",
            "event": payload.event,
            "email_log_id": log.id,
        }

    if payload.event == "lead_status_changed":
        if payload.lead_id is None or payload.status is None:
            raise HTTPException(
                400,
                "lead_id and status are required",
            )

        lead = (
            db.query(models.Lead)
            .filter(models.Lead.id == payload.lead_id)
            .first()
        )

        if not lead:
            raise HTTPException(404, "Lead not found")

        previous_status = lead.status
        lead.status = payload.status

        if (
            payload.status == "converted"
            and previous_status != "converted"
        ):
            convert_lead_to_customer(db, lead)

        db.commit()

        return {
            "status": "ok",
            "event": payload.event,
            "lead_id": lead.id,
            "new_status": lead.status,
        }

    raise HTTPException(400, "Unsupported event")


# ==================================================
# N8N HEALTH CHECK
# ==================================================

@app.get(
    "/api/integrations/n8n/health",
    tags=["n8n Integration"],
)
async def n8n_health_check(
    current_admin: dict = Depends(get_current_admin),
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.head(
                N8N_WEBHOOK_HEALTH_URL,
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=5.0,
            )

            is_reachable = response.status_code < 500

    except Exception:
        is_reachable = False

    if is_reachable:
        return {
            "status": "connected",
            "message": "n8n Cloud is reachable.",
        }

    return {
        "status": "unreachable",
        "message": "n8n Cloud is not responding.",
    }


# ==================================================
# EXECUTION LOG APIs
# ==================================================

@app.post(
    "/api/executions/log",
    response_model=schemas.ExecutionLogResponse,
    status_code=201,
    tags=["n8n Integration"],
)
def log_execution(
    payload: schemas.ExecutionLogCreate,
    db: Session = Depends(get_db),
    n8n_authenticated: bool = Depends(verify_n8n_api_key),
):
    """Create or update an n8n execution record."""

    data = payload.model_dump()

    data["started_at"] = to_utc_naive(data.get("started_at"))
    data["finished_at"] = to_utc_naive(data.get("finished_at"))

    existing = (
        db.query(models.ExecutionLog)
        .filter(
            models.ExecutionLog.execution_id == payload.execution_id
        )
        .first()
    )

    if existing:
        for field, value in data.items():
            setattr(existing, field, value)

        db.commit()
        db.refresh(existing)

        return existing

    new_log = models.ExecutionLog(**data)

    db.add(new_log)
    db.commit()
    db.refresh(new_log)

    return new_log


@app.get(
    "/api/workflows/executions",
    tags=["n8n Integration"],
)
def get_workflow_executions(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_admin),
):
    logs = (
        db.query(models.ExecutionLog)
        .order_by(models.ExecutionLog.created_at.desc())
        .limit(50)
        .all()
    )

    results = []

    for log in logs:
        raw_status = (log.status or "").lower()

        if raw_status in ("success", "succeeded", "completed"):
            display_status = "success"
        else:
            display_status = "error"

        duration_ms = None

        if log.started_at and log.finished_at:
            start = log.started_at
            finish = log.finished_at

            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)

            if finish.tzinfo is None:
                finish = finish.replace(tzinfo=timezone.utc)

            duration_ms = max(
                0,
                int((finish - start).total_seconds() * 1000),
            )

        results.append(
            {
                "id": log.execution_id,
                "execution_id": log.execution_id,
                "workflow_name": log.workflow_name,
                "workflow_id": log.workflow_id,
                "status": display_status,
                "started_at": to_bst_iso(log.started_at),
                "finished_at": to_bst_iso(log.finished_at),
                "duration_ms": duration_ms,
                "error_message": log.error_message,
            }
        )

    return results


@app.get(
    "/api/workflows",
    tags=["n8n Integration"],
)
def get_workflows(
    current_admin: dict = Depends(get_current_admin),
):
    """
    Stable dashboard workflow IDs are retained for compatibility.
    Actual n8n workflow names are supplied by n8n in execution logs.
    """

    return [
        {
            "id": 1,
            "name": "SmartBiz AI - Lead Automation",
            "active": True,
            "nodes": ["Webhook", "HTTP Request", "Gmail", "IF"],
        },
        {
            "id": 2,
            "name": "SmartBiz AI - Customer Follow-up",
            "active": True,
            "nodes": [
                "Schedule",
                "HTTP Request",
                "Split Out",
                "Gmail",
            ],
        },
        {
            "id": 3,
            "name": "SmartBiz AI - Notification Workflow",
            "active": True,
            "nodes": ["Webhook", "HTTP Request"],
        },
    ]
