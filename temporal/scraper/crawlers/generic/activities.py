from __future__ import annotations

import json
import os
from dataclasses import asdict

import requests
from bs4 import BeautifulSoup
from temporalio import activity

from crawlers.generic.helpers import scrape_simple, scrape_nested
from crawlers.generic.models import (
    GenericCrawlerConfig,
    ScrapedEntry,
    SingleCard,
)

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")


@activity.defn
async def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GS-Crawler/1.0; +https://goslar.app)"
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    activity.heartbeat(f"fetched {len(response.text)} bytes")
    return response.text


@activity.defn
async def scrape_entries(cfg: GenericCrawlerConfig, html: str) -> list[dict]:
    """Returns list of dicts so it serialises cleanly for Temporal history."""
    soup = BeautifulSoup(html, "html.parser")
    entries = (
        scrape_nested(soup, cfg) if cfg.type == "nested" else scrape_simple(soup, cfg)
    )
    return [asdict(e) for e in entries]


@activity.defn
async def select_and_post_process(
    cfg: GenericCrawlerConfig, entries: list[dict]
) -> dict | None:
    if not entries:
        return None

    scraped = [ScrapedEntry(**e) for e in entries]

    if cfg.selection.strategy == "first":
        chosen = scraped[0]
    elif cfg.selection.strategy == "latest":
        chosen = sorted(scraped, key=lambda e: e.published_at, reverse=True)[0]
    else:  # 'random'
        import random
        chosen = random.choice(scraped)

    card = SingleCard(
        title=chosen.title,
        description=chosen.description,
        image_url=chosen.image_url,
        call_to_action_url=chosen.call_to_action_url,
        published_at=chosen.published_at,
    )

    # Description template
    if cfg.post_process.single_description_template:
        card.description = cfg.post_process.single_description_template.format(
            title=card.title or "",
            description=card.description or "",
            count=len(entries),
        )

    # Single-card overrides
    single_out = cfg.output.single
    if single_out.title_override:
        card.title = single_out.title_override
    if single_out.image_override:
        card.image_url = single_out.image_override
    if single_out.cta_override:
        card.call_to_action_url = single_out.cta_override.format(
            all_filename=cfg.output.all.filename or ""
        )

    return asdict(card)

@activity.defn
async def save_output(
    cfg: GenericCrawlerConfig, entries: list[dict], single: dict | None
) -> None:
    out_dir = os.path.join(OUTPUT_DIR, cfg.id)
    os.makedirs(out_dir, exist_ok=True)

    if cfg.output.all.enabled:
        filename = cfg.output.all.filename or f"{cfg.id}-alle.json"
        with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        activity.logger.info("wrote %s (%d entries)", filename, len(entries))

    if cfg.output.single.enabled and single is not None:
        filename = cfg.output.single.filename or f"{cfg.id}.json"
        with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as f:
            json.dump(single, f, ensure_ascii=False, indent=2)
        activity.logger.info("wrote %s", filename)
