import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# Jira: only project (ZRA) and credentials in .env; other values from form or hardcoded
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT = os.getenv("JIRA_PROJECT", "ZRA")

JIRA_ISSUE_TYPE = "Bug"
JIRA_LABELS = "BetaConnect"
JIRA_EPIC_LINK = "ZRA-51"
# Epic Link field ID: set in .env (e.g. customfield_10014) to link created issues to Epic ZRA-51
JIRA_EPIC_FIELD_ID = os.getenv("JIRA_EPIC_FIELD_ID", "").strip()

JIRA_CF_ENVIRONMENT = "customfield_14669"
JIRA_CF_CUSTOMER_REPORTED_BUG = "customfield_15855"
JIRA_CF_CUSTOMER_NAME = "customfield_15856"
JIRA_CF_MODULE = "customfield_14720"

# Chat/Teams: default component when not given in message
DEFAULT_CHAT_COMPONENT_NAME = os.getenv("DEFAULT_CHAT_COMPONENT_NAME", "RA_FE").strip()
# Optional: Jira component ID if name lookup fails (e.g. "12345")
DEFAULT_CHAT_COMPONENT_ID = os.getenv("DEFAULT_CHAT_COMPONENT_ID", "").strip()

# Free hosted LLM (Groq - free tier, no local setup)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
