# Das Python-Basis-Image enthaelt auch das gemeinsame UI-Kit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 042_freiwilligenagentur_index.html .
COPY 042_freiwilligenagentur_detail.html .

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image
ENV SCHEDULE="0 2,14 * * *"
