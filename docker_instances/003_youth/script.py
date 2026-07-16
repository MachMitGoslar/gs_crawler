import json
import re
import shutil
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from html import unescape
from pathlib import Path

OUTPUT_DIR = Path("/app/output")
SCRIPT_DIR = Path(__file__).resolve().parent
UI_KIT_DIR = SCRIPT_DIR / "ui-kit"
BASE_URL = "https://crawler.goslar.app/crawler"
CARD_FILE = "003_youth.json"
INDEX_FILE = "003_youth_index.json"
MAP_HTML_FILE = "003_youth_freizeitkarte.html"
EXPORT_UI_KIT_FILES = ["goslar-ui.css", "goslar-ui.js"]
EXPORT_IMAGE_FILES = ["Freizeitkarte.png", "JUZ.png", "Ferienpass.png", "Veranstaltungen.png"]
KML_URL = "https://www.google.com/maps/d/kml?mid=1UT8xTGLbmz_mEvqL9bdofeDhgjHIwFk&forcekml=1"
KML_NS = {"k": "http://www.opengis.net/kml/2.2"}


def write_json(filename: str, data: object) -> None:
    target = OUTPUT_DIR / filename
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Written: {target}")


def json_for_script(data: object) -> str:
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def write_map_html(map_data: dict) -> None:
    html = (SCRIPT_DIR / MAP_HTML_FILE).read_text(encoding="utf-8")
    html = html.replace("__YOUTH_MAP_DATA__", json_for_script(map_data))
    target = OUTPUT_DIR / MAP_HTML_FILE
    target.write_text(html, encoding="utf-8")
    print(f"Written: {target}")


def copy_ui_kit() -> None:
    target_dir = OUTPUT_DIR / "ui-kit"
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in EXPORT_UI_KIT_FILES:
        target = target_dir / filename
        shutil.copyfile(UI_KIT_DIR / filename, target)
        print(f"Copied: {target}")


def copy_image_assets() -> None:
    for filename in EXPORT_IMAGE_FILES:
        target = OUTPUT_DIR / filename
        shutil.copyfile(SCRIPT_DIR / filename, target)
        print(f"Copied: {target}")


def fetch_kml() -> bytes:
    request = urllib.request.Request(KML_URL, headers={"User-Agent": "gs-crawler/003-youth"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def parse_coordinates(value: str) -> tuple[float, float] | None:
    first = (value or "").strip().split()[0] if value else ""
    parts = first.split(",")
    if len(parts) < 2:
        return None
    try:
        return float(parts[1]), float(parts[0])
    except ValueError:
        return None


def placemark_coordinates(placemark: ET.Element) -> tuple[float, float] | None:
    for coordinates in placemark.findall(".//k:coordinates", KML_NS):
        parsed = parse_coordinates(coordinates.text or "")
        if parsed:
            return parsed
    return None


def description_lines(description: str) -> list[str]:
    text = unescape(description or "")
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "\n", text)
    lines = [re.sub(r"\s+", " ", line).strip(" ,") for line in text.splitlines()]
    return [line for line in lines if line]


def extract_address(description: str) -> str | None:
    lines = description_lines(description)
    for index, line in enumerate(lines):
        if not re.search(r"\b386\d{2}\b", line):
            continue

        street_line = None
        for candidate in reversed(lines[max(0, index - 4):index]):
            if re.search(r"\d", candidate) and not re.search(r"\b\d{1,2}[:.]\d{2}\b|Uhr|Montag|Dienstag|Mittwoch|Donnerstag|Freitag", candidate, re.IGNORECASE):
                street_line = candidate.rstrip(",")
                break

        if street_line:
            return f"{street_line}, {line}"
    return None


def parse_kml(kml: bytes) -> dict:
    root = ET.fromstring(kml)
    categories = []
    points = []

    for folder_index, folder in enumerate(root.findall(".//k:Folder", KML_NS), start=1):
        category = (folder.findtext("k:name", default="Weitere Orte", namespaces=KML_NS) or "Weitere Orte").strip()
        category_id = f"cat-{folder_index}"
        category_count = 0

        for placemark in folder.findall("k:Placemark", KML_NS):
            parsed = placemark_coordinates(placemark)
            if not parsed:
                continue

            lat, lon = parsed
            name = (placemark.findtext("k:name", default="Unbenannter Ort", namespaces=KML_NS) or "Unbenannter Ort").strip()
            description = placemark.findtext("k:description", default="", namespaces=KML_NS) or ""
            address = extract_address(description)
            category_count += 1
            point = {
                "id": f"{category_id}-{category_count}",
                "title": name,
                "category": category,
                "categoryId": category_id,
                "lat": lat,
                "lon": lon,
            }
            if address:
                point["address"] = address
            points.append(point)

        if category_count:
            categories.append({"id": category_id, "name": category, "count": category_count})

    return {
        "title": root.findtext(".//k:Document/k:name", default="Freizeitkarte", namespaces=KML_NS),
        "categories": categories,
        "points": points,
        "source": KML_URL,
        "updatedAt": datetime.now().isoformat(sep="T", timespec="minutes"),
    }


def load_map_data() -> dict:
    try:
        return parse_kml(fetch_kml())
    except Exception as exc:
        print(f"Youth map KML could not be loaded: {exc}")
        return {
            "title": "Freizeitkarte",
            "categories": [],
            "points": [],
            "source": KML_URL,
            "updatedAt": datetime.now().isoformat(sep="T", timespec="minutes"),
            "error": "Die Kartendaten konnten aktuell nicht geladen werden.",
        }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now().isoformat(sep="T", timespec="minutes")
    map_url = f"{BASE_URL}/{MAP_HTML_FILE}"
    map_data = load_map_data()

    write_json(CARD_FILE, {
        "title": "GoslarTeens",
        "image_url": None,
        "description": "Freizeitangebote, Treffpunkte und Informationen für Jugendliche in Goslar.",
        "call_to_action_url": f"{BASE_URL}/{INDEX_FILE}",
        "published_at": now,
    })

    write_json(INDEX_FILE, [
        {
            "id": 1,
            "title": "Jugendzentren",
            "image_url": f"{BASE_URL}/JUZ.png",
            "description": "Jugendzentren und Angebote vor Ort in Goslar entdecken.",
            "call_to_action_url": "https://jugend.goslar.de/vor-ort",
            "published_at": now,
        },
        {
            "id": 2,
            "title": "Freizeitkarte",
            "image_url": f"{BASE_URL}/Freizeitkarte.png",
            "description": "Entdecke Jugendorte und Freizeitangebote in Goslar auf einer interaktiven Karte.",
            "call_to_action_url": map_url,
            "published_at": now,
        },
        {
            "id": 3,
            "title": "Ferienpass",
            "image_url": f"{BASE_URL}/Ferienpass.png",
            "description": "Aktuelle Ferienpass-Angebote aus dem Ferienprogramm Goslar.",
            "call_to_action_url": f"https://goslar.feripro.de/anmeldung/76/veranstaltungen",
            "published_at": now,
        },
        {
            "id": 4,
            "title": "Veranstaltungen",
            "image_url": f"{BASE_URL}/Veranstaltungen.png",
            "description": "Veranstaltungen für dich. #GoslarTeens",
            "call_to_action_url": "https://jugend.goslar.de/#c1262",
            "published_at": now,
        },
    ])

    write_map_html(map_data)
    copy_image_assets()
    copy_ui_kit()


if __name__ == "__main__":
    main()
