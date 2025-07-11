# Migriert zu Base-Image für bessere Wartbarkeit
FROM gs_crawler/php_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY fepa_fetcher.php main.php
COPY crontab /etc/cron.d/mycron

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
