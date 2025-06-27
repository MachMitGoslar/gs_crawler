FROM python:3.13-slim

WORKDIR /app


COPY requirements.txt requirements.txt
COPY helpers.py helpers.py
COPY script.py script.py
COPY crontab /etc/cron.d/mycron

RUN apt-get update && apt-get install -y cron python3-venv \
 && chmod 0600 /etc/cron.d/mycron \
 && crontab /etc/cron.d/mycron

RUN python3 -m venv .venv
RUN pip install -r requirements.txt

CMD ["cron", "-f"]