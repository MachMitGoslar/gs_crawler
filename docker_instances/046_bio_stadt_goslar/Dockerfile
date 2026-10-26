# Das Python-Basis-Image enthaelt auch das gemeinsame UI-Kit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 046_bio_stadt_goslar_index.html .
COPY 046_bio_stadt_goslar_detail.html .

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image
ENV SCHEDULE="0 2,14 * * *"
