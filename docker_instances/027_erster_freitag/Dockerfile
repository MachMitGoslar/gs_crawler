# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
ADD script.py .

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image
ENV SCHEDULE="0 9 * * *"
