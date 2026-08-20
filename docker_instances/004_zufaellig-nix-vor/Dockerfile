# Das Python-Basis-Image enthaelt auch das gemeinsame UI-Kit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 004_zufaellig-nix-vor-alle.json .
COPY 004_zufaellig-nix-vor.html .
COPY 004_zufaellig-nix-vor-alle.html .
COPY crontab /etc/cron.d/mycron



# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron && \
    mkdir -p /app/output
