FROM php:8.2-cli

WORKDIR /app


COPY fepa_fetcher.php fepa_fetcher.php
COPY crontab /etc/cron.d/mycron
COPY start_up.sh .

RUN apt-get update && apt-get install -y cron \
 && chmod 0600 /etc/cron.d/mycron \
 && crontab /etc/cron.d/mycron


RUN chmod +x start_up.sh

# Starte Cron + zeige Logs
#CMD ["cron", "-f", ">> /proc/1/fd/1"] 
ENTRYPOINT [ "/app/start_up.sh" ]