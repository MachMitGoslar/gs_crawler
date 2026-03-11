FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir requests

COPY script.py .
COPY 070_wochenmarkt_index.html  /app/static/070_wochenmarkt_index.html
COPY 070_wochenmarkt_detail.html /app/static/070_wochenmarkt_detail.html
COPY crontab /etc/cron.d/mycron
RUN chmod 0600 /etc/cron.d/mycron && crontab /etc/cron.d/mycron

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /app/output

# Copy static HTML to the output volume, then run the script once, then start cron
CMD ["sh", "-c", "cp /app/static/*.html /app/output/ && python script.py && cron -f"]
