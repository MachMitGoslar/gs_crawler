# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_python_selenium_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY crontab /etc/cron.d/mycron
COPY mowas.svg /output/045_naturgefahren/mowas.svg

# helpers.py wird vom Base-Image bereitgestellt

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
