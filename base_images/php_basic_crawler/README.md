# PHP Basic Crawler Base Image

Dieses Base-Image ist für PHP-basierte Crawler gedacht.

## Inhalt

- PHP 8.2 CLI
- Cron für geplante Tasks

## Verwendung

1. Erstelle ein neues Verzeichnis für deinen Crawler
2. Kopiere deine Skripte hinein:
   - `main.php` - Hauptskript (wird beim Start einmal ausgeführt)
   - `crontab` - Cron-Konfiguration
3. Erstelle ein Dockerfile:

```dockerfile
FROM gs_crawler/php_basic_crawler:latest

# Kopiere deine Skripte
COPY main.php .
COPY crontab /etc/cron.d/mycron

# Konfiguriere Cron
RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
```

## Verfügbare Dateien

- `start_up.sh` - Startup-Script (führt main.php aus und startet cron)

## Output

- Standardpfad: `/app/output`
- Wird via Volume Mount zu `httpdocs/crawler` gemappt
