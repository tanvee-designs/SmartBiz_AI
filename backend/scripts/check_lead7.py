import sqlite3

c = sqlite3.connect('SmartBiz_AI.db')

# Total leads
total = c.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
print(f"Total leads: {total}")

# Lead 7
lead7 = c.execute("SELECT id, name, email, status, created_at FROM leads WHERE id=7").fetchone()
print(f"Lead 7: {lead7}")

# Query-র শর্ত অনুযায়ী leads
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=3)
print(f"Cutoff (3 days ago): {cutoff}")

candidates = c.execute("""
    SELECT id, name, email, status, created_at, last_contacted_at
    FROM leads
    WHERE status IN ('new', 'contacted')
""").fetchall()

print(f"\nCandidates (new/contacted): {len(candidates)}")
for row in candidates:
    print(f"  {row}")

c.close()