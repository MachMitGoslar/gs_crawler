# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_flask_monitor:latest

# Zusätzliche Abhängigkeit fürs Parsen des Altstadtfest-Programms (im
# Base-Image nicht enthalten)
RUN .venv/bin/pip install --no-cache-dir beautifulsoup4==4.13.4

# Kopiere container-spezifische Dateien
COPY app.py .
COPY crawler.py .
COPY templates/ templates/
COPY data.json .

# Port ist bereits im Base-Image exponiert
