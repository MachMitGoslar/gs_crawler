FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron curl \
    && rm -rf /var/lib/apt/lists/*

COPY api_clients.py .
COPY config.py .
COPY jobs_logic.py .
COPY request_handler.py .
COPY script.py .
COPY refresh_jobs.py .
COPY jobs.html .
COPY job_detail.html .
COPY crontab /etc/cron.d/mycron

RUN chmod 0600 /etc/cron.d/mycron \
    && crontab /etc/cron.d/mycron \
    && mkdir -p /app/output

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["sh", "-c", "printenv | sed 's/^/export /' > /app/env.sh && python3 /app/refresh_jobs.py && python3 /app/script.py & cron -f"]
