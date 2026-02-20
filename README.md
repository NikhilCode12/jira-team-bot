# Jira Team Utility (Feedback to Issue)

Create Jira bugs from product feedback or from Teams chat (#TeamsJIRABugBot) using a free LLM (Groq) and Jira Cloud API.

## Setup

1. Copy `.env.example` to `.env` and fill in:
   - **JIRA_BASE_URL**, **JIRA_EMAIL**, **JIRA_API_TOKEN** (from [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens))
   - **GROQ_API_KEY** (from [Groq Console](https://console.groq.com))
   - Optional: **DEFAULT_CHAT_COMPONENT_NAME**, **DEFAULT_CHAT_COMPONENT_ID** for Teams/chat flow

2. Install and run:

   ```bash
   pip install -r requirements.txt
   uvicorn app:app --reload
   ```

3. Open http://127.0.0.1:8000 (main form) or http://127.0.0.1:8000/test-teams (test Teams-style message).

## Jira project

- **Project**: ZRA (configurable via `JIRA_PROJECT` in `.env`).
- **Issue type**: Bug. **Labels**: BetaConnect, ZProdBug.
- **Epic**: ZRA-51. Set `JIRA_EPIC_FIELD_ID` in `.env` if your project uses Epic Link.
- **Chat/Teams**: Default component when not in message: RA_FE (or set `DEFAULT_CHAT_COMPONENT_NAME` / `DEFAULT_CHAT_COMPONENT_ID`).

## Usage

- **Web form**: Enter feedback, optional Sprint/Component/Priority/Customer name, then **Create Jira**.
- **Teams / Power Automate**: POST to `/create-jira-from-chat` with body `{"message": "<chat text>", "skip_trigger_check": false}`. Message should contain `#TeamsJIRABugBot` unless `skip_trigger_check` is true. Customer name is parsed from message (e.g. "Customer: X") or use "NA".

**Do not commit `.env`** — it contains secrets. Use `.env.example` as a template.
