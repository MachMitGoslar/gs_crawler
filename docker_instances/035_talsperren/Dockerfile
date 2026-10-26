# Migriert zu Base-Image für bessere Wartbarkeit
FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Zusätzliche Abhängigkeit: matplotlib für die Füllstand-Gauges (im Base-Image nicht enthalten)
COPY requirements.txt .
RUN .venv/bin/pip install --no-cache-dir -r requirements.txt

# Kopiere container-spezifische Dateien
COPY script.py .

# helpers.py wird vom Base-Image bereitgestellt

# Takt (Cron-Ausdruck, UTC) für den Scheduler im Base-Image: stündlich
ENV SCHEDULE="0 * * * *"
# matplotlib braucht ein beschreibbares Cache-Verzeichnis (Container läuft ohne Home/Root)
ENV MPLCONFIGDIR=/tmp/matplotlib
