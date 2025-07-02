FROM python:3.13-slim

WORKDIR /app

# Docker CLI installieren
RUN apt-get update && apt-get install -y \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
COPY app.py app.py
COPY templates/ templates/

RUN python3 -m venv .venv
RUN .venv/bin/pip install -r requirements.txt

EXPOSE 5000

CMD [".venv/bin/python3", "app.py"]
