#!/bin/sh
cd /app

# Mit SCHEDULE: Scheduler führt script.py nach Cron-Ausdruck aus (ersetzt cron).
# Ohne SCHEDULE: script.py läuft einmal im Vordergrund (z. B. eigene Endlosschleife).
if [ -n "$SCHEDULE" ]; then
    echo "Starting scheduler (SCHEDULE=$SCHEDULE)..."
    exec .venv/bin/python3 scheduler.py
fi

echo "Running script.py..."
exec .venv/bin/python3 script.py
