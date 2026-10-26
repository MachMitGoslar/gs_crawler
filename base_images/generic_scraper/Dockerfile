# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Copy and install Python dependencies with cache mount
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# Copy the generic scraper engine
COPY scraper.py .
COPY config_loader.py .
COPY scheduler.py .
COPY run_scheduler.py .
COPY start_up.sh .
RUN chmod +x start_up.sh

# Create output directory
RUN mkdir -p /app/output /app/configs

# Environment defaults
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
# Der Container läuft per Compose mit fremder UID ohne Home; /tmp ist dort ein tmpfs
ENV HOME=/tmp
ENV CONFIG_DIR=/app/configs
ENV OUTPUT_DIR=/app/output

# Entrypoint
ENTRYPOINT ["/app/start_up.sh"]
