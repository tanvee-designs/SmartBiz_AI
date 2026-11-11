import os
import requests

# n8n Webhook URL এনভায়রনমেন্ট ভ্যারিয়েবল থেকে নেবে
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")

def send_lead_to_n8n(lead):
    """n8n-এ নতুন লিডের ডেটা পাঠায়।"""
    if not N8N_WEBHOOK_URL:
        print("N8N_WEBHOOK_URL is not set. Skipping n8n.")
        return

    try:
        # SQLAlchemy অবজেক্টকে JSON সিরিয়ালাইজেবল ডিকশনারিতে কনভার্ট করা
        lead_data = {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "company": lead.company,
            "interest": lead.interest,
            "value": lead.value,
            "status": lead.status,
        }

        # n8n-এ POST রিকোয়েস্ট পাঠানো
        response = requests.post(
            N8N_WEBHOOK_URL, 
            json=lead_data, 
            headers={"ngrok-skip-browser-warning": "true"}, 
            timeout=10
        )
        response.raise_for_status()
        print(f"Successfully sent lead {lead.id} to n8n.")
        
    except Exception as e:
        print(f"Could not send lead to n8n: {e}")