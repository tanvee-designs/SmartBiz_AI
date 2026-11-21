
import os
import requests

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")


def send_lead_to_n8n(lead):
    """Send a new lead to the existing n8n Lead Automation webhook."""

    if not N8N_WEBHOOK_URL:
        print("N8N_WEBHOOK_URL is not set. Skipping n8n.")
        return

    try:
        lead_data = {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company,
            "interest": lead.interest,
            "value": lead.value,
            "status": lead.status,
            "source": lead.source,
            "message": lead.message,
            "event_origin": "backend",
        }

        response = requests.post(
            N8N_WEBHOOK_URL,
            json=lead_data,
            headers={
                "Content-Type": "application/json",
                "ngrok-skip-browser-warning": "true",
            },
            timeout=10,
        )

        response.raise_for_status()

        print(f"Successfully sent lead {lead.id} to n8n.")

    except requests.RequestException as exc:
        print(f"Could not send lead to n8n: {exc}")

    except Exception as exc:
        print(f"Unexpected n8n integration error: {exc}")
