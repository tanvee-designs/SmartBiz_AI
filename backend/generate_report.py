"""
Day 5 - Member 3
generate_business_report(leads, email_logs=None, language="Bangla") -> dict

leads / email_logs: dict-এর list অথবা SQLAlchemy object-এর list (দুটোই চলবে)।
সংখ্যাগুলো Python নিজে গুণে বের করে (ভুল হবে না); AI শুধু সেই সংখ্যা দেখে লেখা (summary, insights, recommendations) তৈরি করে।
লিডের ইমেইল/ফোন AI-কে পাঠানো হয় না, শুধু গণনা পাঠানো হয়।
AI ব্যর্থ হলে fallback রিপোর্ট ফেরত দেয়, তাই এই function কখনো crash করবে না।

ফেরত দেয়: {"title", "summary", "insights", "recommendations", "stats",
            "notification_text", "html", "source" ("ai" / "fallback"), "generated_at"}
"""
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from html import escape
from pathlib import Path

from dotenv import load_dotenv

from generate_email import COMPANY, MODELS, _WRONG_SCRIPT, _clean

load_dotenv()

PROMPT_PATH = Path(__file__).parent / "report_prompt_template.txt"


def _get(item, key, default=None):
    """dict ও object দুটো থেকেই মান পড়ে।"""
    if isinstance(item, dict):
        return item.get(key, default)
    return getattr(item, key, default)


def _parse_date(value):
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
    return None


def build_stats(leads, email_logs=None):
    """লিড ও ইমেইল লগ থেকে সংখ্যাগুলো গুণে বের করে।"""
    leads, logs = list(leads or []), list(email_logs or [])
    now = datetime.utcnow()

    by_status = Counter(_clean(_get(l, "status"), "unknown") for l in leads)
    new_7d = 0
    for l in leads:
        d = _parse_date(_get(l, "created_at"))
        if d and now - d <= timedelta(days=7):
            new_7d += 1

    email_status = Counter(_clean(_get(x, "status"), "pending") for x in logs)
    generated_by = Counter(_clean(_get(x, "generated_by"), "ai") for x in logs)
    sent, failed = email_status.get("sent", 0), email_status.get("failed", 0)
    rate = round(sent * 100 / len(logs)) if logs else None

    return {
        "total_leads": len(leads),
        "leads_with_company": sum(1 for l in leads if _clean(_get(l, "company"), "")),
        "new_leads_last_7_days": new_7d,
        "leads_by_status": dict(by_status),
        "emails_total": len(logs),
        "emails_sent": sent,
        "emails_failed": failed,
        "emails_pending": email_status.get("pending", 0),
        "emails_written_by_ai": generated_by.get("ai", 0),
        "emails_written_by_fallback": generated_by.get("fallback", 0),
        "email_success_rate_percent": rate,
    }


def _notification_text(stats, language):
    if language.lower().startswith("en"):
        return (f"{COMPANY['company_name']} report: {stats['total_leads']} leads, "
                f"{stats['emails_sent']}/{stats['emails_total']} emails sent, "
                f"{stats['emails_failed']} failed.")
    return (f"{COMPANY['company_name']} রিপোর্ট: মোট {stats['total_leads']} জন লিড, "
            f"{stats['emails_total']}টি ইমেইলের মধ্যে {stats['emails_sent']}টি পাঠানো হয়েছে, "
            f"{stats['emails_failed']}টি ব্যর্থ।")


def _fallback_report(stats, language):
    """AI কাজ না করলে সংখ্যা দিয়ে বানানো ডিফল্ট রিপোর্ট।"""
    if language.lower().startswith("en"):
        return {
            "summary": (f"There are {stats['total_leads']} leads in total, "
                        f"{stats['new_leads_last_7_days']} of them new in the last 7 days. "
                        f"{stats['emails_sent']} of {stats['emails_total']} welcome emails were sent."),
            "insights": [
                f"{stats['leads_with_company']} leads provided a company name.",
                f"{stats['emails_failed']} emails failed and {stats['emails_pending']} are pending.",
                f"{stats['emails_written_by_fallback']} emails used the default template instead of AI.",
            ],
            "recommendations": [
                "Follow up with leads that have not received an email yet.",
                "Check the failed emails and resend them.",
                "Review the leads that have not been contacted after a few days.",
            ],
        }
    return {
        "summary": (f"মোট {stats['total_leads']} জন লিড আছে, গত ৭ দিনে নতুন এসেছে "
                    f"{stats['new_leads_last_7_days']} জন। {stats['emails_total']}টি Welcome Email-এর মধ্যে "
                    f"{stats['emails_sent']}টি পাঠানো হয়েছে।"),
        "insights": [
            f"{stats['leads_with_company']} জন লিড তাদের কোম্পানির নাম দিয়েছেন।",
            f"{stats['emails_failed']}টি ইমেইল ব্যর্থ এবং {stats['emails_pending']}টি অপেক্ষমাণ আছে।",
            f"{stats['emails_written_by_fallback']}টি ইমেইলে AI-র বদলে ডিফল্ট টেমপ্লেট ব্যবহার হয়েছে।",
        ],
        "recommendations": [
            "যাদের কাছে এখনো ইমেইল যায়নি তাদের সাথে যোগাযোগ করুন।",
            "ব্যর্থ ইমেইলগুলো পরীক্ষা করে আবার পাঠান।",
            "কয়েক দিন ধরে যোগাযোগ হয়নি এমন লিডদের তালিকা দেখুন।",
        ],
    }


def _parse_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found")
    data = json.loads(text[start : end + 1])

    summary = str(data.get("summary", "")).strip()
    insights = [str(x).strip() for x in data.get("insights", []) if str(x).strip()]
    recs = [str(x).strip() for x in data.get("recommendations", []) if str(x).strip()]
    if not summary or not insights or not recs:
        raise ValueError("summary/insights/recommendations missing")
    if _WRONG_SCRIPT.search(summary + "".join(insights) + "".join(recs)):
        raise ValueError("অন্য ভাষার অক্ষর (উর্দু/আরবি/হিন্দি) পাওয়া গেছে")
    return {"summary": summary, "insights": insights[:3], "recommendations": recs[:3]}


def to_html(title, report):
    items = lambda xs: "".join(f"<li>{escape(x)}</li>" for x in xs)
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:auto;padding:24px;'
        'border:1px solid #e5e7eb;border-radius:8px;color:#1f2937;font-size:15px;line-height:1.6;">'
        f'<h2 style="margin:0 0 14px;font-size:20px;">{escape(title)}</h2>'
        f'<p>{escape(report["summary"])}</p>'
        f'<h3 style="font-size:16px;">Insights</h3><ul>{items(report["insights"])}</ul>'
        f'<h3 style="font-size:16px;">Recommendations</h3><ul>{items(report["recommendations"])}</ul></div>'
    )


def generate_business_report(leads, email_logs=None, language=None):
    """মূল function। সবসময় রিপোর্টের dict ফেরত দেয়।"""
    language = _clean(language, COMPANY["language"])
    stats = build_stats(leads, email_logs)
    report, source = _generate(stats, language)
    title = (f"{COMPANY['company_name']} Business Report" if language.lower().startswith("en")
             else f"{COMPANY['company_name']} ব্যবসায়িক রিপোর্ট")
    return {
        "title": title,
        **report,
        "stats": stats,
        "notification_text": _notification_text(stats, language),
        "html": to_html(title, report),
        "source": source,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def _generate(stats, language):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or stats["total_leads"] == 0:  # ডেটা না থাকলে AI-কে ডাকার দরকার নেই
        return _fallback_report(stats, language), "fallback"
    try:
        from google import genai
        from google.genai import types

        prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
            company_name=COMPANY["company_name"],
            services=COMPANY["services"],
            language=language,
            stats_json=json.dumps(stats, ensure_ascii=False, indent=2),
        )
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=20000))
        result, last_error = None, None
        for model in MODELS:  # একটা মডেল ব্যর্থ হলে পরেরটায় যাও
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                result = _parse_json(response.text)
                break
            except Exception as err:
                last_error = err
                print(f"[warn] {model} ব্যর্থ ({str(err)[:80]}), পরের মডেল চেষ্টা করছি...")
        if result is None:
            raise last_error
        return result, "ai"
    except Exception as error:
        print(f"[warn] AI failed, using fallback: {error}")
        return _fallback_report(stats, language), "fallback"
