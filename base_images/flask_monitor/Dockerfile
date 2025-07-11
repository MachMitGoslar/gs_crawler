FROM python:3.13-slim

# Setze Arbeitsverzeichnis
WORKDIR /app

# Installiere System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Kopiere und installiere Python-Abhängigkeiten
COPY requirements.txt .
RUN python3 -m venv .venv && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# Erstelle Output-Verzeichnis
RUN mkdir -p /app/output

# Standardwerte für Container
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Exponiere Port 5000
EXPOSE 5000

# Standard-Entrypoint für Flask-App
CMD [".venv/bin/python3", "app.py"]
