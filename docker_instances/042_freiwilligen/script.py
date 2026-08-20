import json
import os
import random
import re
import shutil
import sys
from datetime import datetime
from html import escape, unescape
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment

PORTAL_ID = "114"
AGENCY_ID = "25"
ACCESS_KEY = os.environ["FREIWILLIGEN_AGENTUR_API_KEY"].strip()

MATCHING_URL = "https://www.freinet-online.de/query/api/portal/v1/MatchingServiceEndpoint.php"
DETAIL_URL_TEMPLATE = (
    "https://www.freinet-online.de/query/iframe/print.php"
    f"?agid={AGENCY_ID}&styleid=2&frametyp=2&do=go&submit=Suchen&hideund=1&detail={{angebot_id}}"
)
INDEX_HTML_FILE = "042_freiwilligenagentur_index.html"
DETAIL_HTML_FILE = "042_freiwilligenagentur_detail.html"
INDEX_HTML_URL = f"https://crawler.goslar.app/crawler/{INDEX_HTML_FILE}"
OUTPUT_DIR = Path("output")
SCRIPT_DIR = Path(__file__).resolve().parent
UI_KIT_DIR = SCRIPT_DIR / "ui-kit"
EXPORT_UI_KIT_FILES = ["goslar-ui.css", "goslar-ui.js"]
ALLOWED_DESCRIPTION_TAGS = {"br", "p", "div", "ul", "ol", "li", "strong", "b", "em", "i", "u", "span", "font"}
REMOVED_DESCRIPTION_TAGS = {"script", "style", "iframe", "object", "embed", "link", "meta"}
SAFE_COLOR_PATTERN = re.compile(
    r"^(#[0-9a-fA-F]{3,8}|[a-zA-Z]+|rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}(?:\s*,\s*(?:0|1|0?\.\d+))?\s*\))$"
)


def get_tag_text(node, tag_name):
    tag = node.find(tag_name)
    if tag is None:
        return ""
    return " ".join(tag.stripped_strings).strip()


def get_tag_markup(node, tag_name):
    tag = node.find(tag_name)
    if tag is None:
        return ""
    return unescape("".join(str(child) for child in tag.contents)).strip()


def normalize_whitespace(value):
    return " ".join(value.split()).strip()


def normalize_description(value):
    value = re.sub(r"<[^>]+>", " ", unescape(value or ""))
    return normalize_whitespace(value)


def sanitize_color(value):
    value = normalize_whitespace(value).strip("'\"")
    if SAFE_COLOR_PATTERN.fullmatch(value):
        return value
    return ""


def extract_safe_color_from_style(style):
    for declaration in str(style or "").split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        if name.strip().lower() == "color":
            return sanitize_color(value.strip())
    return ""


def sanitize_description_html(value):
    value = unescape(value or "").strip()
    if not value:
        return ""

    if "<" not in value and ">" not in value:
        return "<br>".join(escape(line.strip()) for line in value.splitlines() if line.strip())

    soup = BeautifulSoup(value, "html.parser")

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    for tag in list(soup.find_all(True)):
        name = tag.name.lower()
        if name in REMOVED_DESCRIPTION_TAGS:
            tag.decompose()
            continue

        if name not in ALLOWED_DESCRIPTION_TAGS:
            tag.unwrap()
            continue

        safe_color = extract_safe_color_from_style(tag.get("style"))
        if name == "font" and not safe_color:
            safe_color = sanitize_color(tag.get("color", ""))

        tag.attrs = {}
        if safe_color:
            tag["style"] = f"color: {safe_color}"

        if name == "font":
            tag.name = "span"

    return str(soup).strip()


def html_to_plain_text(value):
    if not value:
        return ""
    return normalize_whitespace(BeautifulSoup(value, "html.parser").get_text(" ", strip=True))


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

    short_description_html = sanitize_description_html(get_tag_markup(offer, "kurz_beschreibung"))
    full_description_html = sanitize_description_html(get_tag_markup(offer, "beschreibung"))
    short_description = html_to_plain_text(short_description_html)
    full_description = html_to_plain_text(full_description_html)
    description = short_description or full_description
    description_html = short_description_html or full_description_html

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

    print_url = DETAIL_URL_TEMPLATE.format(angebot_id=offer_id)

    return {
        "id": int(offer_id),
        "title": title,
        "description": description,
        "description_html": description_html,
        "short_description": short_description,
        "short_description_html": short_description_html,
        "full_description": full_description,
        "full_description_html": full_description_html,
        "organization": organization or None,
        "location": location or None,
        "image_url": avatar or None,
        "call_to_action_url": f"{DETAIL_HTML_FILE}?id={offer_id}",
        "print_url": print_url,
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


def format_offer_count(offer_count):
    if offer_count == 1:
        return "1 Angebot zur ehrenamtlichen Unterstützung"
    return f"{offer_count} Angebote zur ehrenamtlichen Unterstützung"


def build_card(offer_count, published_at):
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


def write_detail_html(offers):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = (SCRIPT_DIR / DETAIL_HTML_FILE).read_text(encoding="utf-8")
    html = html.replace("__OFFERS_JSON__", json_for_script(offers))
    target = OUTPUT_DIR / DETAIL_HTML_FILE
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
    latest_published_at = max((offer["published_at"] for offer in offers), default=datetime.now().strftime("%Y-%m-%dT%H:%M"))

    write_json("042-freiwilligenagentur.json", build_card(len(offers), latest_published_at))
    write_json("042-freiwilligenagentur-alle.json", ordered_index)
    write_html(ordered_index)
    write_detail_html(ordered_index)
    copy_ui_kit()

    print(f"Fetched {len(offers)} active Freinet offers.")

if __name__ == "__main__":
    main()
