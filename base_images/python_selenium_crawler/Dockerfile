FROM python:3.13-slim

# Setze Arbeitsverzeichnis
WORKDIR /app

# Installiere System-Abhängigkeiten inklusive Firefox für Selenium
RUN apt-get update && apt-get install -y \
    cron \
    python3-venv \
    firefox-esr \
    rsyslog \
    && rm -rf /var/lib/apt/lists/*

# Kopiere und installiere Python-Abhängigkeiten
COPY requirements.txt .
RUN python3 -m venv .venv && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# Kopiere Helper-Dateien
COPY helpers.py .

# Kopiere und bereite Startup-Script vor
COPY start_up.sh .
RUN chmod +x start_up.sh

# Erstelle Output-Verzeichnis
RUN mkdir -p /app/output

# Standard-Cron-Einstellungen
RUN mkdir -p /var/log/cron && \
    touch /var/log/cron/python.log

# Standardwerte für Container
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Entrypoint
ENTRYPOINT ["/app/start_up.sh"]
