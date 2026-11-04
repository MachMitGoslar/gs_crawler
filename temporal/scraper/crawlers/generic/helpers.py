"""Pure parsing helpers. No network, no disk, no Temporal imports."""
from __future__ import annotations

import copy
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

from bs4 import BeautifulSoup

from crawlers.generic.models import (
    GenericCrawlerConfig,
    ScrapedEntry,
    Selector,
)

PUBLISHED_AT_FORMAT = '%Y-%m-%dT%H:%M'

GERMAN_MONTHS = {
    'januar': 1, 'jan': 1, 'februar': 2, 'feb': 2, 'märz': 3, 'maerz': 3, 'mär': 3,
    'april': 4, 'apr': 4, 'mai': 5, 'juni': 6, 'jun': 6, 'juli': 7, 'jul': 7,
    'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9, 'oktober': 10, 'okt': 10,
    'november': 11, 'nov': 11, 'dezember': 12, 'dez': 12,
}


def _german_month_to_number(value: str, date_format: str):
    """Replace a German month name in value by its number (and %B/%b in the format by %m).

    strptime's %B/%b depend on the process locale, which is C in the container, so German
    names would never match there.
    """
    def replace(match):
        number = GERMAN_MONTHS.get(match.group(0).lower().rstrip('.'))
        return str(number) if number else match.group(0)

    value = re.sub(r'[A-Za-zäöüÄÖÜ]+\.?', replace, value, count=1)
    return value, date_format.replace('%B', '%m').replace('%b', '%m')


def parse_published_at(value: Optional[str], date_format: Optional[str] = None) -> Optional[str]:
    """Normalize a date from the page to PUBLISHED_AT_FORMAT, or None if it cannot be parsed.

    date_format is a strptime pattern (e.g. '%d.%m.%Y'); without it ISO 8601 is expected
    ('2026-10-25', '2026-10-25T10:00:00+01:00', '...Z'). German month names work with
    %B/%b regardless of the locale ('23. Oktober' with '%d. %B'). If the format has no year
    the current year is used, or the previous one if that would put the date in the future
    (a December date seen in January). Time zones are dropped, the wall-clock time is kept.
    """
    if not value:
        return None
    value = value.strip()
    try:
        if date_format:
            if '%B' in date_format or '%b' in date_format:
                value, date_format = _german_month_to_number(value, date_format)
            has_year = '%Y' in date_format or '%y' in date_format
            now = datetime.now()
            if not has_year:
                value, date_format = f"{value} {now.year}", f"{date_format} %Y"
            parsed = datetime.strptime(value, date_format)
            if not has_year and parsed > now + timedelta(days=1):
                parsed = parsed.replace(year=parsed.year - 1)
        else:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    return parsed.strftime(PUBLISHED_AT_FORMAT)

def extract_value(
    element, selector_config: Optional[Selector], base_url: str = ""
) -> Optional[str]:
    """Extract one field from an element using a Selector. Returns None if
    the selector is missing or yields nothing, honouring fallback/default."""
    if selector_config is None or not selector_config.selector:
        return selector_config.default if selector_config else None

    cfg = selector_config
    found = element.select_one(cfg.selector)
    if not found:
        return cfg.fallback if cfg.fallback is not None else cfg.default

    if cfg.attribute == "text":
        if cfg.exclude:
            found = copy.copy(found)
            for unwanted in found.select(cfg.exclude):
                unwanted.decompose()
        value = found.get_text(strip=True)
    else:
        value = found.get(cfg.attribute, "")

    if value and cfg.regex:
        match = re.search(cfg.regex, value)
        value = (
            match.group(1) if match and match.groups() else match.group(0)
        ) if match else ""

    if value and cfg.prefix and not value.startswith(("http://", "https://")):
        value = cfg.prefix + value

    return value or (cfg.fallback if cfg.fallback is not None else cfg.default)


def scrape_simple(soup: BeautifulSoup, cfg: GenericCrawlerConfig) -> list[ScrapedEntry]:
    s = cfg.selectors
    if not s.container:
        raise ValueError(f"No container selector for {cfg.id}")

    entries: list[ScrapedEntry] = []
    for container in soup.select(s.container):
        published_at = ""
        if s.published_at and s.published_at.selector:
            raw = extract_value(container, s.published_at, cfg.base_url)
            parsed = parse_published_at(raw, s.published_at.date_format)
            if raw and parsed is None:
                logging.warning(f"Warning: {cfg.id}: unparseable published_at '{raw}'")
            published_at = parsed or datetime.now().strftime(PUBLISHED_AT_FORMAT)

        entry = ScrapedEntry(
            title=extract_value(container, s.title, cfg.base_url),
            description=extract_value(container, s.description, cfg.base_url),
            image_url=extract_value(container, s.image_url, cfg.base_url),
            call_to_action_url=extract_value(container, s.call_to_action_url, cfg.base_url),
            published_at=published_at,
        )
        if entry.has_content:
            entries.append(entry)
    return entries


def scrape_nested(soup: BeautifulSoup, cfg: GenericCrawlerConfig) -> list[ScrapedEntry]:
    s = cfg.selectors
    if not s.items or not s.items.selector:
        return []

    entries: list[ScrapedEntry] = []
    for container in soup.select(s.container):
        category_title = extract_value(container, s.category_title, cfg.base_url)

        for item in container.select(s.items.selector):
            image_url = (
                extract_value(item, s.items.image_url, cfg.base_url)
                if s.items.image_url else None
            )
            cta_cfg = s.items.call_to_action_url
            if cta_cfg and cta_cfg.template:
                item_id = item.get(cta_cfg.item_id_attribute, "")
                cta = cta_cfg.template.format(url=cfg.url, item_id=item_id)
            else:
                cta = extract_value(item, cta_cfg, cfg.base_url)

            entries.append(ScrapedEntry(
                title=cfg.output.single.title_override or category_title,
                description=category_title,
                image_url=image_url,
                call_to_action_url=cta,
                published_at="",
            ))
    return entries