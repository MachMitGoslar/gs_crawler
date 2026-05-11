import json
import shutil
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

if Path("/app/output").exists():
    OUTPUT_DIR = Path("/app/output")
else:
    OUTPUT_DIR = REPO_ROOT / "httpdocs" / "crawler"

# Der Registry-Eintrag erwartet aktuell den historischen Dateinamen mit
CARD_OUTPUT_FILES = (
    "060-defi-kataster.json",
)

STATIC_ASSETS = ("index.html", "script.js", "style.css")
LOCATIONS_FILE = "data.json"
SOURCE_LOCATIONS_FILE = SCRIPT_DIR / LOCATIONS_FILE
MAP_OUTPUT_DIR = "060_defi_kataster"


MAP_URL = "https://crawler.goslar.app/crawler/060_defi_kataster/index.html"
IMAGE_URL = None

PUBLISHED_AT = datetime.now().strftime("%Y-%m-%dT%H:%M")


CARD = {
    "title": "Defibrillatoren-Kataster Goslar",
    "description": (
        "Schnell den naechsten Defibrillator in Goslar finden: "
        "Standorte, Verfuegbarkeit und Navigation in der Kartenansicht."
    ),
    "image_url": IMAGE_URL,
    "call_to_action_url": MAP_URL,
    "published_at": PUBLISHED_AT,
}


def ensure_output_dir():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def write_json(data):
    for filename in CARD_OUTPUT_FILES:
        path = OUTPUT_DIR / filename
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        print(f"Gespeichert: {path}")


def write_locations():
    map_dir = OUTPUT_DIR / MAP_OUTPUT_DIR
    map_dir.mkdir(parents=True, exist_ok=True)
    path = map_dir / LOCATIONS_FILE
    shutil.copyfile(SOURCE_LOCATIONS_FILE, path)
    print(f"Gespeichert: {path}")


def publish_static_assets():
    map_dir = OUTPUT_DIR / MAP_OUTPUT_DIR
    map_dir.mkdir(parents=True, exist_ok=True)

    for asset in STATIC_ASSETS:
        source = SCRIPT_DIR / asset
        if not source.exists():
            continue
        target = map_dir / asset
        shutil.copyfile(source, target)
        print(f"Kopiert: {target}")


def main():
    ensure_output_dir()
    write_json(CARD)
    write_locations()
    publish_static_assets()


if __name__ == "__main__":
    main()
