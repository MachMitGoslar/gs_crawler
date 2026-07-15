# Migriert zu Base-Image mit gemeinsamem UI-Kit
FROM ghcr.io/machmitgoslar/gs_crawler_python_ui_kit_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 042_freiwilligenagentur_index.html .
COPY crontab /etc/cron.d/mycron



# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
