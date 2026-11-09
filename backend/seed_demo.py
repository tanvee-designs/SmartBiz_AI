"""SmartBiz_AI — Demo data seeder

চালাও: python seed_demo.py

সব lead-এর created_at ৫ দিন পুরনো — যাতে GET /api/follow-ups/due?days=3 এ due হিসেবে আসে।
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta

from database import SessionLocal, engine, Base
import models


Base.metadata.create_all(bind=engine)
db = SessionLocal()

now = datetime.utcnow()

# ============================================================
# পুরনো data clear (শুধু demo-র জন্য)
# ============================================================
db.query(models.FollowUp).delete()
db.query(models.Notification).delete()
db.query(models.EmailLog).delete()
db.query(models.Customer).delete()
db.query(models.Report).delete()
db.query(models.Lead).delete()
db.commit()
print("🗑️  Old data cleared")


# ============================================================
# LEADS — status-এ ভিন্নতা, created_at ৩-১০ দিন পুরনো
# ============================================================
leads_data = [
    {
        "name": "Sara Khan",
        "email": "sara.demo@example.com",
        "phone": "01711111111",
        "company": "Sara Studio",
        "source": "website",
        "interest": "AI automation",
        "value": 50000,
        "status": "new",
        "created_at": now - timedelta(days=5),
    },
    {
        "name": "Imran Hossain",
        "email": "imran.demo@example.com",
        "phone": "01722222222",
        "company": "Imran Traders",
        "source": "facebook",
        "interest": "CRM integration",
        "value": 75000,
        "status": "contacted",
        "created_at": now - timedelta(days=7),
        "last_contacted_at": now - timedelta(days=4),
    },
    {
        "name": "Mitu Akter",
        "email": "mitu.demo@example.com",
        "phone": "01733333333",
        "company": "Mitu Boutique",
        "source": "referral",
        "interest": "Lead management",
        "value": 40000,
        "status": "qualified",
        "created_at": now - timedelta(days=10),
        "last_contacted_at": now - timedelta(days=5),
    },
    {
        "name": "Jamal Uddin",
        "email": "jamal.demo@example.com",
        "phone": "01744444444",
        "company": "Jamal Enterprise",
        "source": "linkedin",
        "interest": "Full automation",
        "value": 120000,
        "status": "converted",
        "created_at": now - timedelta(days=15),
        "last_contacted_at": now - timedelta(days=2),
    },
    {
        "name": "Farzana Rahman",
        "email": "farzana.demo@example.com",
        "phone": "01755555555",
        "company": "Farzana Fashion",
        "source": "website",
        "interest": "Email automation",
        "value": 30000,
        "status": "new",
        "created_at": now - timedelta(days=4),
    },
    {
        "name": "Kabir Ahmed",
        "email": "kabir.demo@example.com",
        "phone": "01766666666",
        "company": "Kabir Motors",
        "source": "google_forms",
        "interest": "Lead scoring",
        "value": 20000,
        "status": "lost",
        "created_at": now - timedelta(days=20),
        "last_contacted_at": now - timedelta(days=10),
    },
    {
        "name": "Lamia Sultana",
        "email": "lamia.demo@example.com",
        "phone": "01777777777",
        "company": "Lamia Foods",
        "source": "email",
        "interest": "Customer retention",
        "value": 45000,
        "status": "contacted",
        "created_at": now - timedelta(days=6),
        "last_contacted_at": now - timedelta(days=5),
    },
    {
        "name": "Jannatun Naher",
        "email": "jannatunnaher053@gmail.com",
        "phone": "01700000000",
        "company": "SmartBiz_AI Test",
        "source": "test",
        "interest": "Follow-up automation",
        "value": 60000,
        "status": "new",
        "created_at": now - timedelta(days=5),
    },
]

for data in leads_data:
    db.add(models.Lead(**data))
db.commit()
print(f"✅ Leads inserted: {db.query(models.Lead).count()}")


# ============================================================
# CUSTOMERS — converted lead থেকে
# ============================================================
customers_data = [
    {
        "name": "Jamal Uddin",
        "email": "jamal.demo@example.com",
        "phone": "01744444444",
        "company": "Jamal Enterprise",
        "total_deals": 3,
    },
    {
        "name": "Nadia Rahman",
        "email": "nadia.demo@example.com",
        "phone": "01612345678",
        "company": "Nadia Boutique",
        "total_deals": 1,
    },
]

for data in customers_data:
    db.add(models.Customer(**data))
db.commit()
print(f"✅ Customers inserted: {db.query(models.Customer).count()}")


# ============================================================
# FOLLOW-UPS — কিছু lead-এ follow-up history
# ============================================================
follow_ups_data = [
    {
        "lead_id": 2,   # imran
        "channel": "email",
        "status": "sent",
        "message": "Intro email — product overview",
        "created_at": now - timedelta(days=6),
    },
    {
        "lead_id": 2,
        "channel": "email",
        "status": "opened",
        "message": "Follow-up 1 — pricing details",
        "created_at": now - timedelta(days=4),
    },
    {
        "lead_id": 7,   # lamia
        "channel": "email",
        "status": "sent",
        "message": "Follow-up — demo scheduling",
        "created_at": now - timedelta(days=5),
    },
]

for data in follow_ups_data:
    db.add(models.FollowUp(**data))
db.commit()
print(f"✅ Follow-ups inserted: {db.query(models.FollowUp).count()}")


# ============================================================
# NOTIFICATIONS
# ============================================================
notifications_data = [
    {"message": "New lead from website: Sara Khan"},
    {"message": "New lead from facebook: Imran Hossain"},
    {"message": "Follow-up sent to Imran Hossain"},
    {"message": "Nadia Rahman converted to customer 🎉"},
    {"message": "New lead from linkedin: Jamal Uddin"},
]

for data in notifications_data:
    db.add(models.Notification(**data))
db.commit()
print(f"✅ Notifications inserted: {db.query(models.Notification).count()}")


# ============================================================
# EMAIL LOGS — welcome email history
# ============================================================
email_logs_data = [
    {
        "lead_id": 1,
        "to_email": "sara.demo@example.com",
        "subject": "SmartBiz AI-এ আপনাকে স্বাগতম!",
        "body": "প্রিয় Sara Khan, SmartBiz AI-এ আপনাকে স্বাগতম!",
        "generated_by": "ai",
        "status": "sent",
        "created_at": now - timedelta(days=4),
    },
    {
        "lead_id": 8,
        "to_email": "jannatunnaher053@gmail.com",
        "subject": "SmartBiz AI-এ আপনাকে স্বাগতম!",
        "body": "প্রিয় Jannatun Naher, SmartBiz AI-এ আপনাকে স্বাগতম!",
        "generated_by": "ai",
        "status": "pending",
        "created_at": now - timedelta(days=2),
    },
]

for data in email_logs_data:
    db.add(models.EmailLog(**data))
db.commit()
print(f"✅ Email logs inserted: {db.query(models.EmailLog).count()}")


# ============================================================
# REPORTS — AI business report
# ============================================================
import json

reports_data = [
    {
        "report_type": "ai_report",
        "title": "SmartBiz AI ব্যবসায়িক রিপোর্ট",
        "summary": "SmartBiz AI বর্তমানে ৮টি লিড নিয়ে কাজ করছে। গত ৭ দিনে ৪টি নতুন লিড এসেছে।",
        "insights": json.dumps([
            "৮টি লিডের মধ্যে ২টি contacted, ১টি qualified, ১টি converted",
            "ইমেইল অটোমেশন সিস্টেমে ২টি ইমেইল তৈরি হয়েছে",
            "Conversion rate প্রায় ১২.৫%",
        ], ensure_ascii=False),
        "recommendations": json.dumps([
            "qualified লিড (Mitu Akter)-এর সাথে দ্রুত যোগাযোগ করুন",
            "new লিডগুলোর (Sara, Farzana, Jannatun)-এ welcome email পাঠান",
            "lost লিড (Kabir Ahmed)-এর কারণ বিশ্লেষণ করুন",
        ], ensure_ascii=False),
    },
]

for data in reports_data:
    db.add(models.Report(**data))
db.commit()
print(f"✅ Reports inserted: {db.query(models.Report).count()}")


# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("🎉 Demo data seeded successfully!")
print("=" * 60)
print(f"Leads:         {db.query(models.Lead).count()}")
print(f"Customers:     {db.query(models.Customer).count()}")
print(f"Follow-ups:    {db.query(models.FollowUp).count()}")
print(f"Notifications: {db.query(models.Notification).count()}")
print(f"Email logs:    {db.query(models.EmailLog).count()}")
print(f"Reports:       {db.query(models.Report).count()}")
print("=" * 60)

# Due leads check
now_check = datetime.utcnow()
cutoff = now_check - timedelta(days=3)
due_leads = (
    db.query(models.Lead)
    .filter(models.Lead.status.in_(["new", "contacted"]))
    .filter(models.Lead.created_at <= cutoff)
    .all()
)
print(f"\n✅ Due leads (created_at <= {cutoff}): {len(due_leads)}")
for lead in due_leads:
    print(f"   - ID {lead.id}: {lead.name} ({lead.email}) — status={lead.status}")

db.close()