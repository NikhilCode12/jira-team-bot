# Deploy to Render (for Teams testing)

Deploy this app to Render so Power Automate can call your API from the internet (no ngrok needed).

## 1. Get your code on a repo Render can see

Render connects to **GitHub** or **GitLab.com**. If your repo is only on **gitlab.infoedge.com**:

- **Option A:** Push this project to a **GitHub** repo (public or private). In GitHub: New repo → push the `jira-feedback-to-issue` folder (or mirror from GitLab).
- **Option B:** If your org uses **GitLab.com** (not infoedge.com), connect that repo instead.

## 2. Create a Render account and Web Service

1. Go to **[render.com](https://render.com)** and sign up (or log in).
2. **Dashboard** → **New** → **Web Service**.
3. **Connect a repository:**
   - Connect **GitHub** (or GitLab) if not already connected.
   - Select the repo that contains this app (e.g. `jira-team-utility` or the repo that has the `jira-feedback-to-issue` code).
4. **Root Directory:** If the app is in a subfolder (e.g. `jira-feedback-to-issue`), set **Root Directory** to `jira-feedback-to-issue`. If the repo root *is* the app, leave it blank.
5. **Settings:**
   - **Name:** `jira-team-utility` (or any name).
   - **Region:** Choose the closest to you.
   - **Branch:** `master` (or your default branch).
   - **Runtime:** **Python 3**.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`

## 3. Add environment variables (secrets)

In the same Web Service → **Environment** (left sidebar):

Add these (use **Add Environment Variable**; do **not** commit real values to Git):

| Key | Value | Required |
|-----|--------|----------|
| `JIRA_BASE_URL` | e.g. `https://your-domain.atlassian.net` | Yes |
| `JIRA_EMAIL` | Your Jira account email | Yes |
| `JIRA_API_TOKEN` | Jira API token | Yes |
| `GROQ_API_KEY` | Groq API key | Yes |
| `JIRA_PROJECT` | e.g. `ZRA` | Yes (or default in code) |
| `JIRA_EPIC_FIELD_ID` | Optional; leave blank if not used | No |
| `DEFAULT_CHAT_COMPONENT_NAME` | e.g. `RA_FE` | No |
| `DEFAULT_CHAT_COMPONENT_ID` | Optional component id | No |

Save.

## 4. Deploy

1. Click **Create Web Service** (or **Save** if you already created it).
2. Render will build and deploy. Wait until status is **Live** (green).
3. Your app URL will be like: `https://jira-team-utility-xxxx.onrender.com`

## 5. Use this URL in Power Automate (Teams)

In your Power Automate flow, in the **HTTP** action:

- **URI:** `https://jira-team-utility-xxxx.onrender.com/create-jira-from-chat`  
  (replace with your actual Render URL from the dashboard.)

Then send a message with `#TeamsJIRABugBot` in Teams to test.

---

**Note:** On the free tier, the service may **sleep** after ~15 minutes of no traffic. The first request after sleep can take 30–60 seconds; then it responds normally.
