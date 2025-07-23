# Migriert zu Base-Image für bessere Wartbarkeit
FROM gs_crawler/flask_monitor:latest

# Kopiere container-spezifische Dateien
COPY app.py .
COPY templates/ templates/

# Port ist bereits im Base-Image exponiert
