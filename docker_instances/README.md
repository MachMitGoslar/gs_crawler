# GS Crawler System - Container Übersicht

## System Architektur

Das GS Crawler System besteht aus 24 Docker Containern, die verschiedene Websites und Datenquellen automatisiert crawlen und als JSON-Dateien zur Verfügung stellen.

### Health Monitor
- **Container:** `gs_health_monitor`
- **Port:** 5001 (Web Interface)
- **Aufgabe:** Überwacht alle anderen Container und stellt Status-Dashboard bereit
- **Zugriff:** `http://localhost:5000`

## Container Details

### 📰 News & Medien

#### 001_senioren - Seniorenzeitung Goslar
- **Container:** `gs_compiler_001_senioren`
- **Cron:** `0 2 * * *` (täglich um 02:00 Uhr)
- **Aufgabe:** Crawlt die Goslar Seniorenzeitung und erstellt XML-Feed
- **Quelle:** https://www.goslar.de/leben-in-goslar/senioren/seniorenzeitung
- **Output:** `001_senioren_feed.xml`

#### 002_gz - Goslarsche Zeitung
- **Container:** `gs_compiler_002_gz`
- **Cron:** `0 * * * *` + `@reboot` (stündlich)
- **Aufgabe:** Crawlt lokale Nachrichten aus der Goslarschen Zeitung
- **Quelle:** https://www.goslarsche.de/lokales/Goslar
- **Output:** `002_goslarsche.json`, `002_goslarsche-alle.json`

#### 040_hp - Harzer Panorama
- **Container:** `gs_compiler_040_hp`
- **Cron:** `0 2 * * *` + `0 14 * * *` + `@reboot` (2x täglich: 02:00 & 14:00)
- **Aufgabe:** Crawlt das Harzer Panorama Magazin
- **Quelle:** https://www.panorama-am-sonntag.de/
- **Output:** `040_hp.json`

### 🎯 Events & Aktivitäten

#### 002_fepa - Ferienpass
- **Container:** `gs_compiler_002_fepa`
- **Cron:** `0 2 * * *` + `0 14 * * *` (2x täglich: 02:00 & 14:00)
- **Aufgabe:** Holt Ferienpass-Events über API
- **Quelle:** https://goslar.feripro.de/api/
- **Output:** `002_fepa_events.json`
- **Technologie:** PHP

#### 019_was_app - Community Vorschläge
- **Container:** `gs_compiler_019_was_app`
- **Cron:** `*/3 * * * *` + `0 14 * * *` + `@reboot` (alle 3 Minuten + 14:00)
- **Aufgabe:** Community-Vorschläge der WasApp
- **Quelle:** https://machmit.goslar.de/wasapp
- **Output:** `019_was_app.json`

#### 027_erster_freitag - Erster Freitag Events
- **Container:** `gs_compiler_027_erster_freitag`
- **Cron:** `0 9 * * *` (täglich um 09:00 Uhr)
- **Aufgabe:** Events zum "Ersten Freitag" in Goslar
- **Quelle:** https://insides.goslar-app.de/1-freitag-goslar
- **Output:** `027_erster_freitag.json`

#### 051_vhs - VHS Kurse
- **Container:** `gs_compiler_051_vhs`
- **Cron:** `0 9 * * *` (täglich um 09:00 Uhr)
- **Aufgabe:** Volkshochschule Kurse
- **Quelle:** https://www.vhs-goslar.de/
- **Output:** `051_vhs.json`, `051_vhs-alle.json`

#### 052_vhs_kinderuni - VHS Kinderuni
- **Container:** `gs_compiler_052_vhs_kinderuni`
- **Cron:** `0 9 * * *` (täglich um 09:00 Uhr)
- **Aufgabe:** Kinderuni-Kurse der VHS
- **Quelle:** https://www.vhs-goslar.de/
- **Output:** `052_vhs_kinderuni.json`

### 🎓 Bildung & Karriere

#### 050_tschuessschule_studium - Studium
- **Container:** `gs_compiler_050_tschuessschule_studium`
- **Cron:** `0 6 * * *` (täglich um 06:00 Uhr)
- **Aufgabe:** Studienangebote von TschüssSchule
- **Quelle:** https://tschuessschule.de/studium/
- **Output:** `050_tschuessschule_studium.json`, `050_tschuessschule_studium-alle.json`
- **Technologie:** Selenium

#### 053_tschuessschule_praktikum - Praktikum
- **Container:** `gs_compiler_053_tschuessschule_praktikum`
- **Cron:** `0 6 * * *` (täglich um 06:00 Uhr)
- **Aufgabe:** Praktikumsangebote von TschüssSchule
- **Quelle:** https://tschuessschule.de/praktikum/
- **Output:** `053_tschuessschule_praktikum.json`, `053_tschuessschule_praktikum-alle.json`
- **Technologie:** Selenium

#### 054_tschuessschule_ausbildung - Ausbildung
- **Container:** `gs_compiler_054_tschuessschule_ausbildung`
- **Cron:** `0 6 * * *` (täglich um 06:00 Uhr)
- **Aufgabe:** Ausbildungsangebote von TschüssSchule
- **Quelle:** https://tschuessschule.de/ausbildungsberufe/
- **Output:** `054_tschuessschule_ausbildung.json`, `054_tschuessschule_ausbildung-alle.json`
- **Technologie:** Selenium

### 🎨 Kultur & Veranstaltungen

#### 014_kunst_in_ar - Kunst in AR
- **Container:** `gs_compiler_014_kunst_in_ar`
- **Cron:** `0 8 * * *` (täglich um 08:00 Uhr)
- **Aufgabe:** Kunst-Events und Ausstellungen
- **Quelle:** https://kunst-in-ar.de/crawler.html
- **Output:** `014_kunst_in_ar.json`

#### 031_goslarer_geschichten - Goslarer Geschichten
- **Container:** `gs_compiler_031_goslarer_geschichten`
- **Cron:** `0 9 * * *` (täglich um 09:00 Uhr)
- **Aufgabe:** Forum-Beiträge zu Goslarer Geschichten
- **Quelle:** https://www.goslarer-geschichten.de/forum.php
- **Output:** `031_goslarer_geschichten.json`

### 🏘️ Gemeinde & Lokales

#### 041_immenrode - Immenrode
- **Container:** `gs_compiler_041_immenrode`
- **Cron:** `0 2 * * *` + `0 14 * * *` + `@reboot` (2x täglich: 02:00 & 14:00)
- **Aufgabe:** Neuigkeiten aus Immenrode
- **Quelle:** https://immenro.de/
- **Output:** `041_immenrode.json`

#### 042_freiwilligen - Freiwilligenagentur
- **Container:** `gs_compiler_042_freiwilligen`
- **Cron:** `0 2 * * *` + `0 14 * * *` + `@reboot` (2x täglich: 02:00 & 14:00)
- **Aufgabe:** Freiwilligenangebote der Freiwilligenagentur Goslar
- **Quelle:** https://www.freiwilligenagentur-goslar.de/
- **Output:** `042_freiwilligenagentur.json`, `042_freiwilligenagentur-alle.json`

#### 044_wiedelah - Wiedelah
- **Container:** `gs_compiler_044_wiedelah`
- **Cron:** `0 2 * * *` + `0 14 * * *` + `@reboot` (2x täglich: 02:00 & 14:00)
- **Aufgabe:** Arbeitseinsätze und Events in Wiedelah
- **Quelle:** https://dg-wiedelah.de/category/arbeitseinsaetze/
- **Output:** `044_wiedelah.json`, `044_wiedelah_alle.json`

#### 048_jerstedt - Jerstedt
- **Container:** `gs_compiler_048_jerstedt`
- **Cron:** `0 2 * * *` + `0 14 * * *` + `@reboot` (2x täglich: 02:00 & 14:00)
- **Aufgabe:** Stadtteilverein Jerstedt Aktivitäten
- **Quelle:** https://jerstedt.de
- **Output:** `048_jerstedt.json`

### 🚨 Sicherheit & Umwelt

#### 045_naturgefahren - Naturgefahren
- **Container:** `gs_compiler_045_naturgefahren`
- **Cron:** `*/15 * * * *` (alle 15 Minuten)
- **Aufgabe:** Wetterwarnungen und Naturgefahren für Goslar
- **Quelle:** https://www.naturgefahrenportal.de/de/alerts
- **Output:** `045_naturgefahren_de.json`
- **Technologie:** Selenium (Firefox)

### 💧 Umwelt & Ressourcen

#### 047_bodenwasser - Bodenwasser
- **Container:** `gs_compiler_047_bodenwasser`
- **Cron:** `0 2 * * *` + `0 14 * * *` + `@reboot` (2x täglich: 02:00 & 14:00)
- **Aufgabe:** Bodenwasser-Monitoring und Grafiken
- **Output:** `047_bodenwasser.json`, `047_bodenwasser.gif`

#### 035_talsperren - Talsperren
- **Container:** `gs_compiler_035_talsperren`
- **Cron:** `0 */1 * * *` (stündlich)
- **Aufgabe:** Talsperren-Füllstände der Harzwasserwerke
- **Quelle:** https://www.harzwasserwerke.de/infoservice/aktuelle-talsperrendaten/
- **Output:** `035_talsperren.json`
- **Technologie:** Selenium + Matplotlib

### 🏛️ Verwaltung & Service

#### 056_serviceportal - Serviceportal
- **Container:** `gs_compiler_056_serviceportal`
- **Cron:** `0 9 * * *` (täglich um 09:00 Uhr)
- **Aufgabe:** Dienste des Goslarer Serviceportals
- **Quelle:** https://service.goslar.de/home
- **Output:** `056_serviceportal.json`, `056_serviceportal-alle.json`

### 📷 Webcams

#### 032_webcams_goslar - Webcams
- **Container:** `gs_compiler_032_webcams_goslar`
- **Cron:** `0 9 * * *` (täglich um 09:00 Uhr)
- **Aufgabe:** Webcam-Bilder aus Goslar verarbeiten und optimieren
- **Quelle:** https://webcams.goslar.de/
- **Output:** `032_webcams_goslar.json`
- **Technologie:** PIL (Python Imaging Library)

#### 033_goslar24-7 - Goslar 24/7
- **Container:** `gs_compiler_033_goslar24-7`
- **Scheduled:** Jede Stunde zur vollen Uhrzeit
- **Aufgabe:** Webcam Bilder speichern und ein Gif mit stündlichen Webcam Bildern für die letzten 7 Tage erstellen
- **Quelle:** https://webcams.goslar.de/
- **Output:** `033_gif_schuhhof.json`, `033_gif_gmg_marktplatz.json`
- **Technologie:** PIL (Python Imaging Library)


## Cron-Job Zusammenfassung

### Häufigkeit der Ausführung

| Intervall | Anzahl Container | Container |
|-----------|------------------|-----------|
| **Alle 3 Minuten** | 1 | 019_was_app |
| **Alle 15 Minuten** | 1 | 045_naturgefahren |
| **Stündlich** | 2 | 002_gz, 035_talsperren |
| **Täglich um 02:00** | 1 | 001_senioren |
| **2x täglich (02:00 & 14:00)** | 7 | 002_fepa, 040_hp, 041_immenrode, 042_freiwilligen, 044_wiedelah, 047_bodenwasser, 048_jerstedt |
| **Täglich um 06:00** | 3 | 050_tschuessschule_studium, 053_tschuessschule_praktikum, 054_tschuessschule_ausbildung |
| **Täglich um 08:00** | 1 | 014_kunst_in_ar |
| **Täglich um 09:00** | 6 | 027_erster_freitag, 031_goslarer_geschichten, 051_vhs, 052_vhs_kinderuni, 056_serviceportal, 032_webcams_goslar |

### @reboot Container
Die folgenden Container führen ihre Scripts auch beim Container-Start aus:
- 002_gz
- 019_was_app  
- 040_hp
- 041_immenrode
- 042_freiwilligen
- 044_wiedelah
- 047_bodenwasser
- 048_jerstedt

## Technologie-Stack

### Python-basierte Container (21)
- **Standard:** requests, BeautifulSoup, json, datetime
- **Selenium:** 045_naturgefahren (Firefox), 050/053/054_tschuessschule (Chrome)
- **Bildverarbeitung:** 032_webcams_goslar (PIL), 047_bodenwasser (matplotlib)
- **XML:** 001_senioren (lxml)

### PHP-basierte Container (1)
- **002_fepa:** Direkter API-Zugriff

### Health Monitor
- **Technologie:** Flask, Docker API, Jinja2
- **Features:** Web-Dashboard, Container-Management, Performance-Monitoring

## Output-Verzeichnis

Alle Container speichern ihre Ergebnisse in:
```
./httpdocs/crawler/
```

Über Docker Volume Mount verfügbar als:
```
/app/output (Container-intern)
```

## Management

### Container starten
```bash
docker-compose up -d
```

### Container neu bauen
```bash
docker-compose up --build -d
```

### Status überwachen
- **Web-Interface:** http://localhost:5000
- **CLI:** `docker-compose ps`
- **Logs:** `docker-compose logs [container_name]`

### Health Monitor Dashboard
Das Health Monitor Dashboard bietet:
- ✅ Real-time Container Status
- 📊 Performance Metriken (CPU, Memory)
- 📝 Live Logs der letzten Ausgaben
- 🔄 Container Restart-Funktionalität
- 📡 API Endpoints für externe Integration

---

**Letzte Aktualisierung:** 2. Juli 2025  
**Gesamt Container:** 24 (23 Crawler + 1 Health Monitor)  
**Aktive Cron Jobs:** 23
