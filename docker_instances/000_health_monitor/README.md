# GS Crawler Health Monitor

## Übersicht

Der Health Monitor überwacht alle Docker Container des GS Crawler Systems und stellt deren Status auf einer benutzerfreundlichen Weboberfläche dar.

## Features

- **Real-time Monitoring**: Überwacht alle gs_compiler Container in Echtzeit
- **Performance Metriken**: Zeigt CPU- und Speicherverbrauch an
- **Container Management**: Restart-Funktionalität für Container
- **Log Anzeige**: Zeigt die letzten Log-Einträge jedes Containers
- **API Endpoints**: RESTful API für externe Integration
- **Auto-Refresh**: Automatische Aktualisierung alle 60 Sekunden

## Web Interface

Zugriff über: `http://localhost:5000`

### Dashboard Features:
- Übersichtskarten mit Container-Statistiken
- Detailansicht für jeden Container
- Status-Badges (Running, Stopped, Error)
- Performance-Balken für CPU und Memory
- Log-Viewer mit den neuesten Ausgaben
- Restart-Button für einzelne Container

## API Endpoints

### GET /api/status
Gibt den kompletten Status aller Container zurück.

```json
{
  "containers": [...],
  "last_updated": "2025-07-02 10:30:00",
  "total_containers": 12,
  "running": 10,
  "stopped": 2,
  "error": 0
}
```

### GET /api/container/{container_name}
Details zu einem spezifischen Container.

### GET /api/restart/{container_name}
Startet einen Container neu.

## JSON Export

Der Health Monitor erstellt automatisch eine JSON-Datei mit dem aktuellen Status:
- Pfad: `/app/output/000-health-status.json`
- Update-Intervall: Alle 30 Sekunden

## Docker Setup

Der Container benötigt Zugriff auf den Docker Socket:
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

## Konfiguration

- **Port**: 5000 (Web Interface)
- **Update-Intervall**: 30 Sekunden (Status Cache)
- **Auto-Refresh**: 60 Sekunden (Browser)

## Technische Details

- **Framework**: Flask (Python)
- **Docker API**: docker-py
- **Frontend**: Responsive HTML/CSS/JavaScript
- **Monitoring**: Threading für Background-Updates
