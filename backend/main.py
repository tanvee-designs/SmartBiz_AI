from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db
from n8n_client import send_lead_to_n8n

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartBiz_AI")


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