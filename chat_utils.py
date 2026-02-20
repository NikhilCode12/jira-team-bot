"""Utilities for chat-triggered Jira creation (e.g. Teams)."""
import re


def extract_customer_name(message: str) -> str:
    """
    Extract customer name from message text if mentioned.
    Looks for patterns like:
      - Customer: John Doe
      - Customer name: Acme Corp
      - Customer - Jane
      - customer: XYZ
    Returns "NA" if no match.
    """
    if not message or not isinstance(message, str):
        return "NA"
    text = message.strip()
    if not text:
        return "NA"

    # Case-insensitive patterns; capture group = customer value
    patterns = [
        r"Customer\s*:\s*(.+?)(?:\n|$)",           # Customer: ... (to newline or end)
        r"Customer\s+name\s*:\s*(.+?)(?:\n|$)",    # Customer name: ...
        r"Customer\s*-\s*(.+?)(?:\n|$)",          # Customer - ...
        r"customer\s*:\s*(.+?)(?:\n|$)",
        r"customer\s+name\s*:\s*(.+?)(?:\n|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            name = m.group(1).strip()
            # Stop at common punctuation or next label
            name = re.split(r"[\n,;]|Customer\s*[:\-]|#|@", name, maxsplit=1)[0].strip()
            if name and len(name) <= 200:
                return name
    return "NA"


def message_has_trigger(message: str) -> bool:
    """
    Check if message contains #ZProdBug or #TeamsJIRABugBot. Either trigger works.
    """
    if not message or not isinstance(message, str):
        return False
    text = message.strip()
    return (
        "#ZProdBug" in text or "ZProdBug" in text or
        "#TeamsJIRABugBot" in text or "TeamsJIRABugBot" in text
    )


def extract_assignee(message: str, default: str = "Aeras Alvi") -> str:
    """
    Extract assignee from message text if mentioned.
    Looks for patterns like:
      - Assignee: John Doe
      - Assignee - Jane Smith
      - Assigned to: Bob
    Returns default if no match.
    """
    if not message or not isinstance(message, str):
        return default
    text = message.strip()
    if not text:
        return default

    patterns = [
        r"Assignee\s*[:\-]\s*(.+?)(?:\n|$)",
        r"Assigned\s+to\s*[:\-]?\s*(.+?)(?:\n|$)",
        r"Assign\s+to\s*[:\-]?\s*(.+?)(?:\n|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            name = re.split(r"[\n,;]|#|@|\(", name, maxsplit=1)[0].strip()
            if name and len(name) <= 100:
                return name
    return default


def extract_priority(message: str) -> str | None:
    """
    Extract priority from message text if mentioned.
    Looks for patterns like:
      - Priority: High
      - Priority - Critical
      - P1, P2, P3, etc.
    Returns None if no match.
    """
    if not message or not isinstance(message, str):
        return None
    text = message.strip()
    if not text:
        return None

    patterns = [
        r"Priority\s*[:\-]\s*(.+?)(?:\n|$)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            priority = m.group(1).strip()
            priority = re.split(r"[\n,;]|#|@", priority, maxsplit=1)[0].strip()
            if priority and len(priority) <= 50:
                return priority

    p_match = re.search(r"\b(P[1-5])\b", text, re.IGNORECASE)
    if p_match:
        p_level = p_match.group(1).upper()
        priority_map = {"P1": "Highest", "P2": "High", "P3": "Medium", "P4": "Low", "P5": "Lowest"}
        return priority_map.get(p_level)

    return None


def clean_message_for_jira(message: str) -> str:
    """
    Remove trigger hashtags and clean up the message for Jira description.
    Removes #ZProdBug, #TeamsJIRABugBot, and cleans extra whitespace.
    """
    if not message or not isinstance(message, str):
        return message or ""
    text = message

    text = re.sub(r"#?ZProdBug\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"#?TeamsJIRABugBot\s*", "", text, flags=re.IGNORECASE)

    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    text = "\n".join(lines)

    return text.strip()
