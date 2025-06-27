FROM python:3.13-slim

WORKDIR /app


COPY requirements.txt requirements.txt
COPY helpers.py helpers.py
COPY script.py script.py
COPY crontab /etc/cron.d/mycron
COPY start_up.sh .

RUN apt-get update && apt-get install -y cron python3-venv \
 && chmod 0600 /etc/cron.d/mycron \
 && crontab /etc/cron.d/mycron

RUN python3 -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

RUN chmod +x start_up.sh

# Starte Cron + zeige Logs
#CMD ["cron", "-f", ">> /proc/1/fd/1"] 
ENTRYPOINT [ "/app/start_up.sh" ]