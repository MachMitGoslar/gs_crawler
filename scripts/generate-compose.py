#!/usr/bin/env python3
"""
Generate Docker Compose files from crawlers.yaml registry.

Usage:
    python scripts/generate-compose.py          # Generate both files
    python scripts/generate-compose.py --dev    # Generate only compose.dev.yaml
    python scripts/generate-compose.py --prod   # Generate only compose.yaml

Jeder Container läuft gehärtet (nicht als Root, schreibgeschütztes Root-Dateisystem,
keine Capabilities) und bekommt nur seinen eigenen Ordner httpdocs/crawler/<id>
als /app/output. Die Ordner müssen vor `docker compose up` existieren
(scripts/init-output-dirs.sh), sonst legt Docker sie als root an.
"""

import yaml
import sys
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REGISTRY_FILE = PROJECT_ROOT / "crawlers.yaml"

HEALTH_MONITOR = '000_health_monitor'
CRAWLER_ROOT = "./httpdocs/crawler"


def load_registry():
    """Load the crawler registry."""
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def is_enabled(crawler):
    """Crawler können in crawlers.yaml mit `enabled: false` pausiert werden."""
    return crawler.get('enabled', True)


def get_service_name(crawler):
    """Get the Docker service name for a crawler."""
    if 'service_name' in crawler:
        return crawler['service_name']
    cid = crawler['id']
    if cid == HEALTH_MONITOR:
        return 'gs_health_monitor'
    return f"gs_compiler_{cid}"


def get_container_name(crawler):
    """Get the Docker container name for a crawler."""
    cid = crawler['id']
    if cid == HEALTH_MONITOR:
        return 'gs_health_monitor'
    # Handle special cases
    if cid == '033_goslar24-7':
        return 'gs_compiler_033_goslar_24-7'
    return f"gs_compiler_{cid}"


def bind_mount(source, target, read_only=False):
    """Bind-Mount in Langform: fehlt der Quellordner, bricht compose ab statt ihn als root anzulegen."""
    lines = [
        "      - type: bind",
        f"        source: {source}",
        f"        target: {target}",
    ]
    if read_only:
        lines.append("        read_only: true")
    lines.extend([
        "        bind:",
        "          create_host_path: false",
    ])
    return lines


def defaults_block(mode):
    """Gemeinsame Härtung aller Services als YAML-Anker."""
    if mode == 'prod':
        uid = '${CRAWLER_UID:?CRAWLER_UID fehlt (UID des Hosting-Users, siehe .env.example)}'
        gid = '${CRAWLER_GID:?CRAWLER_GID fehlt (GID des Hosting-Users, siehe .env.example)}'
    else:
        uid, gid = '${CRAWLER_UID:-1000}', '${CRAWLER_GID:-1000}'
    return [
        "# Gemeinsame Härtung: kein Root, schreibgeschütztes Dateisystem, keine Capabilities.",
        "# Beschreibbar sind nur /tmp (tmpfs) und die gemounteten Ordner.",
        "x-crawler-defaults: &crawler-defaults",
        f'  user: "{uid}:{gid}"',
        "  read_only: true",
        "  cap_drop:",
        "    - ALL",
        "  security_opt:",
        "    - no-new-privileges:true",
        "  tmpfs:",
        "    - /tmp:rw,noexec,nosuid,size=64m",
        "  init: true",
        "  restart: unless-stopped",
        "",
    ]


def service_lines(crawler, mode, ghcr_prefix, all_services):
    """Compose-Service für einen eigenen Crawler-Container."""
    cid = crawler['id']
    lines = [f"  {get_service_name(crawler)}:", "    <<: *crawler-defaults"]

    if mode == 'prod':
        lines.append(f"    image: {ghcr_prefix}_{cid}:latest")
    else:
        lines.append(f"    build: ./docker_instances/{cid}")

    lines.append("    volumes:")
    if cid == HEALTH_MONITOR:
        # liest alle Ausgaben (nur lesend), schreibt nur in den eigenen Ordner
        lines += bind_mount(CRAWLER_ROOT, "/app/output", read_only=True)
        lines += bind_mount(f"{CRAWLER_ROOT}/{cid}", f"/app/output/{cid}")
        lines += bind_mount("./crawlers.yaml", "/app/configs/crawlers.yaml", read_only=True)
    elif crawler.get('expected_files'):
        lines += bind_mount(f"{CRAWLER_ROOT}/{cid}", "/app/output")
    for volume in crawler.get('volumes', []):
        lines.append(f"      - {volume}")
    if lines[-1] == "    volumes:":
        lines.pop()

    if crawler.get('ports'):
        lines.append("    ports:")
        for port in crawler['ports']:
            lines.append(f'      - "{port}"')

    if 'env_file' in crawler:
        lines.append("    env_file:")
        for ef in crawler['env_file']:
            lines.append(f"      - {ef}")

    lines.append(f"    container_name: {get_container_name(crawler)}")

    if cid == HEALTH_MONITOR:
        lines.append("    depends_on:")
        deps = [s for s in all_services[:3] if s]
        for svc in ['gs_generic_scraper_simple', 'gs_generic_scraper_tschuessschule']:
            if svc not in deps:
                deps.append(svc)
        for dep in deps:
            lines.append(f"      - {dep}")

    lines.append("")
    return lines


def generic_scraper_lines(config_dir, config_crawlers, mode, ghcr_prefix):
    """Ein generic_scraper-Container je Config-Verzeichnis, mit je einem Ordner pro Config-Crawler."""
    lines = [f"  gs_generic_scraper_{config_dir}:", "    <<: *crawler-defaults"]
    if mode == 'prod':
        lines.append(f"    image: {ghcr_prefix}_generic_scraper:latest")
    else:
        lines.append("    build: ./base_images/generic_scraper")
    lines.append("    volumes:")
    for crawler in sorted(config_crawlers, key=lambda c: c['id']):
        if is_enabled(crawler):
            cid = crawler['id']
            lines += bind_mount(f"{CRAWLER_ROOT}/{cid}", f"/app/output/{cid}")
    lines += bind_mount(f"./crawler_configs/{config_dir}", "/app/configs", read_only=True)
    disabled = sorted(c['id'] for c in config_crawlers if not is_enabled(c))
    if disabled:
        lines.append("    environment:")
        lines.append(f'      DISABLED_CONFIGS: "{",".join(disabled)}"')
    lines.append(f"    container_name: gs_generic_scraper_{config_dir}")
    lines.append("")
    return lines


def generate_compose(registry, mode):
    """Generate compose file content. mode: 'dev' (build from source) or 'prod' (pre-built images)."""
    crawlers = registry['crawlers']
    categories = registry['categories']
    ghcr_prefix = registry['settings']['ghcr_prefix']

    by_category = defaultdict(list)
    config_crawlers_by_dir = defaultdict(list)
    for crawler in crawlers:
        if crawler.get('implementation') == 'config':
            config_crawlers_by_dir[crawler.get('config_dir', 'simple')].append(crawler)
        elif is_enabled(crawler):
            by_category[crawler['category']].append(crawler)

    lines = [
        "# =============================================================================",
        "# Development Docker Compose for GS Crawler Stack" if mode == 'dev'
        else "# Production Docker Compose for GS Crawler Stack",
        "# GENERATED FILE - Do not edit directly!",
        "# Edit crawlers.yaml and run: python scripts/generate-compose.py",
    ]
    if mode == 'prod':
        lines.append("# Uses pre-built images from GitHub Container Registry")
    lines += [
        "# =============================================================================",
        "",
    ]
    lines += defaults_block(mode)
    lines.append("services:")

    all_services = []
    named_volumes = []

    for cat_id, cat_info in categories.items():
        cat_crawlers = [c for c in by_category.get(cat_id, []) if c.get('implementation') != 'config']
        if not cat_crawlers:
            continue

        lines.append(f"  # === {cat_info['name'].upper()} ===")
        for crawler in cat_crawlers:
            if crawler['id'] != HEALTH_MONITOR:
                all_services.append(get_service_name(crawler))
            lines += service_lines(crawler, mode, ghcr_prefix, all_services)
            for volume in crawler.get('volumes', []):
                name = volume.split(':')[0]
                if not name.startswith(('.', '/')) and name not in named_volumes:
                    named_volumes.append(name)

    if config_crawlers_by_dir:
        lines.append("  # === GENERIC SCRAPER (Config-Driven) ===")
        if mode == 'dev':
            lines.append("  # These run the YAML-based crawlers from crawler_configs/")
        for config_dir in sorted(config_crawlers_by_dir):
            lines += generic_scraper_lines(config_dir, config_crawlers_by_dir[config_dir], mode, ghcr_prefix)

    if named_volumes:
        lines.append("volumes:")
        for name in named_volumes:
            lines.append(f"  {name}:")
        lines.append("")

    return '\n'.join(lines)


def main():
    args = sys.argv[1:]
    generate_dev = '--dev' in args or not args
    generate_prod = '--prod' in args or not args

    print("Loading crawler registry...")
    registry = load_registry()

    crawler_count = len(registry['crawlers'])
    print(f"Found {crawler_count} crawlers in registry")

    if generate_dev:
        print("Generating compose.dev.yaml...")
        with open(PROJECT_ROOT / "compose.dev.yaml", 'w', encoding='utf-8') as f:
            f.write(generate_compose(registry, 'dev'))
        print("  -> compose.dev.yaml written")

    if generate_prod:
        print("Generating compose.yaml...")
        with open(PROJECT_ROOT / "compose.yaml", 'w', encoding='utf-8') as f:
            f.write(generate_compose(registry, 'prod'))
        print("  -> compose.yaml written")

    print("Done!")


if __name__ == '__main__':
    main()
