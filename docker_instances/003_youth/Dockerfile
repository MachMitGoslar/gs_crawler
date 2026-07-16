FROM ghcr.io/machmitgoslar/gs_crawler_python_ui_kit_crawler:latest

COPY script.py .
COPY 003_youth_freizeitkarte.html .
COPY Freizeitkarte.png .
COPY JUZ.png .
COPY Ferienpass.png .
COPY Veranstaltungen.png .
COPY crontab /etc/cron.d/mycron

RUN chmod 0600 /etc/cron.d/mycron \
    && crontab /etc/cron.d/mycron \
    && mkdir -p /app/output

ENV PYTHONUNBUFFERED=1
