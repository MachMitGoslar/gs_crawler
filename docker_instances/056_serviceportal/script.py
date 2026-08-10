import json
import shutil
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path("/app/output")
UI_KIT_DIR = SCRIPT_DIR / "ui-kit"

IMAGE_URL = "https://crawler.goslar.app/crawler/056_serviceportal_image.png"
EXPORT_JSON_FILE = "056-serviceportal.json"
EXPORT_HTML_FILES = ["056_serviceportal_index.html", "056_serviceportal_termin.html"]
EXPORT_ASSET_FILES = ["056_serviceportal_image.png"]
EXPORT_UI_KIT_FILES = ["goslar-ui.css", "goslar-ui.js"]
UI_OUTPUT_DIR = "ui-kit"
INDEX_HTML_URL = "https://crawler.goslar.app/crawler/056_serviceportal_index.html"

entry = {
    "title": "Online-Dienstleistungen der Stadt Goslar",
    "description": "Termine buchen, Anträge stellen und weitere Online Dienstleistungen - probier uns aus!",
    "image_url": IMAGE_URL,
    "call_to_action_url": INDEX_HTML_URL,
    "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
}


def write_json() -> None:
    path = OUTPUT_DIR / EXPORT_JSON_FILE
    with path.open("w", encoding="utf-8") as handle:
        json.dump(entry, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Gespeichert: {path}")


def copy_static_files() -> None:
    for filename in [*EXPORT_HTML_FILES, *EXPORT_ASSET_FILES]:
        source = SCRIPT_DIR / filename
        target = OUTPUT_DIR / filename
        shutil.copyfile(source, target)
        print(f"Kopiert: {target}")
    ui_target_dir = OUTPUT_DIR / UI_OUTPUT_DIR
    ui_target_dir.mkdir(parents=True, exist_ok=True)
    for filename in EXPORT_UI_KIT_FILES:
        source = UI_KIT_DIR / filename
        target = ui_target_dir / filename
        shutil.copyfile(source, target)
        print(f"Kopiert: {target}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_json()
    copy_static_files()
    print("Erfolgreich gespeichert:", entry["title"])


if __name__ == "__main__":
    main()
