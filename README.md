[![Docker Build and Container Health Test](https://github.com/MachMitGoslar/gs_crawler/actions/workflows/docker-build-test.yml/badge.svg)](https://github.com/MachMitGoslar/gs_crawler/actions/workflows/docker-build-test.yml)

# GS Crawler System

Das GS Crawler System besteht aus Docker Containern, die verschiedene Websites und Datenquellen der Region Goslar automatisiert crawlen und als JSON-Dateien zur Verfügung stellen.

## Quick Start

```bash
# Local development
./scripts/dev.sh setup    # First-time setup (venv, config, etc.)
./scripts/dev.sh up       # Start containers and health monitor
./scripts/dev.sh logs     # View live logs
```

**Health Monitor:** View status at [http://localhost:5015](http://localhost:5015) after starting the system.

## Crawler Registry

All crawlers are defined in [`crawlers.yaml`](crawlers.yaml) - the single source of truth.

To add/modify a crawler:
1. Edit `crawlers.yaml`
2. Run `./scripts/generate-all.sh` to update Dockerfiles and Compose configurations
3. Commit the changes

<!-- CRAWLER_TABLE_START -->
**Total Crawlers:** 26 (17 custom containers, 9 config-driven)

### Infrastructure
_System monitoring and management_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 000_health_monitor | Health Monitor | flask_monitor | Always running | `-` |

### News & Media
_Local news sources and media outlets_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 001_senioren | Seniorenzeitung Goslar | XML Feed | Täglich 02:00 | `001_senioren_feed.xml` |
| 002_gz | Goslarsche Zeitung | News Crawler | Stündlich | `002_goslarsche.json, 002_goslarsche-alle.json` |
| 040_hp | Harzer Panorama | News Crawler | 2x täglich (02:00, 14:00) | `040_hp.json` |

### Events
_Event calendars and activities_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 002_ferienpass | Ferienpass Events | JSON API | 2x täglich (02:00, 14:00) | `002_fepa_events.json` |
| 014_kunst_in_ar | Kunst in AR | Event Crawler | Täglich 08:00 | `017-kunst-in-ar-single.json` |
| 019_was_app | WasApp Community | Community Feed | Alle 3 Minuten | `019_was_app.json` |
| 027_erster_freitag | Erster Freitag Events | Event Crawler | Täglich 09:00 | `027-erster-freitag.json` |
| 070_wochenmarkt | Wochenmarkt Goslar | Market Crawler | Alle 2 Stunden | `070_wochenmarkt_card.json, 070_wochenmarkt_alle...` |

### Local Communities
_Village and neighborhood news_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 041_immenrode | Immenrode News | Local News | 2x täglich (02:00, 14:00) | `041_immenrode.json` |
| 044_wiedelah | Wiedelah Events | Community Events | 2x täglich (02:00, 14:00) | `044-wiedelah.json, 044-wiedelah_alle.json` |
| 048_jerstedt | Jerstedt News | Local News | 2x täglich (02:00, 14:00) | `048_jerstedt.json` |

### Community & Volunteering
_Community organizations and volunteer opportunities_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 031_goslarer_geschichten | Goslarer Geschichten | Community Forum | Täglich 03:00 | `031_goslarer_geschichten.json` |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.