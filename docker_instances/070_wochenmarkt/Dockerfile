FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir requests

COPY script.py .
COPY crontab /etc/cron.d/mycron
RUN chmod 0600 /etc/cron.d/mycron && crontab /etc/cron.d/mycron

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/output

CMD ["sh", "-c", "python script.py && cron -f"]
