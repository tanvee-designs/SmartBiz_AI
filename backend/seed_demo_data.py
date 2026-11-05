import requests

API_URL = "http://127.0.0.1:8000/api/leads"

demo_leads = [
    {"name": "Rahim Uddin", "email": "rahim@example.com", "phone": "01711111111", "company": "Rahim Tech", "source": "website", "interest": "AI Services", "value": 5000},
    {"name": "Karim Ahmed", "email": "karim@example.com", "phone": "01822222222", "company": "Karim Enterprise", "source": "facebook", "interest": "Digital Marketing", "value": 12000},
    {"name": "Sajid Hasan", "email": "sajid@example.com", "phone": "01933333333", "company": "Sajid Corp", "source": "linkedin", "interest": "Business Automation", "value": 8000}
]

for lead in demo_leads:
    response = requests.post(API_URL, json=lead)
    if response.status_code == 201:
        print(f"✅ Added: {lead['name']}")
    elif response.status_code == 409:
        print(f"⏭️ Skipped (duplicate): {lead['name']}")
    else:
        print(f"❌ Failed: {lead['name']} - {response.text}")

print("Demo data seeding complete!")