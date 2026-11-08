import json
import sys

import httpx

BASE_URL = "http://127.0.0.1:8000"

LEADS = [
    {"name": "Sara Khan", "email": "sara.demo@example.com", "phone": "01711000011",
     "company": "Sara Studio", "source": "facebook", "interest": "AI lead automation",
     "value": 25000, "status": "new"},
    {"name": "Imran Hossain", "email": "imran.demo@example.com", "phone": "01711000012",
     "company": "Hossain Traders", "source": "website", "interest": "Email follow-up",
     "value": 18000, "status": "contacted"},
    {"name": "Mitu Akter", "email": "mitu.demo@example.com", "phone": "01711000013",
     "company": "Mitu Boutique", "source": "linkedin", "interest": "CRM and reports",
     "value": 40000, "status": "qualified"},
    {"name": "Jamal Uddin", "email": "jamal.demo@example.com", "phone": "01711000014",
     "company": "Uddin Electronics", "source": "referral", "interest": "Full automation",
     "value": 60000, "status": "converted"},
    {"name": "Farzana Rahman", "email": "farzana.demo@example.com", "phone": "01711000015",
     "company": "Rahman Foods", "source": "google_forms", "interest": "Lead tracking",
     "value": 12000, "status": "new"},
    {"name": "Kabir Ahmed", "email": "kabir.demo@example.com", "phone": "01711000016",
     "company": "Ahmed Logistics", "source": "email", "interest": "Dashboard",
     "value": 8000, "status": "lost"},
    {"name": "Lamia Islam", "email": "lamia.demo@example.com", "phone": "01711000017",
     "company": "Islam Fashion", "source": "website", "interest": "AI reports",
     "value": 30000, "status": "contacted"},
]

CUSTOMERS = [
    {"name": "Rahim Uddin", "email": "rahim.demo@example.com", "phone": "01711000001",
     "company": "Rahim Traders", "total_deals": 3},
    {"name": "Nusrat Jahan", "email": "nusrat.demo@example.com", "phone": "01811000002",
     "company": "Jahan Fashion", "total_deals": 1},
    {"name": "Tanvir Hasan", "email": "tanvir.demo@example.com", "phone": "01911000003",
     "company": "Hasan Electronics", "total_deals": 5},
]

NOTIFICATIONS = [
    "New lead received: Sara Khan (Facebook)",
    "Welcome email sent to Rahim Uddin",
    "Weekly AI business report is ready to view",
]

REPORT = {
    "report_type": "ai_report",
    "title": "Weekly Business Performance Report",
    "summary": (
        "This week SmartBiz_AI collected new leads from several channels. "
        "Most leads came from the website and Facebook, and a good share "
        "of them already moved to the contacted or qualified stage."
    ),
    "insights": [
        "The website and Facebook are the strongest lead sources this week",
        "Two leads are in contact and one is already converted",
        "Welcome emails were sent without errors",
    ],
    "recommendations": [
        "Follow up with new leads within 24 hours",
        "Invest more in Facebook campaigns",
        "Review leads that stay in the contacted status for more than 3 days",
    ],
}

results = []


def check(label, condition):
    results.append(condition)
    print(("PASS  " if condition else "FAIL  ") + label)


def main():
    with httpx.Client(base_url=BASE_URL, timeout=20) as client:
        try:
            client.get("/health")
        except httpx.ConnectError:
            print("Server is not running. Start it first: uvicorn main:app --reload")
            sys.exit(1)

        # 1) Leads (status changes use PATCH /api/leads/{id})
        created = {}
        for lead in LEADS:
            body = {key: val for key, val in lead.items() if key != "status"}
            response = client.post("/api/leads", json=body)
            if response.status_code == 201:
                data = response.json()
                created[lead["email"]] = data
                if lead["status"] != "new":
                    client.patch(f"/api/leads/{data['id']}", json={"status": lead["status"]})
                print("Lead created:", lead["email"], "->", lead["status"])
            else:
                print("Lead FAILED:", response.status_code, response.text)

        # 2) Customers
        for customer in CUSTOMERS:
            response = client.post("/api/customers", json=customer)
            print("Customer", customer["email"], "->", response.status_code)

        # 3) Notifications (the second one becomes read, 2 stay unread)
        ids = []
        for message in NOTIFICATIONS:
            response = client.post("/api/notifications", json={"message": message})
            if response.status_code == 201:
                ids.append(response.json()["id"])
        if len(ids) >= 2:
            client.patch(f"/api/notifications/{ids[1]}/read")

        # 4) AI report
        response = client.post("/api/reports", json=REPORT)
        print("Report ->", response.status_code)

        # 5) Self-check
        print()
        print("--- CHECKS ---")
        first = LEADS[0]
        first_data = created.get(first["email"], {})
        check("Lead response has interest and value",
              first_data.get("interest") == first["interest"]
              and first_data.get("value") == first["value"])

        again = client.post("/api/leads", json={k: v for k, v in first.items() if k != "status"})
        check("Duplicate email returns 409", again.status_code == 409)

        bad = client.post("/api/leads", json={"name": "Bad Source", "email": "bad.source@example.com", "source": "tiktok"})
        check("Unknown source returns 422", bad.status_code == 422)

        patch_id = first_data.get("id", 1)
        patched = client.patch(f"/api/leads/{patch_id}", json={"status": "contacted"})
        check("PATCH /api/leads/{id} returns 200", patched.status_code == 200)
        client.patch(f"/api/leads/{patch_id}", json={"status": "new"})

        stats = client.get("/api/stats/summary")
        stats_ok = (
            stats.status_code == 200
            and stats.json().get("total_leads") == len(LEADS)
            and stats.json()["leads_by_status"]["converted"] == 1
        )
        check("GET /api/stats/summary returns 200 and correct counts", stats_ok)

        reports = client.get("/api/reports").json()
        check("Report insights come back as a list",
              bool(reports) and isinstance(reports[0].get("insights"), list))

        print()
        print("Passed", sum(results), "of", len(results))

        # 6) Field names for Member 6
        customers = client.get("/api/customers").json()
        notifications = client.get("/api/notifications").json()
        print()
        print("--- /api/customers (first item) ---")
        print(json.dumps(customers[0], indent=2, ensure_ascii=False))
        print("--- /api/notifications (first item) ---")
        print(json.dumps(notifications[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()