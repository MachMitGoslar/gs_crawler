#!/bin/bash
echo "Starting up..."
cd /app
.venv/bin/python3 script.py >> /proc/1/fd/1
cron -f
