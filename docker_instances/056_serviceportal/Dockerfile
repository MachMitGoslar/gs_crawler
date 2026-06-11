# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 056_serviceportal_index.html .
COPY 056_serviceportal_termin.html .
COPY crontab /etc/cron.d/mycron



# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
