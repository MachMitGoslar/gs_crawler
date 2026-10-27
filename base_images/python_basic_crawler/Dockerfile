FROM python:3.13-slim

# Setze Arbeitsverzeichnis
WORKDIR /app

# Installiere System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Kopiere und installiere Python-Abhängigkeiten
COPY requirements.txt .
RUN python3 -m venv .venv && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# Kopiere Helper-Dateien
COPY helpers.py .

# Scheduler als Ersatz für cron (aktiv, sobald SCHEDULE gesetzt ist)
COPY scheduler.py .

# Gemeinsames UI-Kit fuer Crawler-HTML-Seiten
COPY goslar-ui.css /app/ui-kit/goslar-ui.css
COPY goslar-ui.js /app/ui-kit/goslar-ui.js

# Kopiere und bereite Startup-Script vor
COPY start_up.sh .
RUN chmod +x start_up.sh

# Erstelle Output-Verzeichnis
RUN mkdir -p /app/output

# Standardwerte für Container
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Der Container läuft per Compose mit fremder UID ohne Home; /tmp ist dort ein tmpfs
ENV HOME=/tmp

# Entrypoint
ENTRYPOINT ["/app/start_up.sh"]
