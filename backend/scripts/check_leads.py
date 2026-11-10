import sqlite3
from datetime import datetime, timedelta

c = sqlite3.connect('SmartBiz_AI.db')

# 1. Total leads
print(f"Total leads: {c.execute('SELECT COUNT(*) FROM leads').fetchone()[0]}")

# 2. new/contacted leads + created_at
print("\n=== new/contacted leads ===")
leads = c.execute(
    "SELECT id, email, status, created_at, last_contacted_at "
    "FROM leads WHERE status IN ('new', 'contacted')"
).fetchall()

cutoff = datetime.utcnow() - timedelta(days=3)
print(f"Cutoff (3 days ago): {cutoff}\n")

for r in leads:
    created = r[3]
    created_dt = datetime.fromisoformat(created) if isinstance(created, str) else created
    due = created_dt <= cutoff
    print(f"ID={r[0]} | email={r[1]} | status={r[2]} | created={r[3]} | due={due}")

# 3. follow_ups column
print("\n=== follow_ups columns ===")
print([r[1] for r in c.execute('PRAGMA table_info(follow_ups)').fetchall()])

c.close()