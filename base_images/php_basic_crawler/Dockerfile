FROM php:8.2-cli

# Setze Arbeitsverzeichnis
WORKDIR /app

# Installiere System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Kopiere und bereite Startup-Script vor
COPY start_up.sh .
RUN chmod +x start_up.sh

# Erstelle Output-Verzeichnis
RUN mkdir -p /app/output

# Standard-Cron-Einstellungen
RUN mkdir -p /var/log/cron && \
    touch /var/log/cron/php.log

# Entrypoint
ENTRYPOINT ["/app/start_up.sh"]
