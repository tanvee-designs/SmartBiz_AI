# SmartBiz_AI — API Contract

এই ফাইলটি Backend (FastAPI) এবং Frontend (Web Dashboard) ও n8n-এর মধ্যে যোগাযোগের নিয়ম নির্ধারণ করে। কোনো endpoint বদলালে আগে এই ফাইল হালনাগাদ করে টিমকে জানাতে হবে।

## 1. Base URL
- Local Development: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`
- Each member runs the backend on their own computer. `127.0.0.1` works only on that computer. For n8n or other computers, use a public tunnel URL (see section 4).

## 2. Endpoints (Backend API)

### 2.1 Create Lead (নতুন লিড তৈরি)
- **Method:** `POST`
- **URL:** `/api/leads`
- **Header:** `Content-Type: application/json`

**Request Body (JSON):**
```json
{
  "name": "Rahim Uddin",
  "email": "rahim@example.com",
  "phone": "01712345678",
  "company": "Rahim Enterprise",
  "source": "facebook",
  "interest": "CRM software",
  "value": 15000
}
```

**Field rules:**

| Field | Required | Rule |
|---|---|---|
| name | Yes | 2 to 100 characters |
| email | Yes | Must be a valid email address |
| phone | No | Up to 30 characters |
| company | No | Up to 150 characters |
| message | No | Free text |
| source | No | One of `website`, `facebook`, `google_forms`, `linkedin`, `referral`, `email`, `other`. Default `website`. Any other value returns 422 |
| interest | No | Text, up to 200 characters |
| value | No | Deal value, a number of 0 or more. Default 0 |

**Notes:**
- Email is saved in lowercase. `Rahim@Example.com` and `rahim@example.com` count as the same email.
- After a lead is saved, the backend automatically sends it to the n8n webhook (section 3).

**Success Response (201 Created):**
```json
{
  "id": 1,
  "name": "Rahim Uddin",
  "email": "rahim@example.com",
  "phone": "01712345678",
  "company": "Rahim Enterprise",
  "message": null,
  "source": "facebook",
  "interest": "CRM software",
  "value": 15000.0,
  "status": "new",
  "created_at": "2026-11-05T06:14:06.638273"
}
```

**Error Responses:**

| Code | When | Body |
|---|---|---|
| 409 Conflict | Email already exists | `{"detail": "Lead with this email already exists"}` |
| 422 Unprocessable Content | Invalid data (email without @, unknown source, name too short) | FastAPI validation error with the field name and reason |

**Frontend should show:**
- 201: "Thank you, your request was received"
- 409: "This email is already registered"
- 422: ask the user to correct the form fields

### 2.2 List Leads (সব লিডের তালিকা)
- **Method:** `GET`
- **URL:** `/api/leads`
- **Optional query:** `status` (for example `/api/leads?status=new` returns only leads with that status)
- **Order:** newest lead first
- **Request Body:** none
- **Success (200):** a list of leads, same shape as the 201 response in 2.1. An empty list `[]` when nothing matches.

**Frontend tip:** show `created_at` as a readable date. Show `message` and `interest` only when they are not `null`.

### 2.3 Update Lead Status (লিডের স্ট্যাটাস বদল)
- **Method:** `PATCH`
- **URL:** `/api/leads/{id}`
- **Request Body:** `{"status": "contacted"}`
- **Allowed status values:** `new`, `contacted`, `qualified`, `converted`, `lost`
- **Success (200):** the updated lead (same shape as 2.1)
- **Errors:** 404 `{"detail": "Lead not found"}`, 422 for any other status value

### 2.4 Customers (কাস্টমার)
**Create:** `POST /api/customers`
```json
{
  "name": "Rahim Uddin",
  "email": "rahim@example.com",
  "phone": "01712345678",
  "company": "Rahim Enterprise",
  "total_deals": 0
}
```
- Required: `name` (2 to 100 characters), `email`. Optional: `phone`, `company`, `total_deals` (whole number, 0 or more, default 0).
- **Success (201):** the saved customer with `id` and `created_at`.
- **Errors:** 409 `{"detail": "Customer with this email already exists"}`, 422 for invalid data.

**List:** `GET /api/customers` returns a list of customers, newest first.

### 2.5 Reports (রিপোর্ট)
**Create:** `POST /api/reports`
```json
{
  "title": "Weekly Lead Performance",
  "summary": "Short summary paragraph.",
  "insights": ["Insight one", "Insight two"],
  "recommendations": ["Do this", "Do that"],
  "report_type": "performance"
}
```
- Required: `title` (2 to 200 characters), `summary` (not empty).
- Optional: `insights` and `recommendations` (lists of strings, default empty), `report_type` (default `ai_report`).
- The old `content` field no longer exists.
- **Success (201):**
```json
{
  "id": 1,
  "report_type": "performance",
  "title": "Weekly Lead Performance",
  "summary": "Short summary paragraph.",
  "insights": ["Insight one", "Insight two"],
  "recommendations": ["Do this", "Do that"],
  "created_at": "2026-11-05T06:30:00.123456"
}
```
- **Errors:** 422 if `title` or `summary` is missing.

**List:** `GET /api/reports` returns reports, newest first. `insights` and `recommendations` come back as real lists.

### 2.6 Notifications (নোটিফিকেশন)
**Create:** `POST /api/notifications`
```json
{
  "message": "New lead received"
}
```
- Required: `message` (1 to 255 characters).
- **Success (201):** `{"id": 1, "message": "New lead received", "is_read": "false", "created_at": "..."}`
- **Note:** `is_read` is a TEXT value, either `"false"` or `"true"` (not a real boolean). In JavaScript compare it with `=== "true"`, because the text `"false"` also counts as true in an `if`.

**List:** `GET /api/notifications` returns notifications, newest first.

**Mark as read:** `PATCH /api/notifications/{id}/read` (no body) returns the notification with `is_read: "true"`. Error: 404 `{"detail": "Notification not found"}`.

### 2.7 Welcome Email (AI ওয়েলকাম ইমেইল)
- **Method:** `POST`
- **URL:** `/automation/welcome-email/{lead_id}` (no request body)
- **Success (200):**
```json
{
  "log_id": 3,
  "to": "rahim@example.com",
  "subject": "...",
  "body": "plain text version",
  "html": "<div>...</div>",
  "source": "ai"
}
```
- `source` is `ai` (written by Gemini) or `fallback` (default email if AI fails). Both always include `subject`, `body` and `html`.
- **Error:** 404 `{"detail": "Lead not found"}`
- **Timing:** can take up to about 60 seconds when the AI model is slow. Clients (n8n) must set a timeout of at least 90 seconds.

### 2.8 Email Logs (ইমেইল লগ)
- **Update status:** `PATCH /email-logs/{log_id}/status?status=sent`. The status goes in the URL query, not in a body. Allowed: `pending`, `sent`, `failed`. Success (200): the log. Errors: 404 `{"detail": "Log not found"}`, 422 for another value.
- **List:** `GET /email-logs` returns logs, newest first. Each log has `id`, `lead_id`, `to_email`, `subject`, `body`, `generated_by`, `status`, `created_at`.
- Lead status and email log status are separate. After an email is sent, n8n updates both: the log (`sent`, this section) and the lead (`contacted`, see 2.3).

### 2.9 Customer Follow-up (কাস্টমার ফলো-আপ)
- **Due list:** `GET /api/follow-ups/due?days=3`
  - Returns leads with status `contacted` whose last contact is `days` or more days old. Default `days` is 3.
  - Last contact = newest sent email log or sent follow-up, or the lead creation time if there is none.
  - Each item is a lead (same fields as 2.1) plus `last_contact_at` and `days_since_contact`. Oldest contact first.
  - n8n calls this once a day.
- **Record a follow-up:** `POST /api/follow-ups`
```json
{
  "lead_id": 1,
  "channel": "email",
  "note": "optional text",
  "status": "sent"
}
```
  - Only `lead_id` is required. `channel` defaults to `email`. `status` is `sent` (default) or `failed`.
  - **Success (201):** `{"id": 1, "lead_id": 1, "channel": "email", "note": null, "status": "sent", "created_at": "..."}`
  - **Errors:** 404 `{"detail": "Lead not found"}`; 409 `{"detail": "A follow-up was already sent to this lead recently"}` when a `sent` follow-up for the same lead already exists within the last 3 days (this prevents duplicate emails); 422 for invalid data.
- A recorded `sent` follow-up updates the lead's last contact time, so the lead leaves the due list. The lead status stays `contacted`. Change it to `qualified` only with `PATCH /api/leads/{id}` when the customer shows genuine interest.
- **List:** `GET /api/follow-ups` (optional `?lead_id=1`) returns follow-ups, newest first.

### 2.10 Health Check
- `GET /health` returns `{"status": "ok", "message": "Backend is healthy"}`.

## 3. n8n Integration

**Webhook payload (backend to n8n):** after a lead is saved (201), the backend sends the saved lead as JSON to the n8n Production Webhook (URL kept in `backend/.env` as `N8N_WEBHOOK_URL`):
```json
{
  "id": 1,
  "name": "Rahim Uddin",
  "email": "rahim@example.com",
  "phone": "01712345678",
  "company": "Rahim Enterprise",
  "message": null,
  "source": "facebook",
  "interest": "CRM software",
  "value": 15000.0,
  "status": "new",
  "created_at": "2026-11-05T06:14:06.638273"
}
```
If n8n is unreachable, the lead is still saved (nothing is lost). The backend only prints a message in its terminal.

**Welcome email flow (n8n calls the backend):**
1. `POST /automation/welcome-email/{id}` (timeout at least 90 seconds)
2. Gmail node: To `{{ $json.to }}`, Subject `{{ $json.subject }}`, HTML message `{{ $json.html }}`
3. On success: `PATCH /email-logs/{log_id}/status?status=sent`, then `PATCH /api/leads/{id}` with `{"status": "contacted"}`
4. On failure: `PATCH /email-logs/{log_id}/status?status=failed`

**Daily follow-up flow:**
1. `GET /api/follow-ups/due?days=3`
2. For each lead: send the follow-up email
3. On success: `POST /api/follow-ups` with `{"lead_id": ..., "status": "sent"}`. On failure: the same call with `"status": "failed"`.

## 4. General Rules
- **Format:** JSON for all request and response bodies. Dates are ISO 8601 text in UTC, for example `2026-11-05T06:14:06.638273`.
- **Errors:** error responses contain `detail`. A 422 `detail` is a list describing each invalid field.
- **Status values:** lead status `new`, `contacted`, `qualified`, `converted`, `lost`. Email log status `pending`, `sent`, `failed`. Follow-up status `sent`, `failed`.
- **Authentication:** none at the moment (local development only). An API key will be added before deployment and announced to the team.
- **Public URL:** `127.0.0.1` is not reachable from other computers. For n8n, Member 4 starts a temporary public tunnel for the backend and shares the URL. The URL changes whenever the tunnel restarts.
- **Database changes:** changing a table structure needs everyone to delete their local `backend/SmartBiz_AI.db` after pulling. Back up first.
- **Secrets:** never upload `.env` to GitHub. Copy `.env.example` to `backend/.env` and use your own values.