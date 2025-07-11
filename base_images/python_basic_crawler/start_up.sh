#!/bin/bash
echo "Starting Python Basic Crawler..."
cd /app

# Prüfe ob ein script.py existiert
if [ -f "script.py" ]; then
    echo "Running script.py once..."
    .venv/bin/python3 script.py >> /proc/1/fd/1
else
    echo "No script.py found, skipping initial run."
fi

# Starte Cron für geplante Tasks
echo "Starting cron daemon..."
cron -f
