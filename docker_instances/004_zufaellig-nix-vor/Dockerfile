# Das Python-Basis-Image enthaelt auch das gemeinsame UI-Kit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 004_zufaellig-nix-vor-alle.json .
COPY 004_zufaellig-nix-vor.html .
COPY 004_zufaellig-nix-vor-alle.html .

RUN mkdir -p /app/output

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image
ENV SCHEDULE="0 7 * * *"
