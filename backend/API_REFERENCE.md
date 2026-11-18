# SmartBiz_AI Backend - API Reference

Complete REST API documentation for SmartBiz_AI backend.

**Base URL:** http://127.0.0.1:8000 (dev) / https://smartbiz-ai-backend-8b8k.onrender.com (prod)

**API Version:** 1.0.0

**Last Updated:** 2026-11-16

---

## Table of Contents

1. Authentication
2. Health Endpoints
3. Auth Endpoints
4. Lead Endpoints
5. Customer Endpoints
6. Dashboard Endpoints
7. Report Endpoints
8. Notification Endpoints
9. Email Log Endpoints
10. Automation Endpoints
11. Follow-up Endpoints
12. n8n Integration Endpoints
13. Error Codes Reference
14. Data Models

---

## Authentication

The API uses dual authentication:

### 1. JWT Bearer Token (Admin)

Header: Authorization: Bearer token

Obtain token: POST /api/auth/login

Expiry: 30 minutes

Used for: Admin dashboard endpoints (leads read, customers, dashboard, reports, notification listing/updates, email logs, automation, follow-ups list, n8n health)

### 2. API Key (n8n Service)

Header: X-API-Key: key

Obtain key: From .env - N8N_API_KEY value

Used for: n8n integration endpoints (notification creation, webhooks, follow-ups due/create, execution logs)

### Public Endpoints (No Auth)

- POST /api/leads - Lead capture from website/forms (duplicate email returns 409)
- GET / - Root
- GET /health - Health check
- POST /api/auth/login - Login

---

## Health Endpoints

### GET /

Description: Root endpoint - confirms server is running.

Auth: None

Request:

GET /

Response (200):

{
  "message": "SmartBiz_AI Backend is running",
  "status": "success"
}

---

### GET /health

Description: Health check for monitoring/load balancers.

Auth: None

Request:

GET /health

Response (200):

{
  "status": "ok",
  "message": "Backend is healthy"
}

---

## Auth Endpoints

### POST /api/auth/login

Description: Admin login. Returns JWT access token.

Auth: None (public)

Request:

POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@smartbiz.ai",
  "password": "admin123"
}

Response (200):

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}

Error Responses:

Code 401 - Invalid credentials
Body: {"detail": "Invalid email or password."}

Code 422 - Missing fields
Body: {"detail": "Validation failed", "errors": [...]}

cURL:

curl -X POST http://127.0.0.1:8000/api/auth/login   -H "Content-Type: application/json"   -d '{"email": "admin@smartbiz.ai", "password": "admin123"}'

---

## Lead Endpoints

### POST /api/leads

Description: Create a new lead (public). Duplicate email addresses are rejected with HTTP 409.

Auth: None (public)

Request:

POST /api/leads
Content-Type: application/json

{
  "name": "Rahim Ahmed",
  "email": "rahim@example.com",
  "phone": "+8801712345678",
  "company": "ABC Technologies",
  "message": "Interested in AI CRM",
  "source": "website",
  "interest": "AI Automation",
  "value": 5000
}

Fields:

- name (string, required, 2-100 chars)
- email (email, required)
- phone (string, optional, max 30)
- company (string, optional, max 150)
- message (string, optional)
- source (enum, optional): manual, website, facebook, google_forms, linkedin, referral, email, other
- interest (string, optional, max 200)
- value (float, optional, >= 0, default 0)

Response (201 Created):

{
  "id": 1,
  "name": "Rahim Ahmed",
  "email": "rahim@example.com",
  "phone": "+8801712345678",
  "company": "ABC Technologies",
  "message": "Interested in AI CRM",
  "source": "website",
  "interest": "AI Automation",
  "value": 5000,
  "status": "new",
  "last_contacted_at": null,
  "created_at": "2026-11-16T09:53:50.066149+06:00"
}

Duplicate Handling:

If email already exists (case-insensitive), returns HTTP 409 Conflict. No duplicate lead is created.

Error Responses:

Code 422 - Validation error
Body: {"detail": "Validation failed", "errors": [...]}

cURL:

curl -X POST http://127.0.0.1:8000/api/leads   -H "Content-Type: application/json"   -d '{"name": "Rahim Ahmed", "email": "rahim@example.com", "source": "website", "value": 5000}'

---

### GET /api/leads

Description: List all leads (newest first). Supports filtering and search.

Auth: JWT

Query Parameters:

- status (enum): Filter by new, contacted, qualified, converted, lost
- source (string): Filter by source
- search (string): Search in name, email, or company

Request Examples:

GET /api/leads
GET /api/leads?status=new
GET /api/leads?source=linkedin
GET /api/leads?search=Rahim
GET /api/leads?status=new&search=Khan

Response (200):

[
  {
    "id": 1,
    "name": "Rahim Ahmed",
    "email": "rahim@example.com",
    "status": "new",
    "source": "website",
    "value": 5000.0,
    "created_at": "2026-11-16T09:53:50+06:00"
  }
]

cURL:

curl -X GET "http://127.0.0.1:8000/api/leads?status=new"   -H "Authorization: Bearer token"

---

### GET /api/leads/{lead_id}

Description: Get single lead by ID.

Auth: JWT

Request:

GET /api/leads/1

Response (200):

{
  "id": 1,
  "name": "Rahim Ahmed",
  "email": "rahim@example.com",
  "phone": "+8801712345678",
  "company": "ABC Technologies",
  "message": "Interested in AI CRM",
  "source": "website",
  "interest": "AI Automation",
  "value": 5000,
  "status": "new",
  "last_contacted_at": null,
  "created_at": "2026-11-16T09:53:50+06:00"
}

Error Responses:

Code 404 - Lead not found
Body: {"detail": "Lead not found"}

---

### PUT /api/leads/{lead_id}

Description: Update lead (partial - only provided fields change).

Auth: JWT

Request:

PUT /api/leads/1
Content-Type: application/json

{
  "value": 9999,
  "interest": "Premium Plan"
}

All Fields (all optional):

name, email, phone, company, message, source, interest, value, status

Response (200): Updated lead object.

Error Responses:

Code 400 - No fields to update
Body: {"detail": "No fields to update"}

Code 404 - Lead not found
Body: {"detail": "Lead not found"}

Code 409 - Email conflict
Body: {"detail": "Another lead with this email already exists"}

Note: If status changes to converted, a Customer record is auto-created.

---

### PATCH /api/leads/{lead_id}/status

Description: Update only the lead status.

Auth: JWT

Request:

PATCH /api/leads/1/status
Content-Type: application/json

{
  "status": "contacted"
}

Valid statuses: new, contacted, qualified, converted, lost

Response (200): Updated lead object.

Side Effect: If status becomes converted, a Customer record is auto-created (or total_deals incremented if customer exists).

---

### DELETE /api/leads/{lead_id}

Description: Delete a lead + its follow-ups + its email logs.

Auth: JWT

Request:

DELETE /api/leads/1

Response (204 No Content): Empty body.

Error Responses:

Code 404 - Lead not found
Body: {"detail": "Lead not found"}

Note: Cascade deletes follow-ups and email logs (no orphans).

---

## Customer Endpoints

### POST /api/customers

Description: Create a customer manually (typically created automatically when lead converts).

Auth: JWT

Request:

POST /api/customers
Content-Type: application/json

{
  "name": "Fatima Khan",
  "email": "fatima@example.com",
  "phone": "+8801812345678",
  "company": "Khan Fashion",
  "total_deals": 1
}

Response (201 Created):

{
  "id": 1,
  "name": "Fatima Khan",
  "email": "fatima@example.com",
  "phone": "+8801812345678",
  "company": "Khan Fashion",
  "total_deals": 1,
  "created_at": "2026-11-16T11:26:33+06:00"
}

Error Responses:

Code 409 - Email exists
Body: {"detail": "Customer with this email already exists"}

---

### GET /api/customers

Description: List all customers (newest first).

Auth: JWT

Request:

GET /api/customers

Response (200): Array of customer objects.

---

## Dashboard Endpoints

### GET /api/dashboard/stats

Description: Summary statistics for dashboard.

Auth: JWT

Request:

GET /api/dashboard/stats

Response (200):

{
  "total_leads": 6,
  "new_leads_last_7_days": 6,
  "leads_by_status": {
    "new": 3,
    "contacted": 2,
    "qualified": 0,
    "converted": 1,
    "lost": 0
  },
  "leads_by_source": {
    "website": 1,
    "facebook": 1,
    "google_forms": 1,
    "linkedin": 1,
    "referral": 1,
    "email": 1
  },
  "total_customers": 2,
  "conversion_rate": 16.7,
  "pipeline_value": 50499.0,
  "converted_value": 3500.0,
  "follow_ups_sent": 1,
  "emails_sent": 2,
  "unread_notifications": 0
}

Fields Explained:

- conversion_rate: (converted / total_leads) * 100
- pipeline_value: Sum of value where status NOT IN (converted, lost)
- converted_value: Sum of value where status = converted
- new_leads_last_7_days: Leads created in last 7 days

---

## Report Endpoints

### POST /api/reports

Description: Save a report manually.

Auth: JWT

Request:

POST /api/reports
Content-Type: application/json

{
  "title": "Q4 Summary",
  "summary": "Strong pipeline growth",
  "insights": ["Lead volume up 20%", "Conversion at 16.7%"],
  "recommendations": ["Focus on LinkedIn", "Follow up within 24h"],
  "report_type": "manual"
}

Response (201 Created): Report object.

---

### GET /api/reports

Description: List all reports (newest first).

Auth: JWT

Response (200): Array of report objects.

---

### POST /api/reports/generate

Description: Generate AI business report from leads + email logs (uses Gemini).

Auth: JWT

Request:

POST /api/reports/generate

No body required.

Response (201 Created):

{
  "id": 1,
  "report_type": "ai_report",
  "title": "SmartBiz AI business report",
  "summary": "SmartBiz AI acquired 6 new leads in last 7 days...",
  "insights": [
    "1 of 6 leads converted",
    "2 AI emails sent successfully",
    "100% email delivery rate"
  ],
  "recommendations": [
    "Contact 3 new leads quickly",
    "Increase welcome email coverage",
    "Maintain 100% email success rate"
  ],
  "created_at": "2026-11-16T12:07:11+06:00"
}

Error Responses:

Code 500 - Module missing
Body: {"detail": "generate_report module not found"}

Code 500 - Gemini API fails
Body: {"detail": "Report generation failed: reason"}

---

## Notification Endpoints

### POST /api/notifications

Description: Create a notification from an authenticated n8n workflow.

Auth: X-API-Key

Request:

POST /api/notifications
Content-Type: application/json

{
  "message": "Custom notification message"
}

Response (201 Created): Notification object.

---

### GET /api/notifications

Description: List all notifications (newest first).

Auth: JWT

Response (200):

[
  {
    "id": 12,
    "message": "Follow-up (email) failed for Karim Hossain",
    "is_read": "false",
    "created_at": "2026-11-16T11:49:56+06:00"
  }
]

---

### PATCH /api/notifications/read-all

Description: Mark all unread notifications as read.

Auth: JWT

Request:

PATCH /api/notifications/read-all

Response (200):

{
  "updated": 11
}

---

### PATCH /api/notifications/{id}/read

Description: Mark one notification as read.

Auth: JWT

Request:

PATCH /api/notifications/12/read

Response (200):

{
  "id": 12,
  "message": "Follow-up (email) failed for Karim Hossain",
  "is_read": "true",
  "created_at": "2026-11-16T11:49:56+06:00"
}

Error Responses:

Code 404 - Notification not found
Body: {"detail": "Notification not found"}

---

## Email Log Endpoints

### GET /email-logs

Description: List all email logs (newest first).

Auth: JWT

Note: No /api prefix.

Request:

GET /email-logs

Response (200):

[
  {
    "id": 2,
    "lead_id": 4,
    "to_email": "karim@example.com",
    "subject": "SmartBiz AI welcome",
    "body": "Dear Karim Hossain,...",
    "generated_by": "ai",
    "status": "sent",
    "created_at": "2026-11-16T12:04:55+06:00"
  }
]

---

### PATCH /email-logs/{log_id}/status

Description: Update email log status.

Auth: JWT

Note: No /api prefix.

Query Parameters:

- status (required): pending, sent, failed

Request:

PATCH /email-logs/2/status?status=sent

Response (200): Updated email log object.

Error Responses:

Code 404 - Log not found
Body: {"detail": "Log not found"}

---

## Automation Endpoints

### POST /automation/welcome-email/{lead_id}

Description: Generate AI welcome email for a lead (Bangla, HTML, personalized).

Auth: JWT

Request:

POST /automation/welcome-email/4

No body required.

Response (200):

{
  "log_id": 2,
  "to": "karim@example.com",
  "subject": "SmartBiz AI welcome, Karim Hossain!",
  "body": "Dear Karim Hossain, Welcome to SmartBiz AI!...",
  "source": "ai",
  "html": "div style=...div"
}

Error Responses:

Code 404 - Lead not found
Body: {"detail": "Lead not found"}

Code 500 - Module missing
Body: {"detail": "generate_email module not found"}

Code 500 - Gemini API fails
Body: {"detail": "Email generation failed: reason"}

Note: Creates an email_log record with status=pending automatically.

---

## Follow-up Endpoints

### GET /api/follow-ups/due

Description: List leads not contacted within days days. Used by n8n follow-up workflow.

Auth: X-API-Key

Query Parameters:

- days (int, default 3, range 0-90)

Request:

GET /api/follow-ups/due?days=3
X-API-Key: your-key

Response (200):

{
  "count": 1,
  "days": 3,
  "leads": [
    {
      "lead_id": 4,
      "name": "Karim Hossain",
      "email": "karim@example.com",
      "company": "Hossain Traders",
      "status": "contacted",
      "created_at": "2026-11-11T19:30:07+06:00",
      "last_contacted_at": "2026-11-11T19:30:07+06:00",
      "last_contact_at": "2026-11-11T19:30:07+06:00",
      "days_since_contact": 4
    }
  ]
}

Behavior:

- Only includes leads with status IN (new, contacted)
- Converted/lost leads auto-skipped
- last_contact_at = max of (created_at, last sent email, last follow-up, last_contacted_at)
- All datetimes in BST (+06:00)

---

### POST /api/follow-ups

Description: Log a follow-up attempt (sent or failed).

Auth: X-API-Key

Request:

POST /api/follow-ups
X-API-Key: your-key
Content-Type: application/json

{
  "lead_id": 4,
  "channel": "email",
  "status": "sent",
  "message": "Day-3 follow-up email sent"
}

Fields:

- lead_id (int, required)
- channel (string, optional, default email)
- status (enum, optional): sent / failed
- note (string, optional)
- message (string, optional)

Response (201 Created):

{
  "id": 1,
  "lead_id": 4,
  "channel": "email",
  "status": "sent",
  "note": null,
  "message": "Day-3 follow-up email sent",
  "created_at": "2026-11-16T11:42:31+06:00"
}

Side Effects (status=sent only):

- lead.last_contacted_at updated
- lead.status becomes contacted if it was new
- New notification created

Error Responses:

Code 404 - Lead not found
Body: {"detail": "Lead not found"}

Code 409 - Duplicate sent within 3 days
Body: {"detail": "A follow-up was already sent recently"}

Note: Duplicate check applies only to status=sent. status=failed always succeeds.

---

### GET /api/follow-ups

Description: List follow-ups (newest first). Admin view.

Auth: JWT

Query Parameters:

- lead_id (int, optional): Filter by lead
- limit (int, default 100): Max results

Request:

GET /api/follow-ups
GET /api/follow-ups?lead_id=4
GET /api/follow-ups?limit=50

Response (200): Array of follow-up objects.

---

## n8n Integration Endpoints

### POST /api/webhooks/n8n

Description: Receive events from n8n workflows.

Auth: X-API-Key

Supported Events: ping, email_sent, email_failed, lead_status_changed

### Event: ping

Request:

{
  "event": "ping"
}

Response (200):

{
  "status": "ok",
  "event": "ping"
}

### Event: email_sent

Request:

{
  "event": "email_sent",
  "email_log_id": 2
}

Response (200):

{
  "status": "ok",
  "event": "email_sent",
  "email_log_id": 2
}

Side Effects:

- email_log.status becomes sent
- lead.last_contacted_at updated
- lead.status becomes contacted if was new

### Event: email_failed

Request:

{
  "event": "email_failed",
  "email_log_id": 2,
  "message": "SMTP timeout"
}

Response (200):

{
  "status": "ok",
  "event": "email_failed",
  "email_log_id": 2
}

Side Effects:

- email_log.status becomes failed
- Notification created with error message

### Event: lead_status_changed

Request:

{
  "event": "lead_status_changed",
  "lead_id": 3,
  "status": "converted"
}

Response (200):

{
  "status": "ok",
  "event": "lead_status_changed",
  "lead_id": 3,
  "new_status": "converted"
}

Side Effect: If status becomes converted, auto-create customer.

Error Responses:

Code 400 - Missing required fields
Body: {"detail": "email_log_id is required"}

Code 401 - Wrong/missing key
Body: {"detail": "Invalid or missing n8n API key."}

Code 404 - Lead/log not found
Body: {"detail": "Lead not found"}

Code 422 - Invalid event type
Body: {"detail": "Validation failed", "errors": [...]}

---

### POST /api/executions/log

Description: Store n8n workflow execution record (idempotent).

Auth: X-API-Key

Request:

POST /api/executions/log
X-API-Key: your-key
Content-Type: application/json

{
  "execution_id": "n8n-exec-2026-11-16-001",
  "workflow_name": "SmartBiz AI - Notification Workflow",
  "workflow_id": "workflow-123",
  "status": "success",
  "started_at": "2026-11-16T12:30:00Z",
  "finished_at": "2026-11-16T12:30:05Z"
}

Fields:

- execution_id (string, required): Unique (idempotency key)
- workflow_name (string, required)
- workflow_id (string, optional): n8n workflow identifier
- status (string, required): success or error
- started_at (datetime, optional): ISO 8601
- finished_at (datetime, optional): ISO 8601
- error_message (string, optional): Execution error details

Response (201 Created):

{
  "id": 1,
  "execution_id": "n8n-exec-2026-11-16-001",
  "workflow_name": "SmartBiz AI - Notification Workflow",
  "workflow_id": "workflow-123",
  "status": "success",
  "started_at": "2026-11-16T12:30:00+06:00",
  "finished_at": "2026-11-16T12:30:05+06:00",
  "error_message": null,
  "created_at": "2026-11-16T18:30:10+06:00"
}

Idempotency: If execution_id already exists, the existing record is updated instead of creating a duplicate. The endpoint uses HTTP 201 for POST responses.

---

### GET /api/integrations/n8n/health

Description: Check whether n8n Cloud is reachable.

Auth: JWT

Request:

GET /api/integrations/n8n/health

Response (200):

{
  "status": "connected",
  "message": "n8n Cloud is reachable."
}

Or:

{
  "status": "unreachable",
  "message": "n8n Cloud is not responding."
}

---

### GET /api/workflows/executions

Description: Get the latest 50 execution logs (admin view).

Auth: JWT

Response (200):

[
  {
    "id": "n8n-exec-2026-11-16-001",
    "workflow_name": "SmartBiz AI - Notification Workflow",
    "status": "success",
    "workflow_id": "workflow-123",
    "started_at": "2026-11-16T12:30:00+06:00",
    "finished_at": "2026-11-16T12:30:05+06:00",
    "duration_ms": 5000,
    "error_message": null
  }
]

---

### GET /api/workflows

Description: List n8n workflows (static metadata).

Auth: JWT

Response (200): Array of workflow metadata objects.

---

## Error Codes Reference

### Standard Error Responses

All errors return JSON:

{
  "detail": "Error message"
}

Validation errors (422) have extended format:

{
  "detail": "Validation failed",
  "errors": [
    {
      "field": "email",
      "message": "value is not a valid email address"
    }
  ]
}

### HTTP Status Codes

Code 200 - OK (Successful GET/PATCH/PUT)
Code 201 - Created (Successful POST)
Code 204 - No Content (Successful DELETE)
Code 400 - Bad Request (Missing required fields)
Code 401 - Unauthorized (Missing/invalid JWT or API key)
Code 404 - Not Found (Resource doesn't exist)
Code 409 - Conflict (Duplicate email, duplicate follow-up)
Code 422 - Unprocessable Entity (Validation failed)
Code 500 - Internal Server Error (AI module failed, DB error)
Code 503 - Service Unavailable (N8N_API_KEY not configured)

---

## Data Models

### Lead

{
  "id": 1,
  "name": "Rahim Ahmed",
  "email": "rahim@example.com",
  "phone": "+8801712345678",
  "company": "ABC Technologies",
  "message": "Interested in AI CRM",
  "source": "website",
  "interest": "AI Automation",
  "value": 5000.0,
  "status": "new",
  "last_contacted_at": null,
  "created_at": "2026-11-16T09:53:50+06:00"
}

Status values: new, contacted, qualified, converted, lost
Source values: manual, website, facebook, google_forms, linkedin, referral, email, other

### Customer

{
  "id": 1,
  "name": "Fatima Khan",
  "email": "fatima@example.com",
  "phone": "+8801812345678",
  "company": "Khan Fashion",
  "total_deals": 1,
  "created_at": "2026-11-16T11:26:33+06:00"
}

### Follow-up

{
  "id": 1,
  "lead_id": 4,
  "channel": "email",
  "status": "sent",
  "note": null,
  "message": "Day-3 follow-up sent",
  "created_at": "2026-11-16T11:42:31+06:00"
}

### Email Log

{
  "id": 2,
  "lead_id": 4,
  "to_email": "karim@example.com",
  "subject": "SmartBiz AI welcome",
  "body": "Dear Karim Hossain,...",
  "generated_by": "ai",
  "status": "sent",
  "created_at": "2026-11-16T12:04:55+06:00"
}

### Report

{
  "id": 1,
  "report_type": "ai_report",
  "title": "SmartBiz AI business report",
  "summary": "...",
  "insights": ["..."],
  "recommendations": ["..."],
  "created_at": "2026-11-16T12:07:11+06:00"
}

### Notification

{
  "id": 12,
  "message": "Follow-up (email) failed for Karim Hossain",
  "is_read": "false",
  "created_at": "2026-11-16T11:49:56+06:00"
}

### Execution Log

{
  "id": 1,
  "execution_id": "n8n-exec-2026-11-16-001",
  "workflow_name": "SmartBiz AI - Notification Workflow",
  "workflow_id": "workflow-123",
  "status": "success",
  "started_at": "2026-11-16T12:30:00+06:00",
  "finished_at": "2026-11-16T12:30:05+06:00",
  "error_message": null,
  "created_at": "2026-11-16T18:30:10+06:00"
}

---

## Endpoint Summary Table

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | / | None | Root |
| GET | /health | None | Health check |
| POST | /api/auth/login | None | Admin login |
| POST | /api/leads | None | Create lead (public) |
| GET | /api/leads | JWT | List/filter/search leads |
| GET | /api/leads/{id} | JWT | Get lead |
| PUT | /api/leads/{id} | JWT | Update lead |
| PATCH | /api/leads/{id}/status | JWT | Update status |
| DELETE | /api/leads/{id} | JWT | Delete lead |
| POST | /api/customers | JWT | Create customer |
| GET | /api/customers | JWT | List customers |
| GET | /api/dashboard/stats | JWT | Dashboard stats |
| POST | /api/reports | JWT | Create report |
| GET | /api/reports | JWT | List reports |
| POST | /api/reports/generate | JWT | AI report |
| POST | /api/notifications | X-API-Key | Create notification from n8n |
| GET | /api/notifications | JWT | List notifs |
| PATCH | /api/notifications/read-all | JWT | Mark all read |
| PATCH | /api/notifications/{id}/read | JWT | Mark one read |
| GET | /email-logs | JWT | List email logs |
| PATCH | /email-logs/{id}/status | JWT | Update log status |
| POST | /automation/welcome-email/{id} | JWT | AI welcome email |
| GET | /api/follow-ups/due | X-API-Key | Due follow-ups |
| POST | /api/follow-ups | X-API-Key | Log follow-up |
| GET | /api/follow-ups | JWT | List follow-ups |
| POST | /api/webhooks/n8n | X-API-Key | n8n webhook |
| POST | /api/executions/log | X-API-Key | Log execution |
| GET | /api/integrations/n8n/health | JWT | n8n health |
| GET | /api/workflows/executions | JWT | Execution logs |
| GET | /api/workflows | JWT | Workflow list |

---

## Quick cURL Examples

### Login

curl -X POST http://127.0.0.1:8000/api/auth/login   -H "Content-Type: application/json"   -d '{"email": "admin@smartbiz.ai", "password": "admin123"}'

### Create lead (public)

curl -X POST http://127.0.0.1:8000/api/leads   -H "Content-Type: application/json"   -d '{"name": "Test", "email": "test@example.com"}'

### List leads (JWT)

curl -X GET http://127.0.0.1:8000/api/leads   -H "Authorization: Bearer TOKEN"

### n8n ping

curl -X POST http://127.0.0.1:8000/api/webhooks/n8n   -H "X-API-Key: your-key"   -H "Content-Type: application/json"   -d '{"event": "ping"}'

### Generate AI report

curl -X POST http://127.0.0.1:8000/api/reports/generate   -H "Authorization: Bearer TOKEN"

---

**End of API Reference**

For setup/run instructions, see README.md
For test evidence, see TEST_RESULTS.md
For demo guide, see DEMO_SCRIPT.md
