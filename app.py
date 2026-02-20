from fastapi import FastAPI, Request, HTTPException, Form, File, UploadFile, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import JIRA_PROJECT, JIRA_EPIC_LINK, JIRA_LABELS, DEFAULT_CHAT_COMPONENT_NAME, DEFAULT_CHAT_COMPONENT_ID
from jira_client import (
    create_issue, get_components, get_priorities, get_assignable_users, add_attachments,
    get_default_chat_component_id, get_user_account_id_by_name, get_priority_id_by_name
)
from llm_client import generate_summary_only
from chat_utils import extract_customer_name, message_has_trigger, extract_assignee, extract_priority, clean_message_for_jira

app = FastAPI(title="Feedback to Jira")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "project": JIRA_PROJECT, "epic": JIRA_EPIC_LINK, "labels": JIRA_LABELS},
    )


@app.get("/test-teams", response_class=HTMLResponse)
async def test_teams(request: Request):
    """Test page: simulate a Teams message and create Jira without needing Teams."""
    return templates.TemplateResponse("test-teams.html", {"request": request})


@app.get("/api/components")
async def api_components():
    try:
        return get_components(JIRA_PROJECT)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/priorities")
async def api_priorities():
    try:
        return get_priorities()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/assignable-users")
async def api_assignable_users(query: str = ""):
    try:
        return get_assignable_users(JIRA_PROJECT, query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/create-jira")
async def create_jira_endpoint(
    feedback: str = Form(..., description="Description (used as-is in Jira)"),
    sprint: str | None = Form(None),
    component_id: str | None = Form(None),
    priority_id: str | None = Form(None),
    assignee_account_id: str | None = Form(None),
    environment: str | None = Form(None),
    module: str | None = Form(None),
    customer_reported_bug: str | None = Form(None),
    customer_name: str | None = Form(None),
    screenshots: list[UploadFile] = File(default=[], description="Up to 4 screenshots"),
):
    feedback = (feedback or "").strip()
    if not feedback:
        raise HTTPException(status_code=422, detail="Feedback is required")
    try:
        summary = generate_summary_only(feedback)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    description = feedback
    key, url = create_issue(
        summary,
        description,
        sprint=sprint,
        component_id=component_id or None,
        priority_id=priority_id or None,
        assignee_account_id=assignee_account_id or None,
        environment=environment or None,
        module=module or None,
        customer_reported_bug=customer_reported_bug or None,
        customer_name=customer_name or None,
    )
    files_to_attach = []
    for f in (screenshots or [])[:4]:
        if f.filename:
            content = await f.read()
            if content:
                ct = f.content_type or "application/octet-stream"
                files_to_attach.append((f.filename, content, ct))
    if files_to_attach:
        try:
            add_attachments(key, files_to_attach)
        except ValueError as e:
            pass
    return {"key": key, "url": url}


def _parse_skip_trigger(value: str | bool | None) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "on", "yes")


async def _create_jira_from_chat_impl(
    message: str,
    customer_name_override: str | None,
    skip_trigger_check: bool,
    screenshot_files: list[UploadFile],
) -> dict:
    """Shared logic: create Jira from message and optionally attach screenshots."""
    if not skip_trigger_check and not message_has_trigger(message):
        raise HTTPException(
            status_code=400,
            detail="Message must contain #ZProdBug or #TeamsJIRABugBot. Use skip_trigger_check=true to test without trigger.",
        )

    customer_name = (customer_name_override or "").strip() if customer_name_override else None
    if not customer_name:
        customer_name = extract_customer_name(message)

    assignee_name = extract_assignee(message, default="Aeras Alvi")
    assignee_account_id = get_user_account_id_by_name(JIRA_PROJECT, assignee_name)

    priority_name = extract_priority(message)
    priority_id = get_priority_id_by_name(priority_name) if priority_name else None

    cleaned_message = clean_message_for_jira(message)

    try:
        summary = generate_summary_only(cleaned_message)
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))

    component_id = get_default_chat_component_id(
        JIRA_PROJECT,
        [DEFAULT_CHAT_COMPONENT_NAME, "RA FE", "RA-FE"],
        fallback_id=DEFAULT_CHAT_COMPONENT_ID or None,
    )
    if not component_id:
        raise HTTPException(
            status_code=503,
            detail="Project requires a component. Set DEFAULT_CHAT_COMPONENT_ID in .env to your RA_FE component id, or add a component to the project.",
        )

    key, url = create_issue(
        summary,
        cleaned_message,
        component_id=component_id,
        priority_id=priority_id,
        assignee_account_id=assignee_account_id,
        customer_name=customer_name or "NA",
    )

    files_to_attach = []
    for f in (screenshot_files or [])[:4]:
        if f and getattr(f, "filename", None):
            content = await f.read()
            if content:
                ct = getattr(f, "content_type", None) or "application/octet-stream"
                files_to_attach.append((f.filename, content, ct))
    if files_to_attach:
        try:
            add_attachments(key, files_to_attach)
        except ValueError:
            pass

    return {
        "key": key,
        "url": url,
        "customer_name": customer_name or "NA",
        "assignee": assignee_name,
        "priority": priority_name,
    }


@app.post("/create-jira-from-chat")
async def create_jira_from_chat(request: Request):
    """
    Create a Jira from a chat message (e.g. Teams). Optional screenshots/images.
    Accepts:
      - application/json: { "message", "customer_name?", "skip_trigger_check?" }
      - multipart/form-data: message, customer_name?, skip_trigger_check?, screenshots[] (files)
    Trigger: message must contain #ZProdBug or #TeamsJIRABugBot (unless skip_trigger_check=true). Component defaults to RA_FE.
    """
    content_type = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
    message: str
    customer_name_override: str | None
    skip_trigger_check: bool
    screenshot_files: list[UploadFile] = []

    if content_type == "application/json":
        body = await request.json()
        message = (body.get("message") or "").strip()
        customer_name_override = body.get("customer_name")
        skip_trigger_check = _parse_skip_trigger(body.get("skip_trigger_check"))
    else:
        form = await request.form()
        message = (form.get("message") or "").strip()
        customer_name_override = form.get("customer_name")
        skip_trigger_check = _parse_skip_trigger(form.get("skip_trigger_check"))
        files = form.getlist("screenshots")
        if not files:
            files = form.getlist("screenshots[]")
        for f in files:
            if hasattr(f, "read") and hasattr(f, "filename"):
                screenshot_files.append(f)

    if not message:
        raise HTTPException(status_code=422, detail="message is required")

    return await _create_jira_from_chat_impl(
        message, customer_name_override, skip_trigger_check, screenshot_files
    )
