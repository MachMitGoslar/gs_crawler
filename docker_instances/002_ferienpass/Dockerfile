FROM php:8.2-cli

WORKDIR /app


COPY fepa_fetcher.php fepa_fetcher.php
COPY crontab /etc/cron.d/mycron

RUN apt-get update && apt-get install -y cron \
 && chmod 0644 /etc/cron.d/mycron \
 && crontab /etc/cron.d/mycron


CMD ["cron", "-f"]