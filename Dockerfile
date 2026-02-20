# Build and run Jira Team Utility (FastAPI)
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY app.py config.py jira_client.py llm_client.py chat_utils.py prompts.py ./
COPY templates/ templates/
COPY static/ static/

# Non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
