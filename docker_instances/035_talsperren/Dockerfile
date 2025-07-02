# Verwende das offizielle Playwright-Image mit Python 3.11
FROM python:3.13-slim

WORKDIR /app

# Kopiere das Python-Skript & Crontab
COPY script.py .
COPY crontab .
COPY start_up.sh .

RUN chmod 0744 script.py

RUN apt-get update && apt-get install -y cron 
RUN apt-get install -y python3-pip 
RUN apt-get install -y firefox-esr
RUN apt-get install -y rsyslog

# Kopiere Anforderungen & installiere sie
COPY requirements.txt .
RUN python3 -m venv .venv
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Berechtigungen & Cron einrichten
RUN chmod 0600 crontab \
    && mkdir -p /var/log/cron
RUN crontab crontab
RUN touch /var/log/cron/python.log

RUN chmod +x start_up.sh

# Starte Cron + zeige Logs
#CMD ["cron", "-f", ">> /proc/1/fd/1"] 
ENTRYPOINT [ "/app/start_up.sh" ]