# Python Selenium Crawler Base Image

Dieses Base-Image ist für erweiterte Python-Crawler gedacht, die Selenium für Browser-Automatisierung benötigen.

## Inhalt

- Python 3.13 mit venv
- Firefox ESR für Selenium
- Cron für geplante Tasks
- Erweiterte Crawler-Bibliotheken:
  - Alle Standard-Bibliotheken (requests, beautifulsoup4, etc.)
  - selenium
  - webdriver-manager
  - matplotlib (für Datenvisualisierung)
  - numpy (für Datenverarbeitung)

## Verwendung

1. Erstelle ein neues Verzeichnis für deinen Crawler
2. Kopiere deine Skripte hinein:
   - `script.py` - Hauptskript (wird beim Start einmal ausgeführt)
   - `crontab` - Cron-Konfiguration
3. Erstelle ein Dockerfile:

```dockerfile
FROM gs_crawler/python_selenium_crawler:latest

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

## Selenium-Konfiguration

Das Image enthält bereits Firefox ESR. Verwende in deinem Code:

```python
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
options.add_argument('--headless')
driver = webdriver.Firefox(options=options)
```
