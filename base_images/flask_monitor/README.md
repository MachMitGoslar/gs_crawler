# Flask Monitor Base Image

Dieses Base-Image ist für Flask-basierte Monitoring-Anwendungen gedacht.

## Inhalt

- Python 3.13 mit venv
- Flask-Abhängigkeiten
- Jinja2 für Templates
- requests für API-Calls

## Verwendung

1. Erstelle ein neues Verzeichnis für deine Flask-App
2. Kopiere deine Dateien hinein:
   - `app.py` - Flask-Anwendung
   - `templates/` - Jinja2-Templates
3. Erstelle ein Dockerfile:

```dockerfile
FROM gs_crawler/flask_monitor:latest

# Kopiere deine Flask-App
COPY app.py .
COPY templates/ templates/

# Exponiere Port (optional, schon in Base-Image)
EXPOSE 5000
```

## Verfügbare Bibliotheken

- Flask 3.0.0
- Jinja2 3.1.2
- requests 2.32.4

## Output

- Standardpfad: `/app/output`
- Wird via Volume Mount zu `httpdocs/crawler` gemappt

## Port

- Standard-Port: 5000
