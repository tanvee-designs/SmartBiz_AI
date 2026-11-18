# SmartBiz_AI Backend

FastAPI-based CRM backend for SmartBiz_AI — an AI-powered lead automation platform.

**Status:** Integration Verification Pending | **Historical Baseline Tests:** 57/57 passed on 2026-11-16 | **Version:** 1.0.0

---

## Overview

SmartBiz_AI Backend is a RESTful API that powers the SmartBiz_AI CRM platform. It handles lead collection, customer management, AI-generated emails and reports, follow-up automation, and integrates with n8n for workflow orchestration.

**Key Highlights:**

- AI-powered Bangla email generation (Gemini API)
- AI-powered business analytics reports (Bangla)
- n8n workflow integration (webhook + events)
- Dual authentication (JWT + API Key)
- Dashboard statistics
- Auto-generated notifications
- BST timezone consistency (+06:00)

> **Verification note:** The 57/57 test result is a historical baseline recorded on 2026-11-16. It does not mean the latest deployed end-to-end integration has been re-tested. Complete current n8n production integration verification before describing the deployment as fully verified.

---

## Features

### Lead Management

- Create leads from public website/forms endpoints
- Duplicate email detection: an existing email is rejected with HTTP 409 Conflict; no duplicate lead is created
- Filter by status/source and search by name/email/company
- Update, delete, and change lead status
- Automatically create or update a customer when a lead is converted

### n8n Integration

- Webhook authentication via `X-API-Key`
- Event types: `ping`, `email_sent`, `email_failed`, `lead_status_changed`
- Due follow-up listing
- Follow-up logging with duplicate prevention
- Idempotent execution logging

### AI Modules

- **Welcome Email:** Gemini-powered, Bangla language, HTML rendering, personalized
- **Business Report:** Data-driven insights and recommendations in Bangla

### Follow-up Automation

- 3-day due detection
- Automatic status transition (`new` to `contacted`) when a follow-up is recorded as sent
- Duplicate sent-follow-up prevention (HTTP 409 within 3 days)
- Converted/lost leads are excluded from due follow-ups

### Dashboard & Analytics

- Total leads, customers, and pipeline value
- Conversion rate calculation
- Lead breakdown by status and source
- Unread notification count

### Notifications

- Auto-generated on key events
- Read marking (single and bulk)
- Unread notification tracking
- n8n can create notifications using `X-API-Key`; dashboard notification reads/updates use JWT

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI |
| Language | Python |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Database | SQLite (development) / PostgreSQL (production recommended) |
| Auth | JWT + API Key |
| AI | Google Gemini API |
| HTTP Client | httpx + requests |
| Server | Uvicorn |

---

## Quick Start

### 1. Clone Repository

```powershell
git clone <your-repository-url>
cd SmartBiz_AI/backend
```

### 2. Create Virtual Environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment

Create a `.env` file based on `.env.example` and set the required values. Do not commit `.env` or share secret values.

```env
DATABASE_URL=sqlite:///./SmartBiz_AI.db
JWT_SECRET_KEY=<your-random-secret>
ADMIN_EMAIL=<your-admin-email>
ADMIN_PASSWORD_HASH=<your-password-hash>
GEMINI_API_KEY=<your-gemini-api-key>
N8N_API_KEY=<shared-secret-matching-n8n-credential>
N8N_BASE_URL=https://<your-n8n-instance>.app.n8n.cloud
COMPANY_NAME=SmartBiz AI
COMPANY_SERVICES=AI-powered lead automation
SENDER_NAME=SmartBiz AI Team
EMAIL_LANGUAGE=Bangla
```

Use the actual variable names and configuration expected by your deployment. Never paste API keys, passwords, or hashes into documentation or source control.

### 5. Run Server

From the `backend` directory:

```powershell
uvicorn main:app --reload
```

Local server: `http://127.0.0.1:8000`

### 6. Verify

```powershell
curl http://127.0.0.1:8000/health
```

Open API docs: `http://127.0.0.1:8000/docs`

---

## Deployment

**Deployed backend:** https://smartbiz-ai-backend-8b8k.onrender.com

**Frontend:** https://smartbiz-automation-official.netlify.app

Render start command:

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

Configure environment variables in the Render service dashboard. Keep production secrets out of Git and documentation. PostgreSQL is recommended for persistent production data; SQLite on an ephemeral hosting filesystem may not provide durable storage.

After deployment, verify the health endpoint and protected API routes using the appropriate credentials. End-to-end n8n workflow verification is a separate step.

---

## Authentication

### Admin Users (JWT)

1. Send admin credentials to `POST /api/auth/login`.
2. Use the returned access token on protected admin endpoints:

```http
Authorization: Bearer <access-token>
```

The token lifetime is determined by the backend configuration.

### n8n Workflows (API Key)

Send the shared key in this header for API-key-protected endpoints:

```http
X-API-Key: <shared-secret>
```

The key configured in Render as `N8N_API_KEY` must match the Header Auth credential configured in n8n. Do not disclose the key.

### Endpoint Authentication Summary

| Endpoint | Authentication |
|----------|----------------|
| `POST /api/leads` | Public |
| `GET /health` | Public |
| `POST /api/auth/login` | Public |
| `GET /api/leads` | JWT |
| `POST /api/notifications` | `X-API-Key` |
| `GET /api/notifications` | JWT |
| `PATCH /api/notifications/{notification_id}/read` | JWT |
| `GET /api/follow-ups/due` | `X-API-Key` |
| `POST /api/follow-ups` | `X-API-Key` |
| `POST /api/webhooks/n8n` | `X-API-Key` |
| `POST /api/executions/log` | `X-API-Key` |
| Other admin dashboard endpoints | JWT, unless documented otherwise |

See [API_REFERENCE.md](API_REFERENCE.md) for the complete endpoint list and request/response details.

---

## Project Structure

```text
backend/
├── main.py
├── models.py
├── schemas.py
├── database.py
├── auth.py
├── generate_email.py
├── generate_report.py
├── n8n_client.py
├── requirements.txt
├── .env.example
├── README.md
├── API_REFERENCE.md
├── TEST_RESULTS.md
└── DEMO_SCRIPT.md
```

Actual files may vary as the project evolves. Keep `.env`, database files containing real data, and other secrets/private artifacts out of public commits.

---

## Database Schema

The backend uses tables for the main CRM resources, including:

- `leads`
- `customers`
- `follow_ups`
- `email_logs`
- `reports`
- `notifications`
- `execution_logs`

Tables are initialized by the application's database setup. Use migrations for controlled schema changes in production.

---

## API Documentation

- Swagger UI (local): `http://127.0.0.1:8000/docs`
- ReDoc (local): `http://127.0.0.1:8000/redoc`
- OpenAPI JSON (local): `http://127.0.0.1:8000/openapi.json`

See [API_REFERENCE.md](API_REFERENCE.md).

---

## Testing

**Historical baseline:** 57/57 tests passed on 2026-11-16, as recorded in `TEST_RESULTS.md`.

This is a dated test result, not a guarantee that every current code change or deployed integration has been re-tested. Run the relevant test suite against the current code before reporting a new pass count. In particular, verify the production n8n workflow callbacks after the latest backend deployment.

### Historical Test Coverage (2026-11-16)

| Phase | Tests | Historical Result |
|-------|-------|-------------------|
| Health + Auth | 5 | Passed |
| Leads CRUD | 17 | Passed |
| n8n Integration | 10 | Passed |
| Follow-ups | 10 | Passed |
| AI Modules | 6 | Passed |
| Dashboard | 3 | Passed |
| Notifications | 5 | Passed |
| Timezone Fix | 1 | Passed |
| **Total** | **57** | **Passed on 2026-11-16** |

---

## Implemented Features

The backend includes the following implemented capabilities; current production integration status must be verified independently:

1. AI Bangla email generation
2. AI Bangla business reports
3. Customer creation/update on lead conversion
4. Authenticated n8n event callbacks
5. Dashboard statistics
6. System notifications
7. Duplicate lead rejection with HTTP 409
8. Structured API error responses
9. BST timezone handling (+06:00)
10. JWT and API-key authentication

---

## Known Limitations / Verification Items

| Item | Notes |
|------|-------|
| Production database | PostgreSQL is recommended for persistent production storage |
| Admin roles | Current authentication may be limited to a single admin configuration |
| Follow-up interval | Current automatic due detection uses a 3-day rule |
| Rate limiting | Add rate limiting before exposing public endpoints broadly |
| Email retry | Add retry/backoff handling if required |
| Token renewal | Add refresh-token flow if required |
| Pagination | Add pagination for growing datasets |
| n8n end-to-end status | Verify lead trigger, execution logging, and notification callback using a controlled test lead |

---

## Troubleshooting

### Server Will Not Start

```powershell
python --version
pip install -r requirements.txt
```

Check that the virtual environment is active and required environment variables are configured.

### Login Fails (401)

- Check that `JWT_SECRET_KEY` is configured.
- Check that the admin email and password configuration match the backend setup.
- Restart the service after changing environment variables.

### n8n Callback Fails (401 or 503)

- Confirm the request includes the `X-API-Key` header.
- Confirm Render's `N8N_API_KEY` matches the n8n Header Auth credential.
- Confirm `N8N_API_KEY` is configured in Render.
- Never paste the key into chat or commit it to Git.

### Database Issues

Back up the database before performing any database maintenance. Do not delete a production database as a troubleshooting shortcut.

---

## Team Responsibilities

| Role | Responsibility |
|------|----------------|
| Member 04 | Backend development |
| n8n Engineer | Workflow automation |
| Frontend Developer | UI integration |
| AI/ML Engineer | AI module development |
| Project Lead | Coordination |

---

## License

Internal project — SmartBiz_AI Team.

---

## Acknowledgments

- FastAPI team
- Google Gemini
- n8n team
- SmartBiz_AI team members

---

**Version:** 1.0.0

**Last Updated:** 2026-11-18

**Status:** Integration Verification Pending
