"""Busflotte der Stadtbus Goslar GmbH als Card-/Index-/Detail-JSON."""

import json
import random
import re
import sys
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import urljoin

import requests

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

if Path("/app/output").exists():
    OUTPUT_DIR = Path("/app/output/busflotte")
else:
    OUTPUT_DIR = REPO_ROOT / "httpdocs" / "crawler" / "busflotte"

API_URL = "https://www.goebus.de/unternehmen/api.php"
COMPANY_ID = 27  # Stadtbus Goslar GmbH
COMPANY_URL = "https://www.goebus.de/unternehmen/stadtbus-goslar"
IMAGE_BASE_URL = "https://www.goebus.de/unternehmen/"
SOURCE_LABEL = "GöBUS – Das Omnibusportal"

BASE_URL = "https://crawler.goslar.app/crawler/busflotte"
CARD_FILE = "073_busflotte_card.json"
INDEX_FILE = "073_busflotte_alle.json"
DETAIL_FILE_TEMPLATE = "073_busflotte_{vehicle_number}.json"
DETAIL_FILE_PATTERN = "073_busflotte_*.json"


def fetch_fleet():
    response = requests.get(
        API_URL,
        params={"cid": COMPANY_ID, "cat": "fleet"},
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()

    if isinstance(payload, dict):
        payload = payload.get("data") or []

    return [vehicle for vehicle in payload if isinstance(vehicle, dict)]


def clean(value):
    return " ".join(str(value or "").split()).strip()


def absolute_image_url(path):
    path = clean(path)
    if not path:
        return None
    return urljoin(IMAGE_BASE_URL, path)


def drivetrain(manufacturer):
    """Antrieb aus dem Modellnamen ableiten - die API hat kein eigenes Feld."""
    model = clean(manufacturer)
    if re.search(r"\bElectric\b|\bE\b", model, flags=re.IGNORECASE):
        return "Elektro"
    return "Diesel"


def short_model(manufacturer):
    """Typbezeichnung in Klammern fuer Titel und Statistik weglassen."""
    return clean(re.sub(r"\s*\([^)]*\)", "", clean(manufacturer)))


def iso_timestamp(value, fallback):
    value = clean(value)
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern).strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            continue
    return fallback


def vehicle_title(vehicle):
    model = short_model(vehicle.get("manufacturer")) or "Bus"
    number = clean(vehicle.get("vehicle_number"))
    return f"Wagen {number} · {model}" if number else model


def vehicle_summary(vehicle):
    parts = [
        clean(vehicle.get("license_plate")),
        f"Baujahr {clean(vehicle.get('build_year'))}" if clean(vehicle.get("build_year")) else "",
        drivetrain(vehicle.get("manufacturer")),
    ]
    return " · ".join(part for part in parts if part)


def vehicle_images(vehicle):
    urls = []
    for key in ("image_small", "image_large"):
        url = absolute_image_url(vehicle.get(key))
        if url and url not in urls:
            urls.append(url)
    return urls


def detail_filename(vehicle):
    number = clean(vehicle.get("vehicle_number")) or clean(vehicle.get("id"))
    safe_number = "".join(ch if ch.isalnum() else "-" for ch in number).strip("-")
    return DETAIL_FILE_TEMPLATE.format(vehicle_number=safe_number)


def build_index_entry(vehicle, fallback_timestamp):
    images = vehicle_images(vehicle)
    return {
        "id": int(vehicle["id"]),
        "title": vehicle_title(vehicle),
        "description": vehicle_summary(vehicle),
        "image_url": images[0] if images else None,
        "call_to_action_url": f"{BASE_URL}/{detail_filename(vehicle)}",
        "published_at": iso_timestamp(vehicle.get("last_update"), fallback_timestamp),
    }


def build_detail(vehicle, fallback_timestamp):
    rows = [
        ("Wagennummer", clean(vehicle.get("vehicle_number"))),
        ("Kennzeichen", clean(vehicle.get("license_plate"))),
        ("Hersteller / Modell", clean(vehicle.get("manufacturer"))),
        ("Baujahr", clean(vehicle.get("build_year"))),
        ("Erstzulassung", clean(vehicle.get("first_registration"))),
        ("Antrieb", drivetrain(vehicle.get("manufacturer"))),
        ("Zeitraum", clean(vehicle.get("period"))),
        ("Historie", clean(vehicle.get("history"))),
        ("Anmerkung", clean(vehicle.get("notes"))),
    ]
    definitions = "".join(
        f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>" for label, value in rows if value
    )
    description = f"<dl>{definitions}</dl><p>Quelle: {escape(SOURCE_LABEL)}</p>"

    return {
        "id": int(vehicle["id"]),
        "title": vehicle_title(vehicle),
        "summary": vehicle_summary(vehicle),
        "description": description,
        "images": [{"url": url} for url in vehicle_images(vehicle)],
        "call_to_action_url": COMPANY_URL,
        "published_at": iso_timestamp(vehicle.get("last_update"), fallback_timestamp),
    }


def build_card_description(vehicles):
    electric = sum(1 for vehicle in vehicles if drivetrain(vehicle.get("manufacturer")) == "Elektro")
    years = sorted(clean(vehicle.get("build_year")) for vehicle in vehicles if clean(vehicle.get("build_year")).isdigit())
    brands = sorted({short_model(vehicle.get("manufacturer")).split(" ")[0] for vehicle in vehicles} - {""})

    sentences = [f"{len(vehicles)} Busse im Linienverkehr"]
    if electric:
        sentences[0] += f", davon {electric} mit Elektroantrieb"
    sentences[0] += "."
    if years:
        sentences.append(f"Baujahre {years[0]} bis {years[-1]}.")
    if brands:
        sentences.append(f"Fahrzeuge von {', '.join(brands)}.")
    sentences.append("Alle Fahrzeuge des Stadtbus Goslar im Überblick.")

    return " ".join(sentences)


def build_card(vehicles, featured_vehicle, fallback_timestamp):
    images = vehicle_images(featured_vehicle)
    return {
        "title": "Die Busflotte des Stadtbus Goslar",
        "description": build_card_description(vehicles),
        "image_url": images[0] if images else None,
        "call_to_action_url": f"{BASE_URL}/{INDEX_FILE}",
        "published_at": fallback_timestamp,
    }


def write_json(filename, payload):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Gespeichert: {path}")


def cleanup_detail_files(current_filenames):
    keep = set(current_filenames) | {CARD_FILE, INDEX_FILE}
    for path in OUTPUT_DIR.glob(DETAIL_FILE_PATTERN):
        if path.name not in keep:
            path.unlink()
            print(f"Entfernt: {path}")


def main():
    try:
        vehicles = fetch_fleet()
    except (requests.RequestException, ValueError) as exc:
        print(f"GöBUS-API nicht erreichbar oder unlesbar: {exc}", file=sys.stderr)
        sys.exit(1)

    vehicles = [vehicle for vehicle in vehicles if vehicle.get("id")]
    if not vehicles:
        print("GöBUS-API lieferte keine Fahrzeuge. Abbruch ohne Ueberschreiben.", file=sys.stderr)
        sys.exit(1)

    vehicles.sort(key=lambda vehicle: (len(clean(vehicle.get("vehicle_number"))), clean(vehicle.get("vehicle_number"))))
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M")

    detail_filenames = []
    for vehicle in vehicles:
        filename = detail_filename(vehicle)
        detail_filenames.append(filename)
        write_json(filename, build_detail(vehicle, now_iso))

    write_json(INDEX_FILE, [build_index_entry(vehicle, now_iso) for vehicle in vehicles])
    write_json(CARD_FILE, build_card(vehicles, random.choice(vehicles), now_iso))
    cleanup_detail_files(detail_filenames)

    print(f"{len(vehicles)} aktive Fahrzeuge der Stadtbus Goslar GmbH exportiert.")


if __name__ == "__main__":
    main()
