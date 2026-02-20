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
