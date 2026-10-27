# Das Python-Basis-Image enthaelt auch das gemeinsame UI-Kit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 056_serviceportal_index.html .
COPY 056_serviceportal_termin.html .
COPY 056_serviceportal_image.png .

RUN mkdir -p /app/output

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image
ENV SCHEDULE="0 9 * * *"
