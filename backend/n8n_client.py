import os

import httpx
from dotenv import load_dotenv

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")


def send_lead_to_n8n(lead_data: dict) -> None:
    if not N8N_WEBHOOK_URL:
        print("N8N_WEBHOOK_URL is not set. Skipping n8n.")
        return

    try:
        response = httpx.post(N8N_WEBHOOK_URL, json=lead_data, timeout=10)
        response.raise_for_status()
        print("Lead sent to n8n successfully")
    except Exception as error:
        print(f"Could not send lead to n8n: {error}")