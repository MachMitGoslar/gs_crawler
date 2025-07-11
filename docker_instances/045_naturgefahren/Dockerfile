# Migriert zu Base-Image für bessere Wartbarkeit
FROM gs_crawler/python_selenium_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY crontab /etc/cron.d/mycron

# helpers.py wird vom Base-Image bereitgestellt

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
