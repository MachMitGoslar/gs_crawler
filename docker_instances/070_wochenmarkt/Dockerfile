# Migriert zu Base-Image für bessere Wartbarkeit (Scheduler statt cron)
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

COPY script.py .

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image
ENV SCHEDULE="*/10 * * * *"
