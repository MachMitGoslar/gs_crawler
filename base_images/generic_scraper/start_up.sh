#!/bin/sh
echo "Starting Generic Scraper..."
cd /app

# Generate crontab from config files
echo "Generating crontab from configs..."
python3 -c "from config_loader import generate_crontab; generate_crontab()"

# Run all scrapers once on startup if RUN_ON_START is set
if [ "${RUN_ON_START:-true}" = "true" ]; then
    echo "Running initial scrape for all configs..."
    for config in /app/configs/*.yaml; do
        if [ -f "$config" ]; then
            echo "Running scraper for: $config"
            python3 scraper.py "$config" >> /proc/1/fd/1 2>&1
        fi
    done
fi

# Start cron daemon
echo "Starting cron daemon..."
cron -f
