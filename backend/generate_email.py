"""
Day 3 - Member 3
generate_welcome_email(lead) -> {"subject": str, "body": str}

Input lead example:
    {"name": "রাহিম", "email": "rahim@example.com", "company": "Rahim Traders", "phone": "017XXXXXXXX"}

AI ব্যর্থ হলে বা JSON ভুল এলে fallback টেমপ্লেট ফেরত দেয়, তাই এই function কখনো crash করবে না।
"""
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---- Business settings: এখানে নিজেদের তথ্য বসান ----
COMPANY = {
    "company_name": os.getenv("COMPANY_NAME", "SmartBiz AI"),
    "services": os.getenv("COMPANY_SERVICES", "AI-powered lead automation for businesses"),
    "sender_name": os.getenv("SENDER_NAME", "Support Team"),
    "cta": os.getenv("COMPANY_CTA", "এই ইমেইলে রিপ্লাই করুন"),
    "language": os.getenv("EMAIL_LANGUAGE", "Bangla"),
}

# AI_MODEL-এ এক বা কমা দিয়ে একাধিক মডেল দেওয়া যায়। প্রথমটা ব্যস্ত/বন্ধ থাকলে নিচের বিকল্পগুলো নিজে চেষ্টা হবে।
_DEFAULT_MODELS = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-latest"]
_chosen = [m.strip().replace("models/", "") for m in os.getenv("AI_MODEL", "").split(",") if m.strip()]
MODELS = _chosen + [m for m in _DEFAULT_MODELS if m not in _chosen]
MODEL = MODELS[0]
PROMPT_PATH = Path(__file__).parent / "prompt_template.txt"


def _clean(value, default):
    """ফাঁকা বা None হলে default ব্যবহার করে।"""
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _fallback_english(lead):
    name = _clean(lead.get("name"), "")
    company = _clean(lead.get("company"), "")
    greeting = f"Dear {name}," if name else "Dear Customer,"
    line = f"We would love to learn how we can help {company}. " if company else ""
    return {
        "subject": f"Welcome to {COMPANY['company_name']}!",
        "body": (
            f"{greeting}\n\nThank you for contacting {COMPANY['company_name']}. {line}"
            f"We are ready to talk. Please reply to this email.\n\n"
            f"Best regards,\n{COMPANY['sender_name']}"
        ),
    }


def fallback_email(lead):
    """AI কাজ না করলে এই ডিফল্ট Welcome Email যাবে।"""
    if _clean(lead.get("language"), COMPANY["language"]).lower().startswith("en"):
        return _fallback_english(lead)
    name = _clean(lead.get("name"), "প্রিয় গ্রাহক")
    lead_company = _clean(lead.get("company"), "")
    interest = _clean(lead.get("interest"), "")
    if lead_company:
        interest_line = f"{lead_company}-এর ব্যবসায় আমরা কীভাবে সাহায্য করতে পারি, তা জানতে আগ্রহী। "
    elif interest:
        interest_line = f"{interest} নিয়ে আপনার আগ্রহ জেনে আমরা আনন্দিত। "
    else:
        interest_line = ""
    greeting = name if name == "প্রিয় গ্রাহক" else f"প্রিয় {name}"
    subject = f"স্বাগতম {COMPANY['company_name']}-এ!"
    body = (
        f"{greeting},\n\n"
        f"{COMPANY['company_name']}-এর সাথে যোগাযোগ করার জন্য ধন্যবাদ। "
        f"{interest_line}"
        f"আপনার সাথে কথা বলতে আমরা প্রস্তুত। {COMPANY['cta']}।\n\n"
        f"শুভেচ্ছান্তে,\n{COMPANY['sender_name']}"
    )
    return {"subject": subject, "body": body}


# উর্দু/আরবি (0600-06FF, 0750-077F) ও দেবনাগরী (0900-097F) অক্ষর ধরে; বাংলা দাঁড়ি । (0964/0965) ইচ্ছে করে বাদ
_WRONG_SCRIPT = re.compile("[%s-%s%s-%s%s-%s%s-%s]" % (chr(0x600), chr(0x6FF), chr(0x750), chr(0x77F), chr(0x900), chr(0x963), chr(0x966), chr(0x97F)))


def _parse_json(text):
    """AI-এর উত্তর থেকে JSON বের করে। ```json ... ``` থাকলেও কাজ করে।"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON found")
    data = json.loads(text[start : end + 1])
    if not data.get("subject") or not data.get("body"):
        raise ValueError("subject/body missing")
    subject, body = str(data["subject"]).strip(), str(data["body"]).strip()
    if _WRONG_SCRIPT.search(subject + body):
        raise ValueError("অন্য ভাষার অক্ষর (উর্দু/আরবি/হিন্দি) পাওয়া গেছে")
    return {"subject": subject, "body": body}


def _check_sender(result, lead_company):
    """AI ভুল করে customer-এর company-কে sender বানালে (যেমন 'Rahim Traders-এর পক্ষ থেকে') বাতিল করে।"""
    if not lead_company:
        return
    c = re.escape(lead_company)
    text = result["subject"] + " " + result["body"]
    patterns = [c + r"[\s\-]*(?:এর|র)?[\s\-]*পক্ষ", r"on behalf of\s+" + c]
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            raise ValueError("AI ভুল করে customer-এর company-কে sender বানিয়েছে")


def to_html(subject, body):
    """Plain text body থেকে সুন্দর HTML email বানায় (Gmail node-এ HTML হিসেবে পাঠানোর জন্য)।"""
    from html import escape

    paragraphs = "".join(
        f'<p style="margin:0 0 14px;">{escape(p).replace(chr(10), "<br>")}</p>'
        for p in body.split("\n\n")
        if p.strip()
    )
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:auto;'
        'padding:24px;border:1px solid #e5e7eb;border-radius:8px;color:#1f2937;'
        'font-size:15px;line-height:1.6;">'
        f'<h2 style="margin:0 0 18px;font-size:20px;color:#111827;">{escape(subject)}</h2>'
        f"{paragraphs}</div>"
    )


def generate_welcome_email(lead):
    """মূল function। সবসময় {"subject", "body", "html", "source"} ফেরত দেয়।
    source = "ai" অথবা "fallback" (Member 5 dashboard-এ দেখাতে পারবে)।
    """
    result = _generate(lead)
    result["html"] = to_html(result["subject"], result["body"])
    return result


def _generate(lead):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {**fallback_email(lead), "source": "fallback"}

    try:
        from google import genai
        from google.genai import types

        prompt = PROMPT_PATH.read_text(encoding="utf-8").format(
            company_name=COMPANY["company_name"],
            services=COMPANY["services"],
            sender_name=COMPANY["sender_name"],
            cta=COMPANY["cta"],
            language=_clean(lead.get("language"), COMPANY["language"]),
            name=_clean(lead.get("name"), "প্রিয় গ্রাহক"),
            lead_company=_clean(lead.get("company"), _clean(lead.get("interest"), "not provided")),
        )
        client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=15000))
        result, last_error = None, None
        for model in MODELS:  # একটা মডেল ব্যর্থ হলে পরেরটায় যাও
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json"),
                )
                result = _parse_json(response.text)
                _check_sender(result, _clean(lead.get("company"), ""))
                break
            except Exception as err:
                last_error = err
                print(f"[warn] {model} ব্যর্থ ({str(err)[:80]}), পরের মডেল চেষ্টা করছি...")
        if result is None:
            raise last_error
        return {**result, "source": "ai"}
    except Exception as error:  # AI/network/JSON যেকোনো সমস্যায় fallback
        print(f"[warn] AI failed, using fallback: {error}")
        return {**fallback_email(lead), "source": "fallback"}
