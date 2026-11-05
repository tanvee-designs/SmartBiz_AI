"""Jannatun-এর lead আবার due অবস্থায় ফিরিয়ে আনে।"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import Lead, FollowUp

Base.metadata.create_all(bind=engine)
db = SessionLocal()

EMAIL = "jannatunnaher053@gmail.com"

lead = db.query(Lead).filter(Lead.email == EMAIL).first()

if not lead:
    print(f"❌ Lead not found for {EMAIL}")
    print("   আগে চালাও: python scripts\\create_test_lead_jannatun.py")
    db.close()
    sys.exit(1)

# Lead reset
lead.status = "new"
lead.last_contacted_at = None
lead.created_at = datetime.utcnow() - timedelta(days=3, hours=2)

# Jannatun-এর সব follow-up delete (due list-এ আসার জন্য)
deleted = db.query(FollowUp).filter(FollowUp.lead_id == lead.id).delete()
db.commit()

print(f"✅ Lead reset successfully")
print(f"   Lead ID:            {lead.id}")
print(f"   Name:               {lead.name}")
print(f"   Email:              {lead.email}")
print(f"   Status:             {lead.status}")
print(f"   Created:            {lead.created_at} (3 days old)")
print(f"   Last contacted:     {lead.last_contacted_at}")
print(f"   Follow-ups deleted: {deleted}")

db.close()