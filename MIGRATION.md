# GS Crawler Consolidation Migration Guide

This document describes the migration from 24 individual container images to a consolidated architecture using config-driven generic scrapers.

## Overview

### Before: 24 Individual Containers
Each crawler had its own:
- Docker container
- Python script
- Dockerfile
- CI/CD build job

### After: ~12 Containers (50% reduction)
- **2 Generic scraper containers** handling 9 crawlers via YAML configs
- **12 Specialized containers** for unique requirements (Selenium, image processing, etc.)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Generic Scraper                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ crawler_configs/simple/          (6 configs)        │   │
│  │ crawler_configs/tschuessschule/  (3 configs)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                          ↓                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ base_images/generic_scraper/                         │   │
│  │ - scraper.py (config-driven scraping engine)         │   │
│  │ - config_loader.py (YAML parsing, cron generation)   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│               Specialized Containers                        │
│  - 000_health_monitor (Flask dashboard)                     │
│  - 001_senioren (XML/RSS generation)                        │
│  - 002_ferienpass (PHP API fetcher)                         │
│  - 019_was_app (high-frequency, 3-min interval)             │
│  - 032_webcams_goslar (GIF generation)                      │
│  - 033_goslar24-7 (SQLite + time-series GIF)                │
│  - 035_talsperren (Selenium + matplotlib)                   │
│  - 045_naturgefahren (Selenium + form automation)           │
│  - 047_bodenwasser (image annotation)                       │
│  - 068_altstadtfest (Flask stateful API)                    │
└─────────────────────────────────────────────────────────────┘
```

## Migrated Crawlers

| Original Container | Config File | Status |
|-------------------|-------------|--------|
| 002_gz | simple/002_gz.yaml | ✅ Migrated |
| 041_immenrode | simple/041_immenrode.yaml | ✅ Migrated |
| 044_wiedelah | simple/044_wiedelah.yaml | ✅ Migrated |
| 048_jerstedt | simple/048_jerstedt.yaml | ✅ Migrated |
| 051_vhs | simple/051_vhs.yaml | ✅ Migrated |
| 052_vhs_kinderuni | simple/052_vhs_kinderuni.yaml | ✅ Migrated |
| 050_tschuessschule_studium | tschuessschule/050_tschuessschule_studium.yaml | ✅ Migrated |
| 053_tschuessschule_praktikum | tschuessschule/053_tschuessschule_praktikum.yaml | ✅ Migrated |
| 054_tschuessschule_ausbildung | tschuessschule/054_tschuessschule_ausbildung.yaml | ✅ Migrated |

## Local Development

### Test a single config
```bash
./scripts/test-scraper-local.sh 002_gz
```

### Test all configs
```bash
./scripts/test-all-configs.sh
```

### Build generic scraper image
```bash
./scripts/build-generic-scraper.sh
```

### Run consolidated stack
```bash
./scripts/run-consolidated.sh up
./scripts/run-consolidated.sh logs
./scripts/run-consolidated.sh down
```

### Add a new crawler
```bash
./scripts/add-crawler.sh
```

## Config File Format

```yaml
id: "002_gz"
name: "Goslarsche Zeitung"

url: "https://www.goslarsche.de/lokales/Goslar"
base_url: "https://www.goslarsche.de/lokales/Goslar"

schedule: "0 * * * *"  # Cron format
run_on_start: true

selectors:
  container: "article.StoryPreviewBox"

  title:
    selector: "h2.article-heading a"
    attribute: "text"

  description:
    selector: "div.article-preview"
    attribute: "text"

  image_url:
    selector: "div.PictureContainer img"
    attribute: "src"
    prefix: "https://example.com"  # Optional URL prefix

  call_to_action_url:
    selector: "h2.article-heading a"
    attribute: "href"

output:
  single:
    enabled: true
    filename: "002_goslarsche.json"
    cta_override: "https://crawler.goslar.app/crawler/002_goslarsche-alle.json"

  all:
    enabled: true
    filename: "002_goslarsche-alle.json"

selection:
  strategy: "first"  # first, random, or latest
```

## CI/CD Improvements

### Test Workflow (PR)
- Single-platform builds (AMD64 only) - 50% faster
- Python-only testing for config changes (no Docker needed)
- Conditional base image builds

### Deploy Workflow (main)
- Conditional base image builds (only when changed)
- Separate job for generic scraper image
- Multi-platform builds only for production

## Rollback Plan

The original containers remain in `docker_instances/` and can be used via:
```bash
docker compose -f compose.dev.yaml up
```

## Next Steps (Future Consolidation)

Candidates for future config-driven migration:
- 014_kunst_in_ar (complex but possible)
- 027_erster_freitag (date logic)
- 031_goslarer_geschichten (date parsing)
- 040_hp (straightforward)
- 042_freiwilligen (paginated)
- 056_serviceportal (random taglines)
