import hashlib
import json
import shutil
from datetime import date, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path("/app/output")
SOURCE_JSON_FILE = "004_zufaellig-nix-vor-alle.json"
EXPORT_JSON_FILE = "004_zufaellig-nix-vor.json"
EXPORT_ALL_JSON_FILE = "004_zufaellig-nix-vor-alle.json"
EXPORT_HTML_FILE = "004_zufaellig-nix-vor.html"
EXPORT_ALL_HTML_FILE = "004_zufaellig-nix-vor-alle.html"
INDEX_HTML_URL = "https://crawler.goslar.app/crawler/004_zufaellig-nix-vor.html"
UI_KIT_DIR = SCRIPT_DIR / "ui-kit"
EXPORT_UI_KIT_FILES = ["goslar-ui.css", "goslar-ui.js"]


def normalize_text(value):
    return " ".join(str(value or "").split()).strip()


def normalize_entry(entry, index):
    title = normalize_text(entry.get("title")) or "Zufällig nix vor?"
    description = normalize_text(entry.get("description"))
    image_url = normalize_text(entry.get("image_url")) or None
    call_to_action_url = normalize_text(entry.get("call_to_action_url")) or None
    published_at = normalize_text(entry.get("published_at")) or datetime.now().strftime("%Y-%m-%dT%H:%M")

    return {
        "id": index + 1,
        "title": title,
        "description": description,
        "image_url": image_url,
        "call_to_action_url": call_to_action_url,
        "published_at": published_at,
    }


def load_entries():
    path = SCRIPT_DIR / SOURCE_JSON_FILE
    with path.open("r", encoding="utf-8") as handle:
        raw_entries = json.load(handle)

    if not isinstance(raw_entries, list):
        raise ValueError(f"{SOURCE_JSON_FILE} muss eine JSON-Liste enthalten.")

    entries = [
        normalize_entry(entry, index)
        for index, entry in enumerate(raw_entries)
        if isinstance(entry, dict)
    ]
    entries = [entry for entry in entries if entry["description"] or entry["image_url"] or entry["call_to_action_url"]]

    if not entries:
        raise ValueError(f"{SOURCE_JSON_FILE} enthält keine nutzbaren Vorschläge.")

    return entries


def pick_daily_entry(entries):
    seed = f"004_zufaellig-nix-vor:{date.today().isoformat()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest[:12], 16) % len(entries)
    return entries[index]


def write_json(filename, payload):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
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


def write_html(entries, featured_entry):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = (SCRIPT_DIR / EXPORT_HTML_FILE).read_text(encoding="utf-8")
    html = html.replace("__SUGGESTIONS_JSON__", json_for_script(entries))
    html = html.replace("__FEATURED_ID__", str(featured_entry["id"]))
    target = OUTPUT_DIR / EXPORT_HTML_FILE
    target.write_text(html, encoding="utf-8")
    print(f"Written: {target}")


def write_all_html(entries):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = (SCRIPT_DIR / EXPORT_ALL_HTML_FILE).read_text(encoding="utf-8")
    html = html.replace("__SUGGESTIONS_JSON__", json_for_script(entries))
    target = OUTPUT_DIR / EXPORT_ALL_HTML_FILE
    target.write_text(html, encoding="utf-8")
    print(f"Written: {target}")


def copy_ui_kit():
    target_dir = OUTPUT_DIR / "ui-kit"
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in EXPORT_UI_KIT_FILES:
        source = UI_KIT_DIR / filename
        target = target_dir / filename
        shutil.copyfile(source, target)
        print(f"Copied: {target}")


def main():
    entries = load_entries()
    daily_entry = pick_daily_entry(entries)
    daily_card = {
        **daily_entry,
        "call_to_action_url": INDEX_HTML_URL,
        "widget_type": None,
    }

    write_json(EXPORT_JSON_FILE, daily_card)
    write_json(EXPORT_ALL_JSON_FILE, entries)
    write_html(entries, daily_entry)
    write_all_html(entries)
    copy_ui_kit()

    print(f"Exported {len(entries)} suggestions. Daily suggestion: {daily_entry['title']}")


if __name__ == "__main__":
    main()
