# SmartBiz AI — Business Automation System

SmartBiz AI is a business automation system for digital marketing agencies and small and medium businesses (SMEs). It cuts down manual work by collecting customer leads, sending automated emails and generating AI-powered reports.

## Problem

Businesses receive many leads every day, but tracking them by hand, sending follow-up emails and building reports takes a lot of time. SmartBiz AI automates the whole process.

## Key Features

1. **Lead collection:** capture new customer data through a web form.
2. **Automated email:** send an email automatically as soon as a new lead arrives (via n8n).
3. **Google Sheets sync:** save every lead to a Google Sheet automatically.
4. **AI reports:** analyse lead data with the Gemini API and generate insights and recommendations.
5. **Notification system:** show notifications on the dashboard.

## How It Works

```
Lead form (frontend)
        │
        ▼
FastAPI backend ──► SQLite database
        │
        ├──► n8n webhook ──► Gmail (automated email)
        │                └──► Google Sheets (lead sync)
        │
        └──► AI module (Gemini API) ──► AI report ──► Dashboard
```

## Technology Stack

| Layer      | Technology                                   |
| ---------- | -------------------------------------------- |
| Backend    | Python, FastAPI, SQLAlchemy                  |
| Database   | SQLite                                       |
| Frontend   | HTML, CSS, JavaScript (responsive dashboard) |
| Automation | n8n (Webhook, Gmail, Google Sheets)          |
| AI         | Google Gemini API (Python)                   |

## Project Structure

```
SmartBiz_AI/
├── backend/      # FastAPI code, database models and API endpoints
├── frontend/     # Dashboard and lead collection form (HTML/CSS/JS)
├── n8n/          # n8n workflow JSON files
├── ai_module/    # Gemini API integration scripts
├── docs/         # Architecture, API contract and testing plan
├── .env.example  # Template for environment variables
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.10 or newer
- Node.js 18+ (to run n8n locally) or Docker
- A Google Gemini API key
- A Google account for Gmail and Google Sheets (used by n8n)

### 1. Clone the repository

```bash
git clone https://github.com/tanvee-designs/SmartBiz_AI.git
cd SmartBiz_AI
```

### 2. Configure environment variables

Copy the example file and fill in your own values. Never commit the real `.env` file.

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Open `.env` and set the values listed in `.env.example` (for example your Gemini API key and the n8n webhook URL).

### 3. Run the backend

```bash
cd backend
python -m venv myenv
source myenv/bin/activate    # Windows: .\myenv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`, and interactive API docs are at `http://127.0.0.1:8000/docs`.

### 4. Run the frontend

The frontend is plain HTML, CSS and JavaScript, so no build step is needed. Serve the `frontend/` folder with any static server:

```bash
cd frontend
python -m http.server 5500
```

Then open `http://localhost:5500` in your browser. Make sure the API base URL in the frontend code points to your running backend.

### 5. Set up n8n

1. Start n8n:
   ```bash
   npx n8n
   ```
   or with Docker:
   ```bash
   docker run -it --rm -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n
   ```
2. Open `http://localhost:5678` and create an account.
3. Go to **Workflows → Import from file** and import the workflow JSON files from the `n8n/` folder, plus `SmartBiz AI - Notification Workflow.json` in the repository root.
4. Create your own credentials in n8n for **Gmail** and **Google Sheets**, then select them in the relevant nodes.
5. Open the **Webhook** node, copy its URL and put it in your `.env` file so the backend can call it.
6. Set the target Google Sheet in the Google Sheets node, then **activate** the workflow.

### 6. Try it out

1. Open the lead form in the frontend and submit a test lead.
2. Check that the lead appears in the dashboard and in your Google Sheet.
3. Check that the automated email arrives.
4. Generate an AI report from the dashboard.

## Documentation

See the [`docs/`](docs/) folder for the architecture, API contract and testing plan.

## Security Notes

- Keep API keys and credentials in `.env` or in n8n credentials only, never in code or workflow JSON files.
- Before sharing exported n8n workflows, check them for real email addresses, webhook URLs and credential IDs.

## License

See the [LICENSE](LICENSE) file.

## Authors

SmartBiz AI was built by a team. Add names and GitHub profiles here.