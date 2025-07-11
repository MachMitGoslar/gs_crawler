# Python Basic Crawler Base Image

Dieses Base-Image ist für Standard-Python-Crawler gedacht, die mit requests, BeautifulSoup und anderen Standard-Bibliotheken arbeiten.

## Inhalt

- Python 3.13 mit venv
- Cron für geplante Tasks
- Standard-Crawler-Bibliotheken:
  - requests
  - beautifulsoup4
  - pillow (für Bildverarbeitung)
  - lxml (für XML-Parsing)
  - Django (für komplexere Anwendungen)

## Verwendung

1. Erstelle ein neues Verzeichnis für deinen Crawler
2. Kopiere deine Skripte hinein:
   - `script.py` - Hauptskript (wird beim Start einmal ausgeführt)
   - `crontab` - Cron-Konfiguration
3. Erstelle ein Dockerfile:

```dockerfile
FROM gs_crawler/python_basic_crawler:latest

# Kopiere deine Skripte
COPY script.py .
COPY crontab /etc/cron.d/mycron

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
```

## Verfügbare Dateien

- `helpers.py` - Gemeinsame Helper-Funktionen
- `start_up.sh` - Startup-Script (führt script.py aus und startet cron)
- `.venv/` - Python Virtual Environment mit allen Abhängigkeiten

## Output

- Standardpfad: `/app/output`
- Wird via Volume Mount zu `httpdocs/crawler` gemappt
