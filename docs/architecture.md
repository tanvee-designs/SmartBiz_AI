# SmartBiz AI — System Architecture & Database Schema

## 1. Database Schema (SQLite)

### Table 1: `leads`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| name | TEXT | NOT NULL | Lead Name |
| email | TEXT | NOT NULL UNIQUE | Email |
| phone | TEXT | NULLABLE | Phone |
| company | TEXT | NULLABLE | Company |
| source | TEXT | DEFAULT 'website' | Source |
| status | TEXT | DEFAULT 'new' | Status |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Created At |

### Table 2: `customers`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| lead_id | INTEGER | FOREIGN KEY (leads.id) | Lead ID |
| name | TEXT | NOT NULL | Customer Name |
| email | TEXT | NOT NULL UNIQUE | Email |
| phone | TEXT | NULLABLE | Phone |
| status | TEXT | DEFAULT 'active' | Status |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Created At |

### Table 3: `email_logs`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| lead_id | INTEGER | FOREIGN KEY (leads.id) | Lead ID |
| email_type | TEXT | NOT NULL | Email Type |
| subject | TEXT | NOT NULL | Subject |
| status | TEXT | DEFAULT 'sent' | Status |
| sent_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Sent At |
| error_message| TEXT | NULLABLE | Error Message |

### Table 4: `reports`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| report_type | TEXT | NOT NULL | Report Type |
| title | TEXT | NOT NULL | Title |
| content | TEXT | NOT NULL | Content |
| generated_at| DATETIME | DEFAULT CURRENT_TIMESTAMP | Generated At |

### Table 5: `notifications`
| Column | Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| user_id | TEXT | DEFAULT 'admin' | User ID |
| title | TEXT | NOT NULL | Title |
| message | TEXT | NOT NULL | Message |
| type | TEXT | DEFAULT 'info' | Type |
| is_read | BOOLEAN | DEFAULT 0 | Read Status |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Created At |

---

## 2. System Architecture Diagram (High Level)

```mermaid
graph TD
    User([User / Client]) -->|Fills Form| Frontend(Web Dashboard / HTML & JS)
    Frontend -->|POST /api/leads| Backend(FastAPI Backend)
    Backend -->|Save Data| DB[(SQLite Database)]
    
    Backend -->|Trigger Webhook| n8n(n8n Automation Engine)
    n8n -->|Gmail API| Email[Automated Welcome Email]
    n8n -->|Google Sheets API| Sheets[Google Sheets Database]
    
    Backend -->|Request AI Report| AI(AI Module / Python + Gemini)
    AI -->|Fetch Data| DB
    AI -->|Generate Insight| Backend
    Backend -->|Show Notification| Frontend