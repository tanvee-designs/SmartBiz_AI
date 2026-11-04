# SmartBiz_AI — API Contract

এই ফাইলটি Backend (FastAPI) এবং Frontend (Web Dashboard) এর মধ্যে যোগাযোগের নিয়ম নির্ধারণ করে।

## 1. Base URL
- Local Development: `http://127.0.0.1:8000`
- Interactive docs: `http://127.0.0.1:8000/docs`

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
  "company": "Rahim Enterprise"
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
| source | No | Defaults to `website` |

**Notes:**
- Email is saved in lowercase. `Rahim@Example.com` and `rahim@example.com` count as the same email.
- After a lead is saved, the backend automatically sends it to the n8n webhook.

**Success Response (201 Created):**
```json
{
  "id": 1,
  "name": "Rahim Uddin",
  "email": "rahim@example.com",
  "phone": "01712345678",
  "company": "Rahim Enterprise",
  "message": null,
  "source": "website",
  "status": "new",
  "created_at": "2026-11-03T07:04:50.046865"
}
```

**Error Responses:**

| Code | When | Body |
|---|---|---|
| 409 Conflict | Email already exists | `{"detail": "Lead with this email already exists"}` |
| 422 Unprocessable Content | Invalid data (for example an email without @) | FastAPI validation error with the field name and reason |

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

**Success Response (200 OK):** a list of leads (an empty list `[]` when nothing matches)
```json
[
  {
    "id": 5,
    "name": "Farhan Hasan",
    "email": "farhan@example.com",
    "phone": "01512345678",
    "company": "Farhan Tech",
    "message": null,
    "source": "website",
    "status": "new",
    "created_at": "2026-11-03T08:05:43.967356"
  }
]
```

**Frontend tip:** show `created_at` as a readable date, and show `message` only when it is not `null`.