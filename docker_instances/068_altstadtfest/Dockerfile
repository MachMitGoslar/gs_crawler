# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_flask_monitor:latest

# Zusätzliche Abhängigkeiten fürs Parsen des Altstadtfest-Programms und für
# korrekte Zeitzonenberechnung (im Base-Image nicht enthalten; der
# Produktionsserver läuft in GMT, das Base-Image hat keine System-Tzdata)
RUN .venv/bin/pip install --no-cache-dir beautifulsoup4==4.13.4 tzdata==2025.2

# Kopiere container-spezifische Dateien
COPY app.py .
COPY crawler.py .
COPY templates/ templates/
COPY data.json .

# Port ist bereits im Base-Image exponiert
