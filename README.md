# SmartBiz AI — Business Automation System

## 📌 Project Overview
SmartBiz AI হলো একটি **Business Automation System**, যা ডিজিটাল মার্কেটিং এজেন্সি এবং SME-দের জন্য ডিজাইন করা হয়েছে। এটি ম্যানুয়াল কাজ কমিয়ে এনে কাস্টমার লিড কালেকশন, অটোমেটেড ইমেইল এবং AI-জেনারেটেড রিপোর্ট প্রদান করে।

## 🎯 Problem Statement
ব্যবসাগুলো প্রতিদিন প্রচুর লিড পায়, কিন্তু ম্যানুয়ালি সেগুলো ট্র্যাক করা, ইমেইল পাঠানো এবং রিপোর্ট বানানো খুবই সময়সাপেক্ষ। SmartBiz AI এই পুরো প্রক্রিয়াটি অটোমেট করে।

## 🛠️ Technology Stack
- **Backend:** Python (FastAPI, SQLAlchemy, SQLite)
- **Frontend:** HTML, CSS, JavaScript (Responsive Dashboard)
- **Automation:** n8n (Webhook, Gmail, Google Sheets)
- **AI:** Gemini API (Python)
- **Database:** SQLite

## 🚀 Key Features
1. **Lead Collection:** ফর্মের মাধ্যমে নতুন কাস্টমার ডেটা কালেক্ট করা।
2. **Automated Email:** নতুন লিড আসার সাথে সাথে স্বয়ংক্রিয় ইমেইল পাঠানো (n8n)।
3. **Google Sheets Sync:** লিড ডেটা গুগল শিটে অটোমেটিক্যালি সেভ হওয়া।
4. **AI Reports:** Gemini API দিয়ে লিড ডেটা অ্যানালাইসিস করে ইনসাইট ও সুপারিশ জেনারেট করা।
5. **Notification System:** ড্যাশবোর্ডে নোটিফিকেশন দেখানো।

## 📂 Folder Structure
- `backend/` — FastAPI কোড, ডাটাবেস মডেল এবং API এন্ডপয়েন্ট।
- `frontend/` — ড্যাশবোর্ড এবং লিড কালেকশন ফর্ম (HTML/CSS/JS)।
- `n8n/` — n8n ওয়ার্কফ্লো JSON ফাইল।
- `ai_module/` — Gemini API ইন্টিগ্রেশন স্ক্রিপ্ট।
- `docs/` — আর্কিটেকচার, API কন্ট্রাক্ট এবং টেস্টিং প্ল্যান।

## 🏃‍♂️ How to Run Locally
1. **Backend:**
   ```bash
   cd backend
   python -m venv myenv
   .\myenv\Scripts\activate  # Windows
   pip install -r requirements.txt
   uvicorn main:app --reload