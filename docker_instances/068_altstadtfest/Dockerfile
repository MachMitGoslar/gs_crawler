FROM python:3.13-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Flask-spezifische Abhängigkeiten
RUN pip install --no-cache-dir flask

# Script und Konfiguration kopieren
COPY altstadtfest_aktuell.py .
COPY events.json .
RUN mkdir templates
COPY templates/test.html templates/

# Port freigeben
EXPOSE 5010

# Environment Variables für Flask
ENV FLASK_APP=altstadtfest_aktuell.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5010

# Startkommando
CMD ["python", "altstadtfest_aktuell.py"]
