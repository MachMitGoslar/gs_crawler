#!/usr/bin/env python3
"""
Generate Docker Compose files from crawlers.yaml registry.

Usage:
    python scripts/generate-compose.py          # Generate both files
    python scripts/generate-compose.py --dev    # Generate only compose.dev.yaml
    python scripts/generate-compose.py --prod   # Generate only compose.yaml
"""

import yaml
import sys
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REGISTRY_FILE = PROJECT_ROOT / "crawlers.yaml"


def load_registry():
    """Load the crawler registry."""
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_service_name(crawler):
    """Get the Docker service name for a crawler."""
    if 'service_name' in crawler:
        return crawler['service_name']
    cid = crawler['id']
    if cid == '000_health_monitor':
        return 'gs_health_monitor'
    return f"gs_compiler_{cid}"


def get_container_name(crawler):
    """Get the Docker container name for a crawler."""
    cid = crawler['id']
    if cid == '000_health_monitor':
        return 'gs_health_monitor'
    # Handle special cases
    if cid == '002_ferienpass':
        return 'gs_compiler_002_fepa'
    if cid == '033_goslar24-7':
        return 'gs_compiler_033_goslar_24-7'
    return f"gs_compiler_{cid}"


def generate_dev_compose(registry):
    """Generate compose.dev.yaml for local development."""
    settings = registry['settings']
    crawlers = registry['crawlers']
    categories = registry['categories']

    # Group crawlers by category
    by_category = defaultdict(list)
    for crawler in crawlers:
        by_category[crawler['category']].append(crawler)

    # Find which config directories are used
    config_dirs = set()
    for crawler in crawlers:
        if crawler.get('implementation') == 'config':
            config_dirs.add(crawler.get('config_dir', 'simple'))

    lines = [
        "# =============================================================================",
        "# Development Docker Compose for GS Crawler Stack",
        "# GENERATED FILE - Do not edit directly!",
        "# Edit crawlers.yaml and run: python scripts/generate-compose.py",
        "# =============================================================================",
        "",
        "services:",
    ]

    # Track services for health monitor depends_on
    all_services = []

    # Generate services by category
    for cat_id, cat_info in categories.items():
        cat_crawlers = by_category.get(cat_id, [])
        if not cat_crawlers:
            continue

        lines.append(f"  # === {cat_info['name'].upper()} ===")

        for crawler in cat_crawlers:
            service_name = get_service_name(crawler)
            container_name = get_container_name(crawler)
            cid = crawler['id']

            if cid != '000_health_monitor':
                all_services.append(service_name)

            lines.append(f"  {service_name}:")

            # Build path
            if crawler.get('implementation') == 'custom':
                if cid == '002_ferienpass':
                    lines.append(f"    build: ./docker_instances/002_ferienpass")
                else:
                    lines.append(f"    build: ./docker_instances/{cid}")
            # Config-driven crawlers are handled by generic_scraper containers
            elif crawler.get('implementation') == 'config':
                # Skip individual entries - they're handled by generic_scraper
                lines.pop()  # Remove the service_name line
                continue

            # Volumes
            lines.append("    volumes:")
            lines.append("      - ./httpdocs/crawler:/app/output")
            # Health monitor needs access to crawlers.yaml registry
            if cid == '000_health_monitor':
                lines.append("      - ./crawlers.yaml:/app/configs/crawlers.yaml:ro")

            # Ports
            if 'ports' in crawler:
                lines.append("    ports:")
                for port in crawler['ports']:
                    lines.append(f'      - "{port}"')

            lines.append(f"    container_name: {container_name}")
            lines.append("    restart: unless-stopped")

            # Health monitor depends_on
            if cid == '000_health_monitor':
                lines.append("    depends_on:")
                # Add first few services as dependencies
                deps = [s for s in all_services[:3] if s]
                for svc in ['gs_generic_scraper_simple', 'gs_generic_scraper_tschuessschule']:
                    if svc not in deps:
                        deps.append(svc)
                for dep in deps:
                    lines.append(f"      - {dep}")

            lines.append("")

    # Add generic scraper containers
    if config_dirs:
        lines.append("  # === GENERIC SCRAPER (Config-Driven) ===")
        lines.append("  # These run the YAML-based crawlers from crawler_configs/")
        for config_dir in sorted(config_dirs):
            lines.append(f"  gs_generic_scraper_{config_dir}:")
            lines.append("    build: ./base_images/generic_scraper")
            lines.append("    volumes:")
            lines.append("      - ./httpdocs/crawler:/app/output")
            lines.append(f"      - ./crawler_configs/{config_dir}:/app/configs")
            lines.append(f"    container_name: gs_generic_scraper_{config_dir}")
            lines.append("    restart: unless-stopped")
            lines.append("")

    # Volume definition
    lines.extend([
        "# Shared volume for all output files",
        "volumes:",
        "  crawler_output:",
        "    driver: local",
        "    driver_opts:",
        "      type: none",
        "      o: bind",
        "      device: ./httpdocs/crawler",
        ""
    ])

    return '\n'.join(lines)


def generate_prod_compose(registry):
    """Generate compose.yaml for production (pre-built images)."""
    settings = registry['settings']
    crawlers = registry['crawlers']
    categories = registry['categories']
    ghcr_prefix = settings['ghcr_prefix']

    # Group crawlers by category
    by_category = defaultdict(list)
    for crawler in crawlers:
        by_category[crawler['category']].append(crawler)

    # Find which config directories are used
    config_dirs = set()
    for crawler in crawlers:
        if crawler.get('implementation') == 'config':
            config_dirs.add(crawler.get('config_dir', 'simple'))

    lines = [
        "# =============================================================================",
        "# Production Docker Compose for GS Crawler Stack",
        "# GENERATED FILE - Do not edit directly!",
        "# Edit crawlers.yaml and run: python scripts/generate-compose.py",
        "# Uses pre-built images from GitHub Container Registry",
        "# =============================================================================",
        "",
        "services:",
    ]

    # Track services for health monitor depends_on
    all_services = []

    # Generate services by category
    for cat_id, cat_info in categories.items():
        cat_crawlers = by_category.get(cat_id, [])
        if not cat_crawlers:
            continue

        lines.append(f"  # === {cat_info['name'].upper()} ===")

        for crawler in cat_crawlers:
            service_name = get_service_name(crawler)
            container_name = get_container_name(crawler)
            cid = crawler['id']

            if cid != '000_health_monitor':
                all_services.append(service_name)

            lines.append(f"  {service_name}:")

            # Image
            if crawler.get('implementation') == 'custom':
                if cid == '002_ferienpass':
                    lines.append(f"    image: {ghcr_prefix}_002_ferienpass:latest")
                else:
                    lines.append(f"    image: {ghcr_prefix}_{cid}:latest")
            elif crawler.get('implementation') == 'config':
                # Skip individual entries - they're handled by generic_scraper
                lines.pop()  # Remove the service_name line
                continue

            # Volumes
            lines.append("    volumes:")
            lines.append("      - ./httpdocs/crawler:/app/output")
            # Health monitor needs access to crawlers.yaml registry
            if cid == '000_health_monitor':
                lines.append("      - ./crawlers.yaml:/app/configs/crawlers.yaml:ro")

            # Ports
            if 'ports' in crawler:
                lines.append("    ports:")
                for port in crawler['ports']:
                    lines.append(f'      - "{port}"')

            lines.append(f"    container_name: {container_name}")
            lines.append("    restart: unless-stopped")

            # Health monitor depends_on
            if cid == '000_health_monitor':
                lines.append("    depends_on:")
                deps = [s for s in all_services[:3] if s]
                for svc in ['gs_generic_scraper_simple', 'gs_generic_scraper_tschuessschule']:
                    if svc not in deps:
                        deps.append(svc)
                for dep in deps:
                    lines.append(f"      - {dep}")

            lines.append("")

    # Add generic scraper containers
    if config_dirs:
        lines.append("  # === GENERIC SCRAPER (Config-Driven) ===")
        for config_dir in sorted(config_dirs):
            lines.append(f"  gs_generic_scraper_{config_dir}:")
            lines.append(f"    image: {ghcr_prefix}_generic_scraper:latest")
            lines.append("    volumes:")
            lines.append("      - ./httpdocs/crawler:/app/output")
            lines.append(f"      - ./crawler_configs/{config_dir}:/app/configs")
            lines.append(f"    container_name: gs_generic_scraper_{config_dir}")
            lines.append("    restart: unless-stopped")
            lines.append("")

    # Volume definition
    lines.extend([
        "# Shared volume for all output files",
        "volumes:",
        "  crawler_output:",
        "    driver: local",
        "    driver_opts:",
        "      type: none",
        "      o: bind",
        "      device: ./httpdocs/crawler",
        ""
    ])

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
        content = generate_dev_compose(registry)
        with open(PROJECT_ROOT / "compose.dev.yaml", 'w', encoding='utf-8') as f:
            f.write(content)
        print("  -> compose.dev.yaml written")

    if generate_prod:
        print("Generating compose.yaml...")
        content = generate_prod_compose(registry)
        with open(PROJECT_ROOT / "compose.yaml", 'w', encoding='utf-8') as f:
            f.write(content)
        print("  -> compose.yaml written")

    print("Done!")


if __name__ == '__main__':
    main()
