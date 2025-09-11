# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_flask_monitor:latest

# Kopiere container-spezifische Dateien
COPY app.py .
COPY templates/ templates/
COPY events.json .

# Port ist bereits im Base-Image exponiert
