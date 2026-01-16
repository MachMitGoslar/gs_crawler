# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies with cache mount
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies with cache mount
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy the generic scraper engine
COPY scraper.py .
COPY config_loader.py .
COPY start_up.sh .
RUN chmod +x start_up.sh

# Create output directory
RUN mkdir -p /app/output /app/configs

# Standard cron settings
RUN mkdir -p /var/log/cron && \
    touch /var/log/cron/scraper.log

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CONFIG_DIR=/app/configs
ENV OUTPUT_DIR=/app/output

# Entrypoint
ENTRYPOINT ["/app/start_up.sh"]
