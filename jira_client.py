import httpx

from config import (
    JIRA_BASE_URL,
    JIRA_EMAIL,
    JIRA_API_TOKEN,
    JIRA_PROJECT,
    JIRA_ISSUE_TYPE,
    JIRA_LABELS,
    JIRA_EPIC_LINK,
    JIRA_EPIC_FIELD_ID,
    JIRA_CF_ENVIRONMENT,
    JIRA_CF_CUSTOMER_REPORTED_BUG,
    JIRA_CF_CUSTOMER_NAME,
    JIRA_CF_MODULE,
)


def _auth():
    return (JIRA_EMAIL, JIRA_API_TOKEN)


def _headers():
    return {"Accept": "application/json", "Content-Type": "application/json"}


def get_components(project_key: str) -> list[dict]:
    """Fetch components for project. Returns list of {id, name}."""
    url = f"{JIRA_BASE_URL}/rest/api/3/project/{project_key}/components"
    with httpx.Client(timeout=15.0) as client:
        r = client.get(url, auth=_auth(), headers=_headers())
        r.raise_for_status()
    data = r.json()
    return [{"id": c["id"], "name": c.get("name", "")} for c in data]


def get_component_id_by_name(project_key: str, component_name: str) -> str | None:
    """Return component id for the given name, or None if not found."""
    components = get_components(project_key)
    name_lower = (component_name or "").strip().lower()
    for c in components:
        if (c.get("name") or "").strip().lower() == name_lower:
            return str(c.get("id")) if c.get("id") is not None else None
    return None


def get_default_chat_component_id(
    project_key: str,
    preferred_names: list[str],
    fallback_id: str | None = None,
) -> str | None:
    """
    Resolve default component: try each preferred name (e.g. RA_FE, RA FE, RA-FE),
    then fallback_id, then first component in project. Returns id as string or None.
    """
    for name in preferred_names:
        if name and name.strip():
            cid = get_component_id_by_name(project_key, name)
            if cid:
                return cid
    if fallback_id and str(fallback_id).strip():
        return str(fallback_id).strip()
    components = get_components(project_key)
    if components and components[0].get("id") is not None:
        return str(components[0]["id"])
    return None


def get_priorities() -> list[dict]:
    """Fetch all priorities. Returns list of {id, name}."""
    url = f"{JIRA_BASE_URL}/rest/api/3/priority"
    with httpx.Client(timeout=15.0) as client:
        r = client.get(url, auth=_auth(), headers=_headers())
        r.raise_for_status()
    data = r.json()
    return [{"id": p["id"], "name": p.get("name", "")} for p in data]


def get_assignable_users(project_key: str, query: str = "") -> list[dict]:
    """Search users assignable to the project. Returns list of {accountId, displayName, emailAddress}."""
    url = f"{JIRA_BASE_URL}/rest/api/3/user/assignable/search"
    params = {"project": project_key, "maxResults": 50}
    if query and query.strip():
        params["query"] = query.strip()
    with httpx.Client(timeout=15.0) as client:
        r = client.get(url, params=params, auth=_auth(), headers=_headers())
        r.raise_for_status()
    data = r.json()
    return [
        {
            "accountId": u.get("accountId", ""),
            "displayName": u.get("displayName", ""),
            "emailAddress": u.get("emailAddress", ""),
        }
        for u in data
    ]


def get_user_account_id_by_name(project_key: str, display_name: str) -> str | None:
    """Find a user's accountId by display name (case-insensitive partial match)."""
    if not display_name or not display_name.strip():
        return None
    name_lower = display_name.strip().lower()
    users = get_assignable_users(project_key, display_name)
    for u in users:
        if name_lower in (u.get("displayName") or "").lower():
            return u.get("accountId")
    return None


def get_priority_id_by_name(priority_name: str) -> str | None:
    """Find priority ID by name (case-insensitive)."""
    if not priority_name or not priority_name.strip():
        return None
    name_lower = priority_name.strip().lower()
    priorities = get_priorities()
    for p in priorities:
        if (p.get("name") or "").lower() == name_lower:
            return p.get("id")
    return None


def _description_to_atlassian_doc(text: str) -> dict:
    """Convert plain text to Atlassian Document Format (ADF) for description."""
    content = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            content.append({"type": "paragraph", "content": []})
            continue
        content.append({
            "type": "paragraph",
            "content": [{"type": "text", "text": line}],
        })
    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": text or "—"}]}]
    return {"type": "doc", "version": 1, "content": content}


def _sanitize_summary(s: str) -> str:
    """Jira summary must be a single line (no newlines)."""
    return " ".join(s.split()).strip()[:255] or "Bug"


def create_issue(
    summary: str,
    description: str,
    *,
    sprint: str | None = None,
    component_id: str | None = None,
    priority_id: str | None = None,
    assignee_account_id: str | None = None,
    environment: str | None = None,
    module: str | None = None,
    customer_reported_bug: str | None = None,
    customer_name: str | None = None,
) -> tuple[str, str]:
    """
    Create a Jira Bug. Environment, Module, Customer Reported Bug, Customer Name come from form.
    Returns (issue_key, browse_url).
    """
    env_val = (environment or "").strip() or "Production"
    mod_val = (module or "").strip() or "Super Admin"
    crb_val = (customer_reported_bug or "No").capitalize()
    cname_val = (customer_name or "").strip() or "NA"

    body = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "summary": _sanitize_summary(summary),
            "description": _description_to_atlassian_doc(description),
            "issuetype": {"name": JIRA_ISSUE_TYPE},
            "labels": [JIRA_LABELS, "ZProdBug"],
            # Required custom fields (values from form)
            JIRA_CF_ENVIRONMENT: {"value": env_val},
            JIRA_CF_CUSTOMER_REPORTED_BUG: {"value": crb_val},
            JIRA_CF_CUSTOMER_NAME: cname_val,
            JIRA_CF_MODULE: {"value": mod_val},
        }
    }
    if component_id:
        body["fields"]["components"] = [{"id": component_id}]
    if priority_id:
        body["fields"]["priority"] = {"id": priority_id}
    if assignee_account_id and assignee_account_id.strip():
        body["fields"]["assignee"] = {"accountId": assignee_account_id.strip()}
    if JIRA_EPIC_FIELD_ID:
        body["fields"][JIRA_EPIC_FIELD_ID] = JIRA_EPIC_LINK

    with httpx.Client(timeout=30.0) as client:
        r = client.post(
            f"{JIRA_BASE_URL}/rest/api/3/issue",
            json=body,
            auth=_auth(),
            headers=_headers(),
        )
        if not r.is_success:
            try:
                err_body = r.json()
                msg = err_body.get("errorMessages", [])
                if isinstance(msg, list) and msg:
                    err_detail = "; ".join(str(m) for m in msg)
                else:
                    err_detail = err_body.get("errors", {})
                    err_detail = str(err_detail) if err_detail else r.text or r.reason_phrase
            except Exception:
                err_detail = r.text or r.reason_phrase
            raise ValueError(f"Jira API {r.status_code}: {err_detail}")
        data = r.json()
    key = data["key"]
    url = f"{JIRA_BASE_URL}/browse/{key}"
    return key, url


def add_attachments(issue_key: str, files: list[tuple[str, bytes, str]]) -> None:
    """Attach files to an issue. files = list of (filename, content_bytes, content_type). Max 4 recommended."""
    if not files:
        return
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/attachments"
    # Jira expects multipart/form-data with each part named "file"
    file_parts = [
        ("file", (filename, content, content_type))
        for filename, content, content_type in files[:4]
    ]
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            url,
            files=file_parts,
            auth=_auth(),
            headers={"X-Atlassian-Token": "no-check"},
        )
        if not r.is_success:
            try:
                err = r.json()
                err_detail = err.get("errorMessages", err.get("errors", r.text))
            except Exception:
                err_detail = r.text or r.reason_phrase
            raise ValueError(f"Jira attachments {r.status_code}: {err_detail}")
