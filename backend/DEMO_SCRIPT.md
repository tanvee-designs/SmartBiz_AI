# SmartBiz_AI - Demo Script



Step-by-step demo flow for SmartBiz_AI backend presentation.



**\*\*Demo Duration:\*\*** 8-10 minutes

**\*\*Demo URL:\*\*** http\://127.0.0.1:8000 (local) / https\://smartbiz-ai-backend-8b8k.onrender.com (deployed)

**\*\*Swagger UI:\*\*** /docs

**\*\*Presented by:\*\*** Member 04 (Backend Developer)



**---**



**## Demo Objectives**



By the end of this demo, the audience should understand:



1\. How leads are captured from multiple sources (website, Facebook, forms)

2\. How AI generates personalized Bangla welcome emails

3\. How leads automatically convert to customers

4\. How n8n workflows integrate with the backend

5\. How real-time dashboard provides business insights

6\. How AI generates business reports with actionable recommendations



**---**



**## Pre-Demo Checklist**



**### 15 Minutes Before Demo**



\- Server running (uvicorn main:app --reload)

\- Swagger accessible (http\://127.0.0.1:8000/docs)

\- Admin JWT token ready (login + Authorize)

\- X-API-Key authorized (test-n8n-secret-123)

\- Database has demo data (6 leads, 2 customers, 2 reports)

\- verify_db.py shows all PASS

\- n8n workflow published + ready

\- GEMINI_API_KEY working (test welcome email)

\- Browser tabs open:

  - Tab 1: Swagger UI (/docs)

  - Tab 2: n8n dashboard (if showing workflow)

  - Tab 3: Frontend (if demoing integration)

\- Backup DB (SmartBiz_AI.db.backup)

\- Screenshots taken (in case of network issues)



**---**



**## Recent Backend Update Note

- Referral-related code was updated in `referral.py` after this demo script was drafted.
- This script does not assume a new referral endpoint or describe unverified referral behavior.
- Before demonstrating referral functionality, confirm its current route, authentication requirement, request body, and response in `/docs` and `API_REFERENCE.md`.

---

## Demo Flow - Step by Step**



**### Scene 1: Project Introduction (1 min)**



**\*\*Say:\*\***

"SmartBiz_AI is an AI-powered lead automation platform. Our backend is built with FastAPI, SQLite, and integrates with Google Gemini for AI capabilities and n8n for workflow automation. Let me show you how it works end-to-end."



**\*\*Show:\*\***

\- Open Swagger UI (http\://127.0.0.1:8000/docs)

\- Point out 11 tag groups: Health, Auth, Leads, Customers, Dashboard, Reports, Notifications, Email Logs, Automation, Follow-ups, n8n Integration



**\*\*Highlight:\*\***

"Swagger auto-generates documentation for all 30+ endpoints. Each endpoint is grouped by domain for easy navigation."



**\*\*Key Message:\*\*** Professional, well-organized API with self-documenting endpoints.



**---**



**### Scene 2: Authentication (30 sec)**



**\*\*Say:\*\***

"We use dual authentication - JWT for admin users and API keys for n8n service integration."



**\*\*Show:\*\***

1\. Click Authorize button

2. Point out the HTTPBearer and X-API-Key authentication schemes.
3. Show JWT authorization for admin endpoints and X-API-Key authorization for protected n8n/service endpoints.



**\*\*Say:\*\***

"Admin users log in with email and password to get a JWT token that expires in 30 minutes. n8n workflows use a shared API key for webhook security."



**\*\*Key Message:\*\*** Enterprise-grade security with role-based auth.



**---**



**### Scene 3: Lead Capture (Public API) (1.5 min)**



**\*\*Say:\*\***

"Let's start with lead capture. Our POST /api/leads endpoint is public - no auth required - so website forms, Facebook lead ads, and Google Forms can all post directly."



**\*\*Show:\*\***



In Swagger UI:



1\. POST /api/leads - Try it out

2\. Paste this body:



{

  "name": "Demo Lead",

  "email": "demo.lead\@example.com",

  "phone": "+8801712345678",

  "company": "Demo Company Ltd",

  "message": "Interested in your AI solution",

  "source": "website",

  "interest": "AI Automation",

  "value": 15000

}



3\. Click Execute

4\. Point out 201 Created + response object



**\*\*Say:\*\***

"Notice the lead is created with status: new and an auto-generated ID. This lead is now in our pipeline."



**\*\*Highlight (Duplicate Detection):\*\***



5. Submit the same complete lead payload again, keeping the same email address.

{
  "name": "Demo Lead Duplicate",
  "email": "demo.lead@example.com",
  "phone": "+8801712345678",
  "company": "Demo Company Ltd",
  "message": "Interested in your AI solution",
  "source": "website",
  "interest": "AI Automation",
  "value": 20000
}

6. Point out the 409 Conflict response for the duplicate email.



**\*\*Say:\*\***

"Our backend prevents duplicate leads by rejecting an email that already exists. The API returns 409 Conflict, preserving data integrity."



**\*\*Key Message:\*\*** Robust lead capture with automatic deduplication.



**---**



**### Scene 4: Lead Management (Admin) (1 min)**



**\*\*Say:\*\***

"Now let's look at how admins manage leads."



**\*\*Show:\*\***



1\. GET /api/leads - Try it out - Execute

2\. Point out the list of leads (6-7 leads)

3\. Try filter: GET /api/leads?status=new - Execute

4\. Try search: GET /api/leads?search=Karim - Execute



**\*\*Say:\*\***

"Admins can filter by status, source, and search across name, email, or company - all in a single API call."



**\*\*Show Status Change:\*\***



5\. PATCH /api/leads/{id}/status - Try it out

6\. Pick a "new" lead, change to contacted

7\. Execute

8\. Point out status change



**\*\*Say:\*\***

"When a lead is converted, the backend automatically creates a customer record. Let me show you that."



**---**



**### Scene 5: AI Welcome Email (Killer Feature #1) (2 min)**



**\*\*Say:\*\***

"This is one of our most impressive features - AI-generated personalized welcome emails in Bangla, powered by Google Gemini."



**\*\*Show:\*\***



1\. Pick a lead ID (e.g., GET /api/leads - note an ID)

2\. POST /automation/welcome-email/{lead_id} - Try it out

3\. Enter lead ID (e.g., 4)

4\. Execute

5\. Scroll through response:

   - subject: "SmartBiz AI welcome, Karim Hossain!"

   - body: Full Bangla text with personalization

   - source: "ai"

   - html: Complete HTML email template



**\*\*Say:\*\***

"Notice - the AI has:

\- Personalized with the lead's name and company

\- Written in Bangla (per our config)

\- Generated HTML for proper email rendering

\- Included company-specific messaging



This is a complete, ready-to-send welcome email - generated in under 3 seconds."



**\*\*Show Email Log:\*\***



6\. GET /email-logs - Execute

7\. Point out the new log with status: "pending"



**\*\*Say:\*\***

"The email is logged with pending status. When n8n sends it via Gmail, the workflow updates status to sent. Full audit trail."



**\*\*Key Message:\*\*** AI-powered personalization at scale, in local language.



**---**



**### Scene 6: Lead Conversion - Auto Customer (1 min)**



**\*\*Say:\*\***

"When a lead converts, we automatically create a customer. No manual data entry."



**\*\*Show:\*\***



1\. PATCH /api/leads/{id}/status - Try it out

2\. Pick a lead (e.g., id=5), change status to converted

3\. Execute

4\. Then GET /api/customers - Execute

5\. Point out the new customer record (same email, total_deals: 1)



**\*\*Say:\*\***

"The moment a lead converts:

\- Customer record created (or total_deals incremented if exists)

\- Notification generated

\- Lead status updated



All in a single API call."



**\*\*Key Message:\*\*** Automated data flow - no manual duplication.



**---**



**### Scene 7: n8n Integration (Killer Feature #2) (1.5 min)**



**\*\*Say:\*\***

"Now let's see the n8n integration - how our backend connects to automation workflows."



**\*\*Show:\*\***



Webhook ping (connection test):



1. POST /api/webhooks/n8n - Try it out (X-API-Key required)

2\. Body: {"event": "ping"}

3\. Execute - 200 OK



**\*\*Say:\*\***

"n8n workflows authenticate with X-API-Key - we just verified the connection."



Show status change event:



4\. POST /api/webhooks/n8n - Body:



{

  "event": "lead_status_changed",

  "lead_id": 5,

  "status": "converted"

}



5\. Execute

6\. Point out response: {"status": "ok", "new_status": "converted"}



**\*\*Say:\*\***

"n8n can trigger status changes from outside, and the backend handles all the business logic - customer creation, notifications, everything."



**\*\*Key Message:\*\*** Bi-directional integration with external automation.



Optional - if n8n workflow is live:



\- Show n8n workflow execution on the n8n dashboard

\- Show execution log in GET /api/workflows/executions



**---**



**### Scene 8: AI Business Report (Killer Feature #3) (1.5 min)**



**\*\*Say:\*\***

"Here's the second killer feature - AI-generated business reports in Bangla, analyzing our entire pipeline."



**\*\*Show:\*\***



1\. POST /api/reports/generate - Try it out

2\. Execute (no body needed)

3\. Scroll through response slowly:

   - title: "SmartBiz AI business report"

   - summary: "SmartBiz AI acquired 6 new leads in last 7 days..."

   - insights: 3 data-driven observations

   - recommendations: 3 actionable recommendations



**\*\*Say:\*\***

"Look at the intelligence here. The AI analyzed:

\- 6 leads over 7 days

\- Status distribution

\- Email delivery rate (100%)

\- Conversion rate (16.7%)



It generated 3 insights and 3 recommendations - all in Bangla, all actionable. This is a real business intelligence report, not a template."



**\*\*Show Reports List:\*\***



4\. GET /api/reports - Execute

5\. Point out the report is saved with timestamp



**\*\*Key Message:\*\*** AI-driven business intelligence in local language.



**---**



**### Scene 9: Real-Time Dashboard (1 min)**



**\*\*Say:\*\***

"Our dashboard gives real-time business metrics."



**\*\*Show:\*\***



1\. GET /api/dashboard/stats - Try it out - Execute

2\. Walk through the response:



**\*\*Say:\*\***

\- total_leads: 6 - total pipeline

\- leads_by_status: 3 new, 2 contacted, 1 converted

\- conversion_rate: 16.7% - 1 of 6 converted

\- pipeline_value: BDT 50,499 - active pipeline value

\- converted_value: BDT 3,500 - closed deals

\- emails_sent: 2 - AI emails sent

\- unread_notifications: 12 - pending admin actions



Every metric is calculated live from the database - no caching, always accurate.



**\*\*Key Message:\*\*** Real-time business intelligence at a glance.



**---**



**### Scene 10: Notifications (30 sec)**



**\*\*Say:\*\***

"Every significant event creates a notification for admin awareness."



**\*\*Show:\*\***



1. GET /api/notifications - Execute (admin JWT required)

2\. Point out the variety:

   - "New lead from website: ..."

   - "Follow-up (email) sent to ..."

   - "Lead converted to customer: ..."



**\*\*Say:\*\***

"12 notifications from the recent demo activity - every lead creation, follow-up, and conversion is tracked."



Show bulk mark:



3. PATCH /api/notifications/read-all - Execute (admin JWT required)

4\. Execute - {"updated": 11}



**\*\*Say:\*\***

"One API call clears the entire notification inbox."



**---**



**### Scene 11: Follow-up Automation (30 sec)**



**\*\*Say:\*\***

"Finally, our follow-up system - automated detection of leads that need attention."



**\*\*Show:\*\***



1. GET /api/follow-ups/due?days=3 - Try it out - Execute (X-API-Key required)

2\. Point out structure: lead_id, name, days_since_contact, last_contact_at

3\. All datetimes in BST (+06:00)



**\*\*Say:\*\***

"n8n calls this endpoint daily. Any lead not contacted in 3+ days is returned. The workflow then sends follow-up emails automatically.



Key features:

\- Converted/lost leads auto-skipped

\- Duplicate prevention (409 if follow-up within 3 days)

\- Consistent BST timezone



This is a fully automated follow-up engine."



**---**



**### Scene 12: Wrap-Up (30 sec)**



**\*\*Say:\*\***

"Let me summarize what we've built:



Backend:

\- FastAPI with 30+ documented endpoints

\- SQLite database (7 tables)

\- Dual auth (JWT + API Key)

\- 57/57 tests passing (historical baseline from 2026-11-16; rerun current tests before presenting as current)



AI Features:

\- Bangla welcome email generation

\- Bangla business report generation



Automation:

\- n8n workflow integration

\- Auto follow-up detection

\- Auto customer creation



Intelligence:

\- Real-time dashboard

\- Auto notifications

\- Duplicate detection



Deployment:

\- Deployed on Render; verify the current production integration before the live demo

\- CORS-enabled for frontend

\- Production-quality code



Any questions?"



**---**



**## Key Talking Points**



**### What Makes This Backend Professional**



1\. 57/57 Tests Passed (historical baseline from 2026-11-16; rerun current tests before presenting as current)

2\. Dual Authentication - Security-first design

3\. AI Integration - Gemini for real intelligence

4\. Complete Documentation - 4 comprehensive docs

5\. Error Handling - 422, 409, 404, 500 with clean messages

6\. Timezone Consistency - All BST (+06:00)

7\. Auto Side Effects - Customer create, notifications, status updates

8\. n8n Integration - 4 event types, secured webhooks

9\. Idempotency - Execution logs, duplicate prevention

10\. Production-Ready - Render-ready, PostgreSQL-switchable



**### What Makes This Backend Impressive**



1\. AI in Local Language - Bangla email + report (rare feature)

2\. End-to-End Automation - Lead to Customer to Follow-up

3\. Real Business Intelligence - AI insights + recommendations

4\. Duplicate Detection - Data integrity maintained

5\. Fast Response - AI email in under 3 seconds



**---**



**## Sample Q&A - Be Ready**



**### Q: "What database are you using?"**



**\*\*A:\*\***

"Currently SQLite for development - it's file-based and zero-config. For production, we can switch to PostgreSQL by changing just one environment variable (DATABASE_URL). The SQLAlchemy ORM makes this seamless."



**### Q: "How does the AI work?"**



**\*\*A:\*\***

"We use Google Gemini API. When a lead is created, we call Gemini with lead context (name, company, etc.) and get back a personalized Bangla email. Same for business reports - we send the lead data and get back insights + recommendations. All AI calls are wrapped in error handling with fallback to template if AI fails."



**### Q: "How is authentication secured?"**



**\*\*A:\*\***

"Two layers:

\- Admin: JWT tokens with HS256 signature, 30-minute expiry

\- n8n: Shared API key stored in .env, verified with constant-time comparison (hmac.compare_digest) to prevent timing attacks



Both methods fail securely with 401 on invalid credentials."



**### Q: "What happens if the AI fails?"**



**\*\*A:\*\***

"Our generate_email.py has fallback logic - if Gemini fails, it returns a template-based email. The API still returns 200 with source: 'template'. For reports, if AI fails, we return 500 with clear error, and admin can retry."



**### Q: "How scalable is this?"**



**\*\*A:\*\***

"The backend is horizontally scalable - multiple Uvicorn workers can run behind a load balancer. We use SQLAlchemy with connection pooling. For high volume, we'd switch SQLite to PostgreSQL and add Redis caching. For the current demo scale (10-100 leads/day), current setup handles it easily."



**### Q: "How many leads can it handle?"**



**\*\*A:\*\***

"With SQLite, single instance handles \~1000 concurrent requests easily. For higher scale, PostgreSQL + connection pooling supports millions of leads. The code architecture already supports this migration."



**### Q: "What about data backup?"**



**\*\*A:\*\***

"SQLite file is backed up by copying SmartBiz_AI.db. In production (PostgreSQL), Render handles automated daily backups. We also have verify_db.py script for integrity checks."



**### Q: "Can frontend integrate easily?"**



**\*\*A:\*\***

"Yes - CORS is enabled for all origins. Every response is JSON with consistent error format. The API_REFERENCE.md has complete request/response examples with cURL for each endpoint. Frontend just needs to call the endpoints."



**### Q: "What's not included?"**



**\*\*A:\*\***

"We intentionally kept scope tight for the demo:

\- Single admin (no multi-user RBAC)

\- No email retry queue (n8n handles retries)

\- Day 1/3/7 staged follow-ups (currently single 3-day interval)

\- No rate limiting



All are documented in README.md under Known Limitations. These are next-phase features, not blockers."



**---**



**## Demo Tips**



**### Before Demo**



\- Rehearse once - timing matters

\- Test all API calls - don't discover failures live

\- Backup DB - in case of accidental data change

\- Have screenshots ready - in case of network issues

\- Restart server - fresh state



**### During Demo**



\- Speak slowly - let audience follow

\- Point at key fields - highlight important data

\- Show IDs - emphasize consistent data

\- Show side effects - auto-created records

\- Show AI output - the Bangla content is impressive



**### If Something Fails**



\- Stay calm - technical demos always have hiccups

\- Use screenshots - show the expected result

\- Explain what should happen - verbally

\- Move on - don't debug live



**---**



**## Demo Data (Pre-Loaded)**



**### 6 Leads**



\| ID | Name | Source | Status | Value |

\|----|------|--------|--------|-------|

\| 1 | Rahim Ahmed Updated | website | contacted | BDT 5,000 |

\| 3 | Fatima Khan | facebook | converted | BDT 3,500 |

\| 4 | Karim Hossain | google_forms | contacted | BDT 9,999 |

\| 5 | Nasrin Sultana | linkedin | new | BDT 25,000 |

\| 6 | Jamal Uddin | referral | new | BDT 6,000 |

\| 7 | Sadia Rahman | email | new | BDT 4,500 |



**### 2 Customers**



\- Fatima Khan (fatima.khan\@example.com) - manual

\- Fatima Khan (fatima\@example.com) - auto-created



**### 2 Reports**



\- id=1: AI-generated Bangla business report

\- id=2: Manual "Q4 Summary"



**### 12 Notifications**



\- New lead notifications (6)

\- Follow-up sent (1)

\- Follow-up failed (1)

\- Conversion notifications (2)

\- Others (2)



**### 2 Email Logs**



\- id=1: Rahim welcome email (status: sent)

\- id=2: Karim welcome email (status: sent)



**### 2 Follow-ups**



\- id=1: Karim (sent)

\- id=2: Karim (failed)



**---**



**## Highlight Numbers for Demo**



\- 57/57 tests passing (historical baseline from 2026-11-16; rerun current tests before presenting as current) (100%)

\- 30+ API endpoints

\- 7 database tables

\- 11 Swagger tag groups

\- BDT 50,499 pipeline value

\- 16.7% conversion rate

\- AI-generated Bangla content (real, not template)

\- 4 n8n event types

\- Under 3 seconds AI email generation

\- 100% email delivery rate



**---**



**## Demo Sign-off**



**\*\*Demo Length:\*\*** 8-10 min (talk) + 3-5 min (Q&A)



**\*\*Tested By:\*\*** Member 04



**\*\*Dry Run Completed:\*\*** Yes (on 2026-11-16)



**\*\*Ready for Live Demo:\*\*** Re-check deployment, credentials, demo data, and current test results immediately before presenting



**---**



For setup instructions, see README.md

For API details, see API_REFERENCE.md

For test evidence, see TEST_RESULTS.md
