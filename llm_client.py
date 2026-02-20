import re
import httpx

from config import GROQ_API_KEY, GROQ_MODEL
from prompts import FEEDBACK_TO_JIRA_PROMPT, SUMMARY_ONLY_PROMPT

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


def generate_summary_only(feedback: str) -> str:
    """Generate a short one-line summary from feedback. Use feedback as-is for description."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Get a free key at https://console.groq.com")
    prompt = f"{SUMMARY_ONLY_PROMPT}\n\nFEEDBACK:\n{feedback}"
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.3,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            GROQ_CHAT_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
    data = r.json()
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
    summary_match = re.search(r"SUMMARY:\s*(.+)", text, re.DOTALL | re.IGNORECASE)
    if summary_match:
        return " ".join(summary_match.group(1).strip().split())[:255] or "Bug"
    return (feedback[:200].strip() or "Bug").split("\n")[0][:255]


def generate_summary_and_description(feedback: str) -> tuple[str, str]:
    """Call Groq (free tier) to get SUMMARY and DESCRIPTION from feedback. Returns (summary, description)."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Get a free key at https://console.groq.com")
    prompt = f"{FEEDBACK_TO_JIRA_PROMPT}\n\nFEEDBACK:\n{feedback}"
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024,
        "temperature": 0.3,
    }
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            GROQ_CHAT_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        r.raise_for_status()
    data = r.json()
    text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""

    summary = ""
    description = ""
    summary_match = re.search(
        r"SUMMARY:\s*(.+?)(?=\nDESCRIPTION:|\nDESCRIPTION\s*:|\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if summary_match:
        summary = summary_match.group(1).strip().split("\n")[0][:255]
    desc_match = re.search(r"DESCRIPTION\s*:\s*(.+)", text, re.DOTALL | re.IGNORECASE)
    if desc_match:
        description = desc_match.group(1).strip()[:65000]

    if not summary:
        summary = feedback[:200].strip() or "Feedback"
    if not description:
        description = feedback[:65000]

    return summary, description
