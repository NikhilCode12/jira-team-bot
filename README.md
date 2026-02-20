# Jira Team Utility (Feedback to Issue)

Create Jira bugs from product feedback or from Teams chat (#TeamsJIRABugBot) using a free LLM (Groq) and Jira Cloud API.

## Setup

1. Create a `.env` file in the project root with:
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

**Do not commit `.env`** — it contains secrets.

---

## Deploy (GitLab)

Repo: **gitlab.infoedge.com/nikhil.s4/jira-team-utility**

### Option 1: GitLab CI/CD (build image on push)

- Push to `master` runs the pipeline in `.gitlab-ci.yml`: builds a Docker image and pushes it to **GitLab Container Registry** for this project.
- In GitLab: **CI/CD → Pipelines** to see runs; **Packages & Registries → Container Registry** for the image.

### Option 2: Run the Docker image anywhere

Build and run locally or on a server:

```bash
docker build -t jira-team-utility .
docker run -p 8000:8000 --env-file .env jira-team-utility
```

Or pull from GitLab Container Registry (after enabling it and one successful pipeline):

```bash
docker login gitlab.infoedge.com
docker pull gitlab.infoedge.com/nikhil.s4/jira-team-utility:latest
docker run -p 8000:8000 -e JIRA_BASE_URL=... -e JIRA_EMAIL=... -e JIRA_API_TOKEN=... -e GROQ_API_KEY=... jira-team-utility:latest
```

Set all required env vars via `-e` or `--env-file` (never commit the file).

### Option 3: Deploy to your own server / Kubernetes

- **Server**: SSH to the host, clone the repo, set `.env`, run `docker run` or `uvicorn` behind a reverse proxy (nginx/Caddy).
- **Kubernetes**: Use the image from GitLab Registry; create a Deployment and Service; put secrets in a Secret or your GitLab CI variables and inject them into the pod.
- **Azure / AWS / GCP**: Use App Service, ECS, Cloud Run, etc., and point the service at the GitLab image or connect the repo for auto-deploy.

Enable **Container Registry** in the GitLab project (**Settings → General → Visibility**) if the build job fails with registry errors.

### Deploy to Render (for Teams testing)

To get a public URL so Power Automate can call your app (no ngrok): see **[DEPLOY_RENDER.md](DEPLOY_RENDER.md)** for step-by-step. You’ll need the repo on **GitHub** or **GitLab.com** for Render to connect; then add env vars in Render and use the given URL in the flow.
