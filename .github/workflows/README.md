# GitHub Actions für GS Crawler System

Dieses Verzeichnis enthält GitHub Actions Workflows zur automatisierten Überwachung und Validierung des Docker-basierten Crawler-Systems.

## Workflows

### 1. Docker Build and Container Health Test (`docker-build-test.yml`)

**Trigger:**
- Push auf `main` oder `develop` Branch
- Pull Requests auf `main` Branch  
- Manuell über GitHub UI

**Zweck:**
- Baut alle Docker Container neu
- Startet das komplette System
- Testet den Health Monitor
- Validiert die API-Endpoints
- Überprüft Output-Dateien
- Führt Security-Scan durch (nur bei main branch)

**Schritte:**
1. Repository checkout
2. Docker Buildx Setup
3. Alle Container bauen
4. Container starten und initialisieren lassen
5. Health Monitor API testen
6. Container-Status via API validieren
7. Output-Dateien überprüfen
8. Bei Fehlern: Container-Logs anzeigen
9. Cleanup

### 2. Daily Health Check (`daily-health-check.yml`)

**Trigger:**
- Täglich um 06:00 UTC (Cron)
- Manuell über GitHub UI

**Zweck:**
- Regelmäßige Systemüberwachung
- Längere Laufzeit für vollständige Crawler-Ausführung
- Detaillierte Analyse der Output-Dateien
- Health-Report-Generierung

**Schritte:**
1. System aufbauen und starten
2. 3 Minuten warten für komplette Initialisierung
3. Umfassende Gesundheitsprüfung
4. JSON-Validierung aller Output-Dateien
5. Health-Report generieren und als Artefakt speichern
6. Kritische Issues bewerten
7. Cleanup

## Features

### Health Monitor Integration
- Beide Workflows nutzen den Health Monitor (Port 5001)
- API-Endpoints werden getestet: `/health`, `/api/status`, `/`
- JSON-Response wird ausgewertet für Container-Status

### Output-Validierung
- Überprüfung der `httpdocs/crawler/` Verzeichnisstruktur
- Dateizählung und -größenanalyse
- JSON-Syntax-Validierung
- Erkennung leerer Dateien

### Error Handling
- Container-Logs bei Fehlern
- Graceful handling wenn Crawler noch keine Ausgabe produziert haben
- Kritische vs. Warnungen unterscheiden

### Security
- Trivy vulnerability scanner (nur main branch)
- SARIF-Upload für GitHub Security Tab

## Erwartete Ausgaben

Die Workflows erwarten folgende kritische Dateien in `httpdocs/crawler/`:
- "047_bodenwasser.json"
- "035-talsperren_alle.json"
- "019_was_app.json"
- "040_hp.json"

Weitere Dateien werden erkannt und validiert, aber ihr Fehlen führt nicht zu einem Workflow-Fehler.

## Artefakte

Der Daily Health Check speichert einen detaillierten Health-Report als GitHub Artefakt:
- Dateiname: `health-report-<run-number>`
- Aufbewahrung: 30 Tage
- Enthält: Container-Status, Dateistatistiken, Health Monitor Response

## Monitoring

### Success Criteria
- Alle Container starten erfolgreich
- Health Monitor API antwortet
- Mindestens eine Output-Datei wird generiert
- Keine kritischen Container-Ausfälle

### Warning Indicators
- Leere Output-Dateien
- Einzelne Container mit Problemen
- Langsame API-Response

### Failure Conditions
- Health Monitor nicht erreichbar
- Keine Output-Dateien nach 3 Minuten
- Mehr als 3 leere Dateien
- Mehr als ein Container ausgefallen
- Mehr als 2 kritische Issues gleichzeitig

## Verwendung

### Manuell starten
1. Gehe zu Actions Tab im GitHub Repository
2. Wähle gewünschten Workflow
3. Klicke "Run workflow"

### Logs einsehen
- Workflow-Runs zeigen detaillierte Logs für jeden Schritt
- Bei Fehlern werden Container-Logs automatisch angezeigt
- Health-Reports können als Artefakte heruntergeladen werden

### Troubleshooting
- Prüfe Container-Logs in den Workflow-Ausgaben
- Health Monitor Response zeigt detaillierten System-Status
- Bei persistenten Problemen: manuell docker-compose lokal testen

## Konfiguration

Die Workflows können angepasst werden:
- **Timing:** Ändere Cron-Schedule in `daily-health-check.yml`
- **Timeout:** Verlängere Sleep-Zeiten für langsamere Systeme
- **Critical Files:** Erweitere die Liste in `Test specific crawler endpoints`
- **Failure Thresholds:** Anpasse die Schwellwerte in `Check for critical issues`
