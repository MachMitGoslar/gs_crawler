# Python Basic Crawler Base Image

Dieses Base-Image ist für Standard-Python-Crawler gedacht, die mit requests, BeautifulSoup und anderen Standard-Bibliotheken arbeiten.

## Inhalt

- Python 3.13 mit venv
- Scheduler für geplante Tasks (statt cron, läuft ohne Root)
- Standard-Crawler-Bibliotheken:
  - requests
  - beautifulsoup4
  - pillow (für Bildverarbeitung)
  - lxml (für XML-Parsing)
  - Django (für komplexere Anwendungen)

## Verwendung

1. Erstelle ein neues Verzeichnis für deinen Crawler
2. Kopiere deine Skripte hinein:
   - `script.py` - Hauptskript (wird beim Start einmal und danach nach `SCHEDULE` ausgeführt)
3. Erstelle ein Dockerfile:

```dockerfile
FROM gs_crawler/python_basic_crawler:latest

# Kopiere deine Skripte
COPY script.py .

# Takt als Cron-Ausdruck in UTC, mehrere Ausdrücke mit ';' trennen
ENV SCHEDULE="0 * * * *"
```

### Scheduler

`scheduler.py` ersetzt den cron-Daemon. Er läuft als PID 1 ohne Root-Rechte, schreibt direkt nach
stdout (`docker logs`) und führt `script.py` nacheinander aus (kein paralleler Doppellauf).

| Variable | Bedeutung | Standard |
|---|---|---|
| `SCHEDULE` | Cron-Ausdruck mit 5 Feldern, mehrere mit `;` | – |
| `SCRIPT` | Skript, das ausgeführt wird | `script.py` |
| `RUN_ON_START` | einmal direkt beim Start ausführen (ersetzt `@reboot`) | `true` |
| `SCRIPT_TIMEOUT` | Sekunden, nach denen ein hängender Lauf beendet wird | `1800` |

Ohne `SCHEDULE` startet der Container `script.py` einmal im Vordergrund (für Skripte mit eigener
Endlosschleife, z. B. `033_goslar24-7`).

## Verfügbare Dateien

- `helpers.py` - Gemeinsame Helper-Funktionen
- `scheduler.py` - Scheduler (siehe oben)
- `start_up.sh` - Startup-Script (startet den Scheduler oder script.py)
- `ui-kit/goslar-ui.css` - Gemeinsame Styles für Crawler-HTML-Seiten
- `ui-kit/goslar-ui.js` - Gemeinsames Such-, Filter- und Scroll-Verhalten
- `.venv/` - Python Virtual Environment mit allen Abhängigkeiten

## Output

- Standardpfad: `/app/output`
- Wird via Volume Mount zum eigenen Ordner `httpdocs/crawler/<crawler-id>` gemappt (öffentlich unter `/crawler/<crawler-id>/`)
