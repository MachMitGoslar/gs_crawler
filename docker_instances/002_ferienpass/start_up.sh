#!/bin/bash
echo "Starting up..."
cd /app
php fepa_fetcher.php >> /proc/1/fd/1
cron -f