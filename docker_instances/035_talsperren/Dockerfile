# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# matplotlib für die Füllstand-Gauges (im Base-Image nicht enthalten)
RUN .venv/bin/pip install --no-cache-dir matplotlib==3.10.3

# Kopiere container-spezifische Dateien
COPY script.py .
COPY crontab /etc/cron.d/mycron

# helpers.py wird vom Base-Image bereitgestellt

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
