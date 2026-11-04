from typing import List, Literal, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db
from generate_email import generate_welcome_email
from n8n_client import send_lead_to_n8n

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartBiz_AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "SmartBiz_AI Backend is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


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
    email = lead.email.lower()

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
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)

    lead_data = schemas.LeadResponse.model_validate(new_lead).model_dump(mode="json")
    background_tasks.add_task(send_lead_to_n8n, lead_data)

    return new_lead


@app.get("/api/leads", response_model=List[schemas.LeadResponse])
def list_leads(
    lead_status: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(models.Lead)
    if lead_status:
        query = query.filter(models.Lead.status == lead_status)
    return query.order_by(models.Lead.created_at.desc()).all()


@app.patch(
    "/api/leads/{lead_id}",
    response_model=schemas.LeadResponse,
    responses={404: {"description": "Lead not found"}},
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


# ---- Day 3: Welcome Email Automation (Member 3 module) ----


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

    return {"log_id": log.id, "to": lead.email, **result}


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
    return db.query(models.EmailLog).order_by(models.EmailLog.created_at.desc()).all()