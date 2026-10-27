# GS Crawler Health Monitor (Dateisystem-basiert)

## Übersicht

Der Health Monitor überwacht alle Docker Container des GS Crawler Systems durch Dateisystem-Monitoring und stellt deren Status auf einer benutzerfreundlichen Weboberfläche dar. Diese Version funktioniert ohne Docker Socket Zugriff.

## Features

- **Dateisystem-Monitoring**: Überwacht alle Container durch Analyse der Output-Dateien
- **Datei-Status**: Zeigt Existenz, Größe, Alter und Gültigkeit der JSON-Dateien
- **Health Scoring**: Berechnet automatische Health-Scores basierend auf Datei-Status
- **Problem-Erkennung**: Identifiziert fehlende, veraltete oder ungültige Dateien
- **API Endpoints**: RESTful API für externe Integration
- **Auto-Refresh**: Automatische Aktualisierung alle 60 Sekunden

## Monitoring-Prinzip

Da kein Docker Socket Zugriff verfügbar ist, überwacht der Health Monitor:

1. **Datei-Existenz**: Prüft ob erwartete Output-Dateien vorhanden sind
2. **Datei-Alter**: Warnt bei veralteten Dateien (>24h = Warning, >48h = Error)
3. **JSON-Validität**: Validiert JSON-Dateien auf korrektes Format
4. **Dateigröße**: Überwacht Dateigröße und Änderungen

## Container Status Kategorien

- **🟢 Running**: Alle Dateien vorhanden und aktuell
- **🟡 Warning**: Einige Dateien fehlen oder sind veraltet (24-48h)
- **🔴 Error**: Kritische Probleme (keine Dateien oder >48h alt)
- **⚪ Unknown**: Status kann nicht bestimmt werden

## Web Interface

Zugriff über: `http://localhost:5000`

### Dashboard Features:
- Übersichtskarten mit System-Statistiken (Running/Warning/Error/Total)
- Detailansicht für jeden Container mit Datei-Status
- Dateigröße und Alter-Information
- Problem-Alerts und Warnungen
- Container-Details Modal

## API Endpoints

### GET /api/status
Gibt den kompletten Status aller Container zurück.

```json
{
  "containers": [...],
  "last_updated": "2025-07-02 10:30:00",
  "total_containers": 23,
  "running": 18,
  "warning": 3,
  "error": 2
}
```

### GET /api/container/{container_name}
Details zu einem spezifischen Container.

### GET /api/files/{container_name}
Datei-Details zu einem spezifischen Container.

### GET /api/health
System Health Check mit Score (0-100).

```json
{
  "health_score": 85.2,
  "status": "healthy",
  "summary": {...},
  "last_updated": "2025-07-02 10:30:00"
}
```

## JSON Export

Der Health Monitor erstellt automatisch eine JSON-Datei mit dem aktuellen Status:
- Pfad: `/app/output/000-health-status.json`
- Update-Intervall: Alle 30 Sekunden

## Docker Setup (ohne Socket)

Der Container benötigt **keinen** Docker Socket Zugriff:
```yaml
gs_health_monitor:
  build: ./docker_instances/000_health_monitor
  volumes:
    - ./httpdocs/crawler:/app/output:ro                                       # liest alle Ausgaben, nur lesend
    - ./httpdocs/crawler/000_health_monitor:/app/output/000_health_monitor    # schreibt nur hierhin
  ports:
    - "5000:5000"
```

## Überwachte Container

Der Monitor kennt 23 Container und deren erwartete Output-Dateien:

| Container | Erwartete Dateien | Typ |
|-----------|------------------|-----|
| gs_compiler_001_senioren | 001_senioren_feed.xml | XML Feed |
| gs_compiler_002_fepa | 002_fepa_events.json | JSON API |
| gs_compiler_002_gz | 002_goslarsche.json, 002_goslarsche-alle.json | News Crawler |
| ... | ... | ... |

## Konfiguration

- **Port**: 5000 (Web Interface)
- **Update-Intervall**: 30 Sekunden (Status Cache)
- **Auto-Refresh**: 60 Sekunden (Browser)
- **File Age Warning**: 24 Stunden
- **File Age Error**: 48 Stunden

## Technische Details

- **Framework**: Flask (Python)
- **Monitoring**: Dateisystem-basiert
- **Frontend**: Responsive HTML/CSS/JavaScript
- **Dependencies**: Keine Docker-Bibliotheken
- **Security**: Kein privilegierter Container-Zugriff erforderlich

## Vorteile dieser Lösung

1. **Sicherheit**: Kein Docker Socket Zugriff erforderlich
2. **Einfachheit**: Basiert nur auf Dateisystem-Monitoring
3. **Portabilität**: Funktioniert in allen Docker-Umgebungen
4. **Zuverlässigkeit**: Weniger Abhängigkeiten und Fehlerpunkte
5. **Performance**: Geringer Ressourcenverbrauch

## Limitierungen

- Keine direkten Container-Performance Metriken (CPU/Memory)
- Keine Container-Restart Funktionalität
- Status basiert nur auf Output-Dateien, nicht auf tatsächlichem Container-Status
