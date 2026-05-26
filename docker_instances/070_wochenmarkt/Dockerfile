FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir requests

COPY script.py .
COPY crontab /etc/cron.d/mycron
RUN chmod 0600 /etc/cron.d/mycron && crontab /etc/cron.d/mycron

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/output

# Dump env vars for cron, copy static HTML, run once, then start cron
CMD ["sh", "-c", "printenv | sed 's/^/export /' > /app/env.sh && python script.py && cron -f"]
