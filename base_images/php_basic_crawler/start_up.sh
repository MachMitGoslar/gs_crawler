#!/bin/bash
echo "Starting PHP Basic Crawler..."
cd /app

# Prüfe ob ein main.php existiert
if [ -f "main.php" ]; then
    echo "Running main.php once..."
    php main.php >> /proc/1/fd/1
else
    echo "No main.php found, skipping initial run."
fi

# Starte Cron für geplante Tasks
echo "Starting cron daemon..."
cron -f
