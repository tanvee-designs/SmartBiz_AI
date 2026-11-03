# SmartBiz AI — Business Automation System

## 🚀 Project Overview
SmartBiz AI is an AI-powered business automation system that collects leads, automates emails, updates Google Sheets, and generates AI reports using n8n and Gemini API.

## 🛠️ Tech Stack
- **Backend:** Python (FastAPI, SQLAlchemy, SQLite)
- **Frontend:** HTML, CSS, JavaScript
- **Automation:** n8n
- **AI:** Gemini API (Python)
- **Database:** SQLite

## 📁 Folder Structure
- `backend/` — FastAPI code & Database models
- `frontend/` — Web Dashboard & Lead Form
- `n8n/` — n8n workflow JSON files
- `ai_module/` — AI Report generation logic
- `docs/` — Project architecture, API contracts, Testing plans

## 🏃‍♂️ How to Run Locally
1. **Backend:** 
   ```bash
   cd backend
   python -m venv myenv
   .\myenv\Scripts\activate
   pip install fastapi uvicorn sqlalchemy
   uvicorn main:app --reload