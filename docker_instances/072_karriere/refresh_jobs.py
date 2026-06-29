"""Periodischer Export einer zufaelligen Karriere-Card nach /app/output."""

import json
import os
from datetime import datetime
from pathlib import Path
from random import SystemRandom

from jobs_logic import build_jobs_payload


BASE_URL = os.getenv("CRAWLER_BASE_URL", "https://crawler.goslar.app").rstrip("/")
INDEX_URL = os.getenv("KARRIERE_INDEX_URL", "https://crawler.goslar.app/karriere/?location=Goslar")
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/output"))
OUTPUT_FILE = OUTPUT_DIR / "072_karriere_card.json"
EMPTY_DESCRIPTION = "Aktuell sind keine passenden Jobangebote fuer den Landkreis Goslar verfuegbar."


def build_location_label(job: dict) -> str:
    location = job.get("location") or {}
    parts = [location.get("city"), location.get("postal_code"), location.get("region")]
    return ", ".join(str(part) for part in parts if part)


def build_card_description(job: dict) -> str:
    segments = []
    employer = job.get("employer")
    if employer:
        segments.append(f"Arbeitgeber: {employer}.")

    location_label = build_location_label(job)
    if location_label:
        segments.append(f"Ort: {location_label}.")

    category_label = job.get("category_label")
    if category_label:
        segments.append(f"Kategorie: {category_label}.")

    starts_at = job.get("starts_at")
    if starts_at:
        segments.append(f"Start: {starts_at}.")

    published_at = job.get("published_at")
    if published_at:
        segments.append(f"Veroeffentlicht: {published_at}.")

    return " ".join(segments) if segments else "Aktuelles Stellenangebot aus dem Landkreis Goslar."


def build_image_url(job: dict) -> str | None:
    logo_url = job.get("logo_url")
    if not logo_url:
        return None
    if str(logo_url).startswith(("http://", "https://")):
        return str(logo_url)
    return f"{BASE_URL}{logo_url}"


def build_empty_card(now_str: str) -> dict:
    return {
        "title": "Karriere Goslar",
        "description": EMPTY_DESCRIPTION,
        "image_url": None,
        "call_to_action_url": None,
        "published_at": now_str,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now().isoformat(sep="T", timespec="minutes")
    payload = build_jobs_payload({})
    jobs = payload.get("results") or []

    if not jobs:
        card = build_empty_card(now_str)
    else:
        selected_job = SystemRandom().choice(jobs)
        card = {
            "title": selected_job.get("title") or "Karriere Goslar",
            "description": build_card_description(selected_job),
            "image_url": build_image_url(selected_job),
            "call_to_action_url": INDEX_URL,
            "published_at": now_str,
        }

    with OUTPUT_FILE.open("w", encoding="utf-8") as output_file:
        json.dump(card, output_file, ensure_ascii=False, indent=2)

    print(f"Wrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
