# Das Python-Basis-Image enthaelt auch das gemeinsame UI-Kit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Kopiere container-spezifische Dateien
COPY script.py .
COPY 080_bereitschaftsdienste_card.png .
COPY 080_bereitschaftsdienste_index.html .
COPY 080_bereitschaftsdienste_medizinisch.html .
COPY 080_bereitschaftsdienste_sicherheit.html .
COPY 080_bereitschaftsdienste_staedtisch.html .
COPY csm__bkf5951-bearbeitet_65e837eae0.jpg .

RUN mkdir -p /app/output

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image
ENV SCHEDULE="*/15 * * * *"
