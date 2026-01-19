#!/usr/bin/env python3
"""
Generate README.md crawler documentation from crawlers.yaml registry.

Usage:
    python scripts/generate-readme.py

This updates the crawler tables in README.md between the marker comments:
<!-- CRAWLER_TABLE_START --> and <!-- CRAWLER_TABLE_END -->
"""

import yaml
import re
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
REGISTRY_FILE = PROJECT_ROOT / "crawlers.yaml"
README_FILE = PROJECT_ROOT / "README.md"

START_MARKER = "<!-- CRAWLER_TABLE_START -->"
END_MARKER = "<!-- CRAWLER_TABLE_END -->"


def load_registry():
    """Load the crawler registry."""
    with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def generate_crawler_tables(registry):
    """Generate markdown tables for all crawlers."""
    crawlers = registry['crawlers']
    categories = registry['categories']

    # Group crawlers by category
    by_category = defaultdict(list)
    for crawler in crawlers:
        by_category[crawler['category']].append(crawler)

    lines = []

    # Summary counts
    total = len(crawlers)
    custom = sum(1 for c in crawlers if c.get('implementation') == 'custom')
    config = sum(1 for c in crawlers if c.get('implementation') == 'config')

    lines.append(f"**Total Crawlers:** {total} ({custom} custom containers, {config} config-driven)")
    lines.append("")

    # Generate table for each category
    for cat_id, cat_info in categories.items():
        cat_crawlers = by_category.get(cat_id, [])
        if not cat_crawlers:
            continue

        lines.append(f"### {cat_info['name']}")
        lines.append(f"_{cat_info['description']}_")
        lines.append("")
        lines.append("| ID | Name | Type | Schedule | Output Files |")
        lines.append("|:---|:-----|:-----|:---------|:-------------|")

        for crawler in cat_crawlers:
            cid = crawler['id']
            name = crawler['name']
            ctype = crawler['type']
            schedule = crawler.get('schedule_human', crawler.get('schedule', '-'))
            files = ', '.join(crawler.get('expected_files', [])) or '-'

            # Truncate long file lists
            if len(files) > 50:
                files = files[:47] + "..."

            lines.append(f"| {cid} | {name} | {ctype} | {schedule} | `{files}` |")

        lines.append("")

    return '\n'.join(lines)


def update_readme(new_content):
    """Update README.md with new crawler tables."""
    if not README_FILE.exists():
        print(f"Warning: {README_FILE} not found, creating new file")
        with open(README_FILE, 'w', encoding='utf-8') as f:
            f.write(f"# GS Crawler\n\n{START_MARKER}\n{new_content}\n{END_MARKER}\n")
        return True

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find markers
    start_idx = content.find(START_MARKER)
    end_idx = content.find(END_MARKER)

    if start_idx == -1 or end_idx == -1:
        print("Warning: Markers not found in README.md")
        print(f"Add these markers where you want the crawler tables:")
        print(f"  {START_MARKER}")
        print(f"  {END_MARKER}")
        return False

    # Replace content between markers
    new_readme = (
        content[:start_idx + len(START_MARKER)] +
        "\n" + new_content + "\n" +
        content[end_idx:]
    )

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(new_readme)

    return True


def main():
    print("Loading crawler registry...")
    registry = load_registry()

    crawler_count = len(registry['crawlers'])
    print(f"Found {crawler_count} crawlers in registry")

    print("Generating crawler tables...")
    tables = generate_crawler_tables(registry)

    print("Updating README.md...")
    if update_readme(tables):
        print("  -> README.md updated")
    else:
        print("  -> Failed to update README.md (check for markers)")

    print("Done!")


if __name__ == '__main__':
    main()
