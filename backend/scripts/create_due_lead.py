"""Testing-এর জন্য ৩ দিন পুরনো due lead তৈরি করে।"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from database import SessionLocal, engine, Base
from models import Lead

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# ৩ দিন পুরনো "new" status lead
old_lead = Lead(
    name="Due Test Lead (3 days old)",
    email="duetest3d@example.com",
    phone="01788888888",
    company="Due Test Co",
    source="test",
    status="new",
    created_at=datetime.utcnow() - timedelta(days=3, hours=2),
    last_contacted_at=None,
)
db.add(old_lead)

# ৫ দিন পুরনো "contacted" lead, last_contacted ৪ দিন আগে
old_contacted = Lead(
    name="Due Contacted Lead (4 days since last contact)",
    email="duecontacted@example.com",
    phone="01777777777",
    company="Due Contacted Co",
    source="test",
    status="contacted",
    created_at=datetime.utcnow() - timedelta(days=10),
    last_contacted_at=datetime.utcnow() - timedelta(days=4),
)
db.add(old_contacted)

db.commit()
print(f"✅ Created test leads:")
print(f"   - {old_lead.email} (new, 3 days old)")
print(f"   - {old_contacted.email} (contacted, last contact 4 days ago)")
db.close()