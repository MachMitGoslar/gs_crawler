# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 080_bereitschaftsdienste_card.png .
COPY 080_bereitschaftsdienste_index.html .
COPY 080_bereitschaftsdienste_medizinisch.html .
COPY 080_bereitschaftsdienste_sicherheit.html .
COPY 080_bereitschaftsdienste_staedtisch.html .
COPY csm__bkf5951-bearbeitet_65e837eae0.jpg .
COPY crontab /etc/cron.d/mycron

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron && \
    mkdir -p /app/output
