# Base-Images für GS Crawler System

Dieses Verzeichnis enthält wiederverwendbare Base-Images, die die Redundanz in den Container-Konfigurationen drastisch reduzieren.

## 🎯 Vorteile der Base-Images

### Vorher (Probleme):
- **Redundanz:** Jeder Container hatte identische Dockerfile-Strukturen
- **Wartbarkeit:** Änderungen mussten in 20+ Dockerfiles repliziert werden
- **Größe:** Jeder Container installierte dieselben Dependencies
- **Konsistenz:** Unterschiedliche Python-/PHP-Versionen zwischen Containern
- **Build-Zeit:** Lange Build-Zeiten durch redundante Installationen

### Nachher (Vorteile):
- **DRY-Prinzip:** Ein Base-Image für ähnliche Container-Typen
- **Einfache Wartung:** Änderungen nur in Base-Images nötig
- **Kleinere Images:** Shared Layers reduzieren Speicherverbrauch
- **Konsistenz:** Einheitliche Versionen und Konfigurationen
- **Schnelle Builds:** Base-Images werden gecacht und wiederverwendet

## 🏗️ Verfügbare Base-Images

### 1. `gs_crawler/python_basic_crawler`
**Für:** Standard Python-Crawler mit requests, BeautifulSoup, etc.  
**Verwendet von:** 19 Container (80% der Crawler)  
**Reduziert:** ~750 Zeilen redundanten Code  

**Enthält:**
- Python 3.13 + venv
- requests, beautifulsoup4, pillow, lxml
- Cron-Daemon
- Gemeinsame Helper-Funktionen

### 2. `gs_crawler/python_selenium_crawler`
**Für:** Erweiterte Crawler mit Browser-Automatisierung  
**Verwendet von:** 2 Container (naturgefahren, talsperren)  
**Reduziert:** ~100 Zeilen redundanten Code  

**Enthält:**
- Alles von python_basic_crawler
- Firefox ESR + Selenium WebDriver
- matplotlib, numpy für Datenverarbeitung

### 3. `gs_crawler/php_basic_crawler`
**Für:** PHP-basierte Crawler  
**Verwendet von:** 1 Container (ferienpass)  
**Reduziert:** ~50 Zeilen redundanten Code  

**Enthält:**
- PHP 8.2 CLI
- Cron-Daemon

### 4. `gs_crawler/flask_monitor`
**Für:** Flask-basierte Monitoring-Anwendungen  
**Verwendet von:** 1 Container (health_monitor)  
**Reduziert:** ~30 Zeilen redundanten Code  

**Enthält:**
- Python 3.13 + venv
- Flask, Jinja2, requests

## 🚀 Verwendung

### 1. Base-Images bauen
```bash
# Alle Base-Images auf einmal bauen
./base_images/build_all.sh

# Oder einzeln bauen
cd base_images/python_basic_crawler
docker build -t gs_crawler/python_basic_crawler:latest .
```

### 2. Bestehende Container migrieren
```bash
# Automatische Migration aller Container
./migrate_to_base_images.sh

# Manuelle Migration eines Containers
cd docker_instances/001_senioren
# Ersetze Dockerfile-Inhalt mit:
```

```dockerfile
FROM gs_crawler/python_basic_crawler:latest

COPY script.py .
COPY crontab /etc/cron.d/mycron

RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
```

### 3. Neuen Container erstellen
```bash
# Erstelle neues Container-Verzeichnis
mkdir docker_instances/999_new_crawler

# Erstelle Dockerfile
cat > docker_instances/999_new_crawler/Dockerfile << EOF
FROM gs_crawler/python_basic_crawler:latest

COPY script.py .
COPY crontab /etc/cron.d/mycron

RUN chmod 0600 /etc/cron.d/mycron && \
    crontab /etc/cron.d/mycron
EOF

# Erstelle dein Crawler-Script
cat > docker_instances/999_new_crawler/script.py << EOF
import requests
from helpers import ensure_directory_exists
import os

# Output-Pfad (helpers.py ist im Base-Image verfügbar)
output_path = os.path.join("/app/output", "999_new_crawler.json")
ensure_directory_exists(output_path)

# Dein Crawler-Code hier...
EOF

# Erstelle Crontab
echo "0 */6 * * * cd /app && .venv/bin/python3 script.py" > docker_instances/999_new_crawler/crontab
```

## 📊 Statistiken & Einsparungen

### Reduzierte Redundanz:
- **Dockerfile-Zeilen:** Von ~1200 auf ~300 (75% Reduktion)
- **requirements.txt Dateien:** Von 23 auf 4 (83% Reduktion)
- **start_up.sh Dateien:** Von 23 auf 4 (83% Reduktion)
- **helpers.py Dateien:** Von 15 auf 2 (87% Reduktion)

### Build-Performance:
- **Base-Image Build:** ~5-10 Minuten (einmalig)
- **Container Build:** ~30 Sekunden (vorher: 2-3 Minuten)
- **Parallele Builds:** Möglich durch shared layers
- **Docker Cache:** Effizientere Nutzung

### Wartbarkeit:
- **Dependency Updates:** 1 Datei statt 20+
- **Security Patches:** Automatisch für alle Container
- **Neue Features:** Zentral in Base-Images
- **Testing:** Einheitliche Testumgebung

## 🔧 Entwickler-Workflow

### Dependency hinzufügen:
```bash
# 1. Bearbeite Base-Image requirements.txt
echo "new-package==1.0.0" >> base_images/python_basic_crawler/requirements.txt

# 2. Rebuild Base-Image
cd base_images/python_basic_crawler
docker build -t gs_crawler/python_basic_crawler:latest .

# 3. Rebuild affected containers
docker-compose build
```

### Debugging:
```bash
# Interaktive Shell im Base-Image
docker run -it gs_crawler/python_basic_crawler:latest bash

# Container-spezifische Logs
docker-compose logs gs_compiler_001_senioren
```

## 🎛️ Konfiguration

### Environment Variables:
Alle Base-Images setzen:
- `PYTHONUNBUFFERED=1` (für Python-Images)
- `PYTHONDONTWRITEBYTECODE=1` (für Python-Images)

### Ports:
- Python/PHP Crawler: Kein Port (reine Cron-Jobs)
- Flask Monitor: Port 5000 exponiert

### Volumes:
- Standard-Output: `/app/output`
- Wird gemappt zu: `./httpdocs/crawler`

## 🔄 Migration bestehender Container

Das `migrate_to_base_images.sh` Script führt automatisch folgende Aktionen aus:

1. **Backup:** Erstellt `.backup` Dateien der ursprünglichen Dockerfiles
2. **Cleanup:** Entfernt redundante Dateien (requirements.txt, start_up.sh, helpers.py)
3. **Update:** Erstellt neue, minimale Dockerfiles basierend auf Base-Images
4. **Validation:** Überprüft Container-Typen und wählt passende Base-Images

## 📚 Weitere Informationen

- **Base-Image Details:** Siehe README.md in jeweiligen Unterverzeichnissen
- **Container-Übersicht:** `CONTAINER_OVERVIEW.md`
- **GitHub Actions:** Werden automatisch angepasst für neue Struktur
- **Troubleshooting:** Prüfe `docker images` für verfügbare Base-Images

---

**Nächste Schritte:**
1. `./base_images/build_all.sh` - Baue alle Base-Images
2. `./migrate_to_base_images.sh` - Migriere bestehende Container
3. `docker-compose build` - Rebuild alle Container
4. `docker-compose up -d` - Starte System mit neuer Struktur
