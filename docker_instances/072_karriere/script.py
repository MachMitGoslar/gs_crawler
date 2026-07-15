"""Statischer Export des Karriereportals nach /app/output."""

import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from random import SystemRandom
from api_clients import fetch_logo
from config import DEFAULT_LOCATION
from jobs_logic import build_ba_job_url, build_jobs_payload, normalize_external_url


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path("/app/output")
UI_KIT_DIR = SCRIPT_DIR / "ui-kit"
LOGO_OUTPUT_DIR = OUTPUT_DIR / "072_logos"
LOGO_MANIFEST_FILE = LOGO_OUTPUT_DIR / "manifest.json"
CARD_JSON_FILE = "072_karriere_card.json"
JOBS_JSON_FILE = "072_jobs.json"
INDEX_HTML_FILE = "072_karriere_index.html"
EXPORT_UI_KIT_FILES = ["goslar-ui.css", "goslar-ui.js"]
EXPORT_STATIC_FILES = ["jobs.css", "jobs.js"]
BASE_URL = "https://crawler.goslar.app/crawler"
INDEX_URL = f"{BASE_URL}/{INDEX_HTML_FILE}?location=Goslar&wo=Goslar"
EMPTY_DESCRIPTION = "Aktuell sind keine passenden Jobangebote fuer den Landkreis Goslar verfuegbar."
MAX_LOGO_WORKERS = 8


def build_application_url(job: dict) -> str | None:
    raw = job.get("raw") if isinstance(job.get("raw"), dict) else {}
    external_url = normalize_external_url(raw.get("externeUrl")) or normalize_external_url(job.get("detail_url"))
    if external_url:
        return external_url

    job_id = str(job.get("id") or "").strip()
    if job_id and (raw.get("refnr") or job.get("source") in {"bundesapi", "ausbildung", "selbststaendigkeit", "praktikum"}):
        return build_ba_job_url(job_id)

    return normalize_external_url(job.get("click_url"))


def prepare_jobs(payload: dict, logo_urls: dict[str, str | None]) -> dict:
    jobs = payload.get("results") or []
    for job in jobs:
        job["click_url"] = build_application_url(job)
        job["fallback_url"] = job.get("click_url")
        job["logo_url"] = logo_urls.get(extract_logo_hash(job))
    payload["filters"] = {"location": DEFAULT_LOCATION, "wo": DEFAULT_LOCATION}
    return payload



def extract_logo_hash(job: dict | None) -> str:
    if not job:
        return ""
    raw = job.get("raw") if isinstance(job.get("raw"), dict) else {}
    return str(raw.get("arbeitgeberKundennummerHash") or raw.get("kundennummerHash") or "").strip()


def load_logo_manifest() -> dict[str, str | None]:
    try:
        if LOGO_MANIFEST_FILE.exists():
            data = json.loads(LOGO_MANIFEST_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return {str(key): value if isinstance(value, str) else None for key, value in data.items()}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def save_logo_manifest(manifest: dict[str, str | None]) -> None:
    LOGO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGO_MANIFEST_FILE.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def logo_suffix(content_type: str) -> str:
    normalized = content_type.casefold()
    if "png" in normalized:
        return ".png"
    if "jpeg" in normalized or "jpg" in normalized:
        return ".jpg"
    if "svg" in normalized:
        return ".svg"
    return ".webp"


def logo_filename(logo_hash: str, content_type: str) -> str:
    safe_hash = "".join(ch if ch.isalnum() else "-" for ch in logo_hash).strip("-")[:96]
    return f"{safe_hash or 'logo'}{logo_suffix(content_type)}"


def fetch_logo_asset(logo_hash: str) -> tuple[str, str | None]:
    try:
        body, content_type = fetch_logo(logo_hash)
    except Exception as exc:
        print(f"Logo konnte nicht geladen werden ({logo_hash[:16]}...): {exc}")
        return logo_hash, None

    filename = logo_filename(logo_hash, content_type)
    target = LOGO_OUTPUT_DIR / filename
    target.write_bytes(body)
    return logo_hash, f"072_logos/{filename}"


def export_logos(jobs: list[dict]) -> dict[str, str | None]:
    logo_hashes = sorted({extract_logo_hash(job) for job in jobs if extract_logo_hash(job)})
    manifest = load_logo_manifest()
    missing_hashes = [logo_hash for logo_hash in logo_hashes if logo_hash not in manifest]

    if missing_hashes:
        LOGO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=MAX_LOGO_WORKERS) as executor:
            futures = [executor.submit(fetch_logo_asset, logo_hash) for logo_hash in missing_hashes]
            for future in as_completed(futures):
                logo_hash, relative_path = future.result()
                manifest[logo_hash] = relative_path
        save_logo_manifest(manifest)

    return {logo_hash: manifest.get(logo_hash) for logo_hash in logo_hashes}


def build_location_label(job: dict) -> str:
    location = job.get("location") or {}
    parts = [location.get("city"), location.get("postal_code"), location.get("region")]
    return ", ".join(str(part) for part in parts if part)


def build_card_description(job: dict) -> str:
    segments = []
    if job.get("title"):
        segments.append(f"{job['title']}.")
    if job.get("employer"):
        segments.append(f"Arbeitgeber: {job['employer']}.")
    location_label = build_location_label(job)
    if location_label:
        segments.append(f"Ort: {location_label}.")
    if job.get("category_label"):
        segments.append(f"Kategorie: {job['category_label']}.")
    if job.get("starts_at"):
        segments.append(f"Start: {job['starts_at']}.")
    if job.get("published_at"):
        segments.append(f"Veroeffentlicht: {job['published_at']}.")
    return " ".join(segments) if segments else "Aktuelles Stellenangebot aus dem Landkreis Goslar."


def write_json(filename: str, data: object) -> None:
    target = OUTPUT_DIR / filename
    with target.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Gespeichert: {target}")


def render_template(source_name: str, replacements: dict[str, str]) -> str:
    html = (SCRIPT_DIR / source_name).read_text(encoding="utf-8")
    for old, new in replacements.items():
        html = html.replace(old, new)
    return html


def json_for_script(data: object) -> str:
    """Serialisiert JSON so, dass es sicher in einem Script-Block stehen kann."""
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def write_html(payload: dict) -> None:
    common = {
        '<link href="/ui-kit/goslar-ui.css" rel="stylesheet" />': '<link href="ui-kit/goslar-ui.css" rel="stylesheet" />',
        "__APP_BASE_PATH__": json.dumps(""),
    }
    index_html = render_template(
        "jobs.html",
        {
            **common,
            "__DEFAULT_LOCATION__": json.dumps(DEFAULT_LOCATION),
            "__JOBS_DATA_URL__": json.dumps(JOBS_JSON_FILE),
            "__JOBS_DATA_JSON__": json_for_script(payload),
            "__STATIC_INDEX_URL__": json.dumps(INDEX_HTML_FILE),
        },
    )
    (OUTPUT_DIR / INDEX_HTML_FILE).write_text(index_html, encoding="utf-8")
    print(f"Gespeichert: {OUTPUT_DIR / INDEX_HTML_FILE}")


def copy_ui_kit() -> None:
    target_dir = OUTPUT_DIR / "ui-kit"
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in EXPORT_UI_KIT_FILES:
        target = target_dir / filename
        shutil.copyfile(UI_KIT_DIR / filename, target)
        print(f"Kopiert: {target}")


def copy_static_assets() -> None:
    for filename in EXPORT_STATIC_FILES:
        target = OUTPUT_DIR / filename
        shutil.copyfile(SCRIPT_DIR / filename, target)
        print(f"Kopiert: {target}")


def build_card(payload: dict, now_str: str) -> dict:
    jobs = payload.get("results") or []
    if not jobs:
        return {
            "title": "Karriere Goslar",
            "description": EMPTY_DESCRIPTION,
            "image_url": None,
            "call_to_action_url": INDEX_URL,
            "published_at": now_str,
        }

    selected_job = SystemRandom().choice(jobs)
    return {
        "title": selected_job.get("title") or "Karriere Goslar",
        "description": build_card_description(selected_job),
        "image_url": None,
        "call_to_action_url": INDEX_URL,
        "published_at": selected_job.get("published_at") or now_str,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    now_str = datetime.now().isoformat(sep="T", timespec="minutes")

    raw_payload = build_jobs_payload({})
    logo_urls = export_logos(raw_payload.get("results") or [])
    payload = prepare_jobs(raw_payload, logo_urls)
    write_json(JOBS_JSON_FILE, payload)
    write_json(CARD_JSON_FILE, build_card(payload, now_str))
    write_html(payload)
    copy_static_assets()
    copy_ui_kit()


if __name__ == "__main__":
    main()
