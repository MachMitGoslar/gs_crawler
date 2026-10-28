[![Docker Build and Container Health Test](https://github.com/MachMitGoslar/gs_crawler/actions/workflows/docker-build-test.yml/badge.svg)](https://github.com/MachMitGoslar/gs_crawler/actions/workflows/docker-build-test.yml)

# GS Crawler System

Das GS Crawler System besteht aus Docker Containern, die verschiedene Websites und Datenquellen der Region Goslar automatisiert crawlen und als JSON-Dateien zur Verfügung stellen.

## Quick Start

```bash
# Local development
./scripts/dev.sh setup    # First-time setup
./scripts/dev.sh up       # Start containers
./scripts/dev.sh logs     # View logs

# Health Monitor: http://localhost:5015
```

## Crawler Registry

All crawlers are defined in [`crawlers.yaml`](crawlers.yaml) - the single source of truth.

To add/modify a crawler:
1. Edit `crawlers.yaml`
2. Run `./scripts/generate-all.sh`
3. Commit the changes

<!-- CRAWLER_TABLE_START -->
**Total Crawlers:** 39 (22 custom containers, 17 config-driven)

### Infrastructure
_System monitoring and management_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 000_health_monitor | Health Monitor | flask_monitor | Always running | `-` |

### News & Media
_Local news sources and media outlets_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 001_senioren | Seniorenzeitung Goslar | XML Feed | Täglich 02:00 | `001_senioren/001_senioren_feed.xml` |
| 002_gz | Goslarsche Zeitung | News Crawler | Stündlich | `002_gz/002_goslarsche.json, 002_gz/002_goslarsc...` |
| 040_hp | Harzer Panorama | News Crawler | 2x täglich (02:00, 14:00) | `040_hp/040_hp.json` |

### Events
_Event calendars and activities_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 004_zufaellig-nix-vor | Zufällig nix vor? | Suggestion Feed | Täglich 07:00 | `004_zufaellig-nix-vor/ui-kit/goslar-ui.css, 004...` |
| 014_kunst_in_ar | Kunst in AR | Event Crawler | Täglich 08:00 | `014_kunst_in_ar/017-kunst-in-ar-single.json` |
| 019_was_app | WasApp Community | Community Feed | Alle 3 Minuten | `019_was_app/019_was_app.json` |
| 027_erster_freitag | Erster Freitag Events | Event Crawler | Täglich 09:00 | `027_erster_freitag/027-erster-freitag.json` |
| 070_wochenmarkt | Wochenmarkt Goslar | Market Crawler | Alle 2 Stunden | `070_wochenmarkt/070_wochenmarkt_card.json, 070_...` |

### Local Communities
_Village and neighborhood news_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 041_immenrode | Immenrode News | Local News | 2x täglich (02:00, 14:00) | `041_immenrode/041_immenrode.json` |
| 086_liebenburg | Liebenburg aktuelle Mitteilungen | Local News | Täglich 09:00 | `086_liebenburg/086_liebenburg.json, 086_liebenb...` |
| 087_langelsheim | Langelsheim aktuelle Mitteilungen | Local News | Täglich 09:00 | `087_langelsheim/087_langelsheim.json, 087_lange...` |
| 088_braunlage | Braunlage Mitteilungen | Local News | Täglich 09:00 | `088_braunlage/088_braunlage.json, 088_braunlage...` |
| 089_seesen | Seesen Mitteilungen | Local News | Täglich 09:00 | `089_seesen/089_seesen.json, 089_seesen/089_sees...` |
| 090_bad_harzburg | Bad Harzburg aktuelle Mitteilungen | Local News | Täglich 09:00 | `090_bad_harzburg/090_bad_harzburg.json, 090_bad...` |
| 057_cvd | CVD Goslar Nachrichten | Local News | Täglich 09:00 | `057_cvd/057_cvd.json, 057_cvd/057_cvd_alle.json` |
| 092_lewerdaele | Lewer-Daele Veranstaltungen | Community Events | Täglich 09:00 | `092_lewerdaele/092_lewerdaele.json, 092_lewerda...` |
| 106_ratsgymnasium | Ratsgymnasium Goslar Beiträge | Local News | Täglich 09:00 | `106_ratsgymnasium/106_ratsgymnasium.json, 106_r...` |
| 044_wiedelah | Wiedelah Events | Community Events | 2x täglich (02:00, 14:00) | `044_wiedelah/044-wiedelah.json, 044_wiedelah/04...` |
| 048_jerstedt | Jerstedt News _(pausiert)_ | Local News | - | `048_jerstedt/048_jerstedt.json` |

### Community & Volunteering
_Community organizations and volunteer opportunities_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 031_goslarer_geschichten | Goslarer Geschichten | Forum Crawler | Täglich 09:00 | `031_goslarer_geschichten/031-goslarer_geschicht...` |
| 042_freiwilligen | Freiwilligenagentur | Volunteer Portal | 2x täglich (02:00, 14:00) | `042_freiwilligen/ui-kit/goslar-ui.css, 042_frei...` |

### Environmental Monitoring
_Weather, water, and environmental data_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 035_talsperren | Talsperren Daten _(pausiert)_ | Umwelt Monitor | - | `035_talsperren/035-talsperren_alle.json, 035_ta...` |
| 045_naturgefahren | Naturgefahren Monitor | Weather Alert | Alle 15 Minuten | `045_naturgefahren/045_naturgefahren_de.json` |
| 046_bio_stadt_goslar | Biostadt Goslar | Info & Einkaufsführer | 2x täglich (02:00, 14:00) | `046_bio_stadt_goslar/ui-kit/goslar-ui.css, 046_...` |
| 047_bodenwasser | Bodenwasser Monitor | Umwelt Monitor | 2x täglich (02:00, 14:00) | `047_bodenwasser/047_bodenwasser.json, 047_boden...` |

### Education
_Schools, courses, and educational opportunities_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 050_tschuessschule_studium | TschüssSchule Studium | Education Portal | Täglich 06:00 | `050_tschuessschule_studium/050-tschuessschule-s...` |
| 051_vhs | VHS Kurse | Education Portal | Täglich 09:00 | `051_vhs/051_vhs.json, 051_vhs/051_vhs-alle.json` |
| 052_vhs_kinderuni | VHS Kinderuni | Education Portal | Täglich 09:00 | `052_vhs_kinderuni/052_vhs_kinderuni.json, 052_v...` |
| 053_tschuessschule_praktikum | TschüssSchule Praktikum | Education Portal | Täglich 06:00 | `053_tschuessschule_praktikum/053-tschuessschule...` |
| 054_tschuessschule_ausbildung | TschüssSchule Ausbildung | Education Portal | Täglich 06:00 | `054_tschuessschule_ausbildung/054-tschuessschul...` |

### Mobilität & Verkehr
_ÖPNV, Fuhrparks und Verkehrsdaten_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 073_busflotte | Busflotte Stadtbus Goslar | Fleet Data | Wöchentlich Montag 04:00 | `073_busflotte/073_busflotte_card.json, 073_busf...` |

### Specialized
_Unique data sources requiring custom processing_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 032_webcams_goslar | Webcams Goslar | Webcam Processor | Täglich 09:00 | `032_webcams_goslar/032_webcams_goslar.json, 032...` |
| 033_goslar24-7 | Goslar24-7 Webcams | Webcam Processor | Stündlich | `033_goslar24-7/033_gif_schuhhof.json, 033_gosla...` |
| 056_serviceportal | Serviceportal Goslar | Service Portal | Täglich 09:00 | `056_serviceportal/ui-kit/goslar-ui.css, 056_ser...` |
| 060_defi_kataster | Defibrillatoren Kataster | Defi Locations | Täglich 06:00 | `060_defi_kataster/ui-kit/goslar-ui.css, 060_def...` |
| 080_bereitschaftsdienste | Bereitschaftsdienste Goslar | Emergency Services | Alle 15 Minuten (API nur nach Endzeit) | `080_bereitschaftsdienste/ui-kit/goslar-ui.css, ...` |

### API Services
_API endpoints and services_

| ID | Name | Type | Schedule | Output Files |
|:---|:-----|:-----|:---------|:-------------|
| 068_altstadtfest | Altstadtfest Goslar | API Endpoint | API Endpoint | `-` |
| 072_karriere | Karriere Goslar | Job Portal | Stündlich | `072_karriere/ui-kit/goslar-ui.css, 072_karriere...` |

<!-- CRAWLER_TABLE_END -->

## Architecture

```
crawlers.yaml              <- Single source of truth
     |
     +-> Health Monitor    <- Reads crawler definitions at runtime
     +-> compose.yaml      <- Generated via ./scripts/generate-compose.py
     +-> compose.dev.yaml  <- Generated via ./scripts/generate-compose.py
     +-> README.md tables  <- Generated via ./scripts/generate-readme.py
```

### Implementation Types

| Type | Location | Description |
|:-----|:---------|:------------|
| **custom** | `docker_instances/XXX_name/` | Full Dockerfile + custom Python script |
| **config** | `crawler_configs/simple/` | YAML config for generic scraper |
| **config** | `crawler_configs/tschuessschule/` | YAML config for nested scraper |

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup instructions.

### Key Commands

```bash
./scripts/dev.sh setup        # Build base images locally
./scripts/dev.sh up           # Start all containers
./scripts/dev.sh down         # Stop all containers
./scripts/dev.sh logs         # Follow logs
./scripts/dev.sh test         # Run scraper tests

./scripts/generate-all.sh     # Regenerate compose files and README
```

### Ports

| Port | Service |
|:-----|:--------|
| 5015 | Health Monitor Dashboard |
| 5016 | Altstadtfest API |

## Output

Every crawler writes to its own folder `httpdocs/crawler/<id>/` (mounted as `/app/output` in its container, public at `/crawler/<id>/`). Create the folders with `./scripts/init-output-dirs.sh` before `docker compose up`; `scripts/dev.sh` does this automatically. See [docs/HARDENING.md](docs/HARDENING.md).

## CI/CD

- **Build Test:** Validates all containers on push/PR
- **Daily Health Check:** Runs containers daily and validates output

---

**Configuration:** [`crawlers.yaml`](crawlers.yaml)
**Contributing:** See [CONTRIBUTING.md](CONTRIBUTING.md)
