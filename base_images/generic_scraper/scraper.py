#!/usr/bin/env python3
"""
Generic web scraper engine.
Parses websites based on YAML configuration files.
"""
import sys
import os
import json
import random
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup

from config_loader import load_config, get_selector_config


OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/app/output')


def fetch_page(url: str) -> BeautifulSoup:
    """Fetch and parse a webpage."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; GS-Crawler/1.0; +https://goslar.app)'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, 'html.parser')


def extract_value(element, selector_config: Dict[str, Any], base_url: str = '') -> Optional[str]:
    """Extract a value from an element using selector config."""
    selector = selector_config.get('selector', '')
    attribute = selector_config.get('attribute', 'text')
    prefix = selector_config.get('prefix', '')
    fallback = selector_config.get('fallback')
    default = selector_config.get('default')

    if not selector:
        return default

    found = element.select_one(selector)
    if not found:
        return fallback if fallback is not None else default

    # Extract value based on attribute type
    if attribute == 'text':
        value = found.get_text(strip=True)
    elif attribute in ('href', 'src', 'id'):
        value = found.get(attribute, '')
    else:
        value = found.get(attribute, '')

    if value and prefix:
        # Don't add prefix if value is already absolute URL
        if not value.startswith(('http://', 'https://')):
            value = prefix + value

    return value if value else (fallback if fallback is not None else default)


def scrape_simple(soup: BeautifulSoup, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape using simple container-based approach."""
    selectors = config['selectors']
    base_url = config.get('base_url', config['url'])

    container_selector = selectors.get('container', '')
    if not container_selector:
        print(f"Warning: No container selector defined for {config['id']}")
        return []

    containers = soup.select(container_selector)
    print(f"Found {len(containers)} items for {config['id']}")

    entries = []
    for index, container in enumerate(containers):
        entry = {
            'id': index + 1,
            'title': extract_value(container, get_selector_config(selectors, 'title'), base_url),
            'description': extract_value(container, get_selector_config(selectors, 'description'), base_url),
            'image_url': extract_value(container, get_selector_config(selectors, 'image_url'), base_url),
            'call_to_action_url': extract_value(container, get_selector_config(selectors, 'call_to_action_url'), base_url),
            'published_at': datetime.now().strftime('%Y-%m-%dT%H:%M')
        }

        # Only add entries that have at least a title or description
        if entry['title'] or entry['description']:
            entries.append(entry)

    return entries


def scrape_nested(soup: BeautifulSoup, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Scrape using nested container approach (for tschuessschule-style pages)."""
    selectors = config['selectors']
    base_url = config.get('base_url', config['url'])
    url = config['url']

    container_selector = selectors.get('container', '')
    containers = soup.select(container_selector)

    entries = []
    entry_id = 1

    for container in containers:
        # Get category title from container
        category_config = get_selector_config(selectors, 'category_title')
        category_title = extract_value(container, category_config, base_url)

        # Get items config
        items_config = selectors.get('items', {})
        items_selector = items_config.get('selector', '')

        if not items_selector:
            continue

        items = container.select(items_selector)

        for item in items:
            # Extract image
            image_config = items_config.get('image_url', {})
            image_url = extract_value(item, image_config, base_url) if image_config else None

            # Build call_to_action_url
            cta_config = items_config.get('call_to_action_url', {})
            if cta_config.get('template'):
                item_id = item.get(cta_config.get('item_id_attribute', 'id'), '')
                call_to_action_url = cta_config['template'].format(url=url, item_id=item_id)
            else:
                call_to_action_url = extract_value(item, cta_config, base_url)

            entry = {
                'id': entry_id,
                'title': config['output']['single'].get('title_override', category_title),
                'description': category_title,
                'image_url': image_url,
                'call_to_action_url': call_to_action_url,
                'published_at': ''
            }

            entries.append(entry)
            entry_id += 1

    return entries


def select_single(entries: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
    """Select a single entry based on selection strategy."""
    if not entries:
        return {}

    strategy = config.get('selection', {}).get('strategy', 'random')

    if strategy == 'first':
        selected = entries[0].copy()
    elif strategy == 'random':
        selected = random.choice(entries).copy()
    elif strategy == 'latest':
        # Sort by published_at if available
        sorted_entries = sorted(
            entries,
            key=lambda x: x.get('published_at', ''),
            reverse=True
        )
        selected = sorted_entries[0].copy()
    else:
        selected = entries[0].copy()

    return selected


def apply_post_processing(entry: Dict[str, Any], all_entries: List[Dict], config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply post-processing to the single entry."""
    post_process = config.get('post_process', {})
    output_config = config.get('output', {}).get('single', {})

    # Apply title override
    if 'title_override' in output_config:
        entry['title'] = output_config['title_override']

    # Apply description template
    template = post_process.get('single_description_template')
    if template:
        entry['description'] = template.format(
            title=entry.get('title', ''),
            description=entry.get('description', ''),
            count=len(all_entries)
        )

    # Apply CTA override
    if 'cta_override' in output_config:
        all_filename = config.get('output', {}).get('all', {}).get('filename', '')
        entry['call_to_action_url'] = output_config['cta_override'].format(
            all_filename=all_filename
        )

    return entry


def save_output(entries: List[Dict], single_entry: Dict, config: Dict[str, Any]):
    """Save output files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_config = config.get('output', {})

    # Save "all" file
    if output_config.get('all', {}).get('enabled', False):
        all_filename = output_config['all'].get('filename', f"{config['id']}-alle.json")
        all_path = os.path.join(OUTPUT_DIR, all_filename)
        with open(all_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(entries)} entries to {all_filename}")

    # Save "single" file
    if output_config.get('single', {}).get('enabled', False) and single_entry:
        single_filename = output_config['single'].get('filename', f"{config['id']}.json")
        single_path = os.path.join(OUTPUT_DIR, single_filename)
        with open(single_path, 'w', encoding='utf-8') as f:
            json.dump(single_entry, f, ensure_ascii=False, indent=2)
        print(f"Saved single entry to {single_filename}")


def run_scraper(config_path: str):
    """Main scraper execution."""
    print(f"\n{'='*50}")
    print(f"Starting scraper at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Config: {config_path}")
    print(f"{'='*50}")

    try:
        # Load config
        config = load_config(config_path)
        print(f"Crawler: {config['name']} ({config['id']})")
        print(f"URL: {config['url']}")

        # Fetch page
        soup = fetch_page(config['url'])

        # Scrape based on type
        scraper_type = config.get('type', 'simple')
        if scraper_type == 'nested':
            entries = scrape_nested(soup, config)
        else:
            entries = scrape_simple(soup, config)

        if not entries:
            print(f"No entries found for {config['id']}")
            return

        print(f"Scraped {len(entries)} entries")

        # Select single entry
        single_entry = select_single(entries, config)

        # Apply post-processing
        if single_entry:
            single_entry = apply_post_processing(single_entry, entries, config)

        # Save output
        save_output(entries, single_entry, config)

        print(f"Scraper {config['id']} completed successfully")

    except Exception as e:
        print(f"Error in scraper: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <config_path>")
        print("       python scraper.py /app/configs/002_gz.yaml")
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    run_scraper(config_path)
