FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY api_clients.py .
COPY config.py .
COPY jobs_logic.py .
COPY script.py .
COPY refresh_jobs.py .
COPY jobs.html .
COPY jobs.css .
COPY jobs.js .
COPY crontab /etc/cron.d/mycron

RUN chmod 0600 /etc/cron.d/mycron \
    && crontab /etc/cron.d/mycron \
    && mkdir -p /app/output

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
