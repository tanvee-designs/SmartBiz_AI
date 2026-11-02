# SmartBiz AI — API Contract

এই ফাইলটি Backend (FastAPI) এবং Frontend (Web Dashboard) এর মধ্যে যোগাযোগের নিয়ম নির্ধারণ করে।

## 1. Base URL
- Local Development: `http://127.0.0.1:8000`

## 2. Endpoints (Backend API)

### 2.1 Create Lead (নতুন লিড তৈরি)
- **Method:** `POST`
- **URL:** `/api/leads`
- **Request Body (JSON):**
  ```json
  {
    "name": "Rahim Uddin",
    "email": "rahim@example.com",
    "phone": "01712345678",
    "company": "Rahim Enterprise"
  }