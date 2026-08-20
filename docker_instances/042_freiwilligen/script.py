import json
import os
import random
import re
import shutil
import sys
from datetime import datetime
from html import unescape
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PORTAL_ID = "114"
AGENCY_ID = "25"
ACCESS_KEY = os.environ["FREIWILLIGEN_AGENTUR_API_KEY"].strip()

MATCHING_URL = "https://www.freinet-online.de/query/api/portal/v1/MatchingServiceEndpoint.php"
DETAIL_URL_TEMPLATE = (
    "https://www.freinet-online.de/query/iframe/print.php"
    f"?agid={AGENCY_ID}&styleid=2&frametyp=2&do=go&submit=Suchen&hideund=1&detail={{angebot_id}}"
)
INDEX_HTML_FILE = "042_freiwilligenagentur_index.html"
INDEX_HTML_URL = f"https://crawler.goslar.app/crawler/{INDEX_HTML_FILE}"
OUTPUT_DIR = Path("output")
SCRIPT_DIR = Path(__file__).resolve().parent
UI_KIT_DIR = SCRIPT_DIR / "ui-kit"
EXPORT_UI_KIT_FILES = ["goslar-ui.css", "goslar-ui.js"]


def get_tag_text(node, tag_name):
    tag = node.find(tag_name)
    if tag is None:
        return ""
    return " ".join(tag.stripped_strings).strip()


def normalize_whitespace(value):
    return " ".join(value.split()).strip()


def normalize_description(value):
    value = re.sub(r"<[^>]+>", " ", unescape(value or ""))
    return normalize_whitespace(value)


def unix_to_iso8601(timestamp_text, fallback):
    timestamp_text = (timestamp_text or "").strip()
    if not timestamp_text:
        return fallback

    try:
        timestamp = int(timestamp_text)
    except ValueError:
        return fallback

    if timestamp <= 0:
        return fallback

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%dT%H:%M")


def build_offer_entry(offer, fallback_timestamp):
    offer_id = offer.get("angebotsid") or offer.get("angebotsId")
    if not offer_id:
        return None

    title = normalize_whitespace(get_tag_text(offer, "angebotsname"))
    if not title:
        return None

    short_description = normalize_description(get_tag_text(offer, "kurz_beschreibung"))
    full_description = normalize_description(get_tag_text(offer, "beschreibung"))
    description = short_description or full_description

    organization = normalize_whitespace(get_tag_text(offer, "einrichtungsname"))
    place_parts = [
        normalize_whitespace(get_tag_text(offer, "plz")),
        normalize_whitespace(get_tag_text(offer, "ort")),
    ]
    location = " ".join(part for part in place_parts if part).strip()

    if organization and location:
        description = f"{description} ({organization}, {location})" if description else f"{organization}, {location}"
    elif organization:
        description = f"{description} ({organization})" if description else organization
    elif location:
        description = f"{description} ({location})" if description else location

    description = normalize_description(description)

    avatar = normalize_whitespace(get_tag_text(offer, "avatar"))
    published_at = unix_to_iso8601(get_tag_text(offer, "bearbeitet"), fallback_timestamp)
    if published_at == fallback_timestamp:
        published_at = unix_to_iso8601(get_tag_text(offer, "erstellt"), fallback_timestamp)

    return {
        "id": int(offer_id),
        "title": "Freiwilligenagentur",
        "description": description,
        "image_url": avatar or None,
        "call_to_action_url": DETAIL_URL_TEMPLATE.format(angebot_id=offer_id),
        "published_at": published_at,
    }


def fetch_offers():
    response = requests.get(
        MATCHING_URL,
        params={
            "portalId": PORTAL_ID,
            "accessKey": ACCESS_KEY,
            "limit": 10000,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.text


def parse_offers(xml_text):
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M")
    soup = BeautifulSoup(xml_text, "xml")
    offers = []
    offer_ids = []

    for offer in soup.find_all("angebot"):
        entry = build_offer_entry(offer, now_iso)
        if entry is None:
            continue
        offers.append(entry)
        offer_ids.append(entry["id"])

    return offers, offer_ids


def build_card(featured_offer):
    return {
        "title": "Freiwilligenagentur",
        "description": format_offer_count(offer_count),
        "image_url": None,
        "call_to_action_url": INDEX_HTML_URL,
        "published_at": published_at,
        "widget_type": None,
    }


def write_json(filename, payload):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Written: {path}")


def json_for_script(data):
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def write_html(offers):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = (SCRIPT_DIR / INDEX_HTML_FILE).read_text(encoding="utf-8")
    html = html.replace("__OFFERS_JSON__", json_for_script(offers))
    target = OUTPUT_DIR / INDEX_HTML_FILE
    target.write_text(html, encoding="utf-8")
    print(f"Written: {target}")


def copy_ui_kit():
    target_dir = OUTPUT_DIR / "ui-kit"
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in EXPORT_UI_KIT_FILES:
        target = target_dir / filename
        shutil.copyfile(UI_KIT_DIR / filename, target)
        print(f"Copied: {target}")


def main():
    if not ACCESS_KEY:
        print("FREIWILLIGEN_AGENTUR_API_KEY is empty. Aborting before calling Freinet.", file=sys.stderr)
        sys.exit(1)

    xml_text = fetch_offers()
    offers, offer_ids = parse_offers(xml_text)

    if not offer_ids:
        print("Freinet returned no offer IDs. Aborting without overwriting output files.", file=sys.stderr)
        sys.exit(1)

    featured_offer = random.choice(offers)
    ordered_index = [featured_offer] + [offer for offer in offers if offer["id"] != featured_offer["id"]]

    write_json("042-freiwilligenagentur.json", build_card(featured_offer))
    write_json("042-freiwilligenagentur-alle.json", ordered_index)
    write_html(ordered_index)
    copy_ui_kit()

    print(f"Fetched {len(offers)} active Freinet offers.")

if __name__ == "__main__":
    main()
