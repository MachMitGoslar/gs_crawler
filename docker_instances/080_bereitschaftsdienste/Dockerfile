# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 080_bereitschaftsdienste_index.html .
COPY 080_bereitschaftsdienste_medizinisch.html .
COPY crontab /etc/cron.d/mycron

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron && \
    mkdir -p /app/output
