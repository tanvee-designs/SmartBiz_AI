"""Jannatun-এর n8n End-to-End test-এর জন্য due lead তৈরি করে।"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import Lead

Base.metadata.create_all(bind=engine)
db = SessionLocal()

EMAIL = "jannatunnaher053@gmail.com"

# পুরনো lead থাকলে delete (duplicate এড়াতে)
existing = db.query(Lead).filter(Lead.email == EMAIL).first()
if existing:
    db.delete(existing)
    db.commit()
    print(f"🗑️  Old lead deleted (id: {existing.id})")

# নতুন due lead — ৩ দিন পুরনো, status "new"
new_lead = Lead(
    name="Jannatun Naher",
    email=EMAIL,
    phone="01700000000",
    company="SmartBiz_AI Test",
    source="test",
    status="new",
    created_at=datetime.utcnow() - timedelta(days=3, hours=2),  # ৩ দিনের বেশি পুরনো
    last_contacted_at=None,
)
db.add(new_lead)
db.commit()
db.refresh(new_lead)

print(f"\n✅ Lead created successfully")
print(f"   Lead ID: {new_lead.id}")
print(f"   Name:    {new_lead.name}")
print(f"   Email:   {new_lead.email}")
print(f"   Status:  {new_lead.status}")
print(f"   Created: {new_lead.created_at} (3 days old)")
print(f"\n📋 Jannatun-কে এই Lead ID দাও: {new_lead.id}")

db.close()