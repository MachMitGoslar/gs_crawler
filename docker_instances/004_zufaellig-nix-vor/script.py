import hashlib
import json
import shutil
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


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
EMBED_CHECK_TIMEOUT_SECONDS = 6
PUBLIC_ORIGIN = "{uri.scheme}://{uri.netloc}".format(uri=urlparse(INDEX_HTML_URL))


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


def enrich_embed_metadata(entries):
    return [
        {
            **entry,
            "can_embed_iframe": can_embed_iframe(entry.get("call_to_action_url")),
        }
        for entry in entries
    ]


def can_embed_iframe(url):
    if not url:
        return False

    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return False

    status_code, headers = fetch_response_metadata(url)
    if status_code and status_code >= 400:
        return False

    if not headers:
        return True

    return not blocks_iframe(headers, parsed_url)


def fetch_response_metadata(url):
    for method in ("HEAD", "GET"):
        request = Request(
            url,
            method=method,
            headers={
                "User-Agent": "GoslarAppCrawler/1.0 (+https://goslar.app)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urlopen(request, timeout=EMBED_CHECK_TIMEOUT_SECONDS) as response:
                return response.status, response.headers
        except HTTPError as error:
            if error.headers and has_frame_policy_header(error.headers):
                return error.code, error.headers
            if method == "HEAD":
                continue
            if error.headers:
                return error.code, error.headers
        except (TimeoutError, URLError, OSError):
            if method == "HEAD":
                continue

    return None, None


def has_frame_policy_header(headers):
    if headers.get("X-Frame-Options"):
        return True
    return any(get_csp_directive(value, "frame-ancestors") is not None for value in get_all_headers(headers, "Content-Security-Policy"))


def blocks_iframe(headers, parsed_url):
    x_frame_options = normalize_header(headers.get("X-Frame-Options"))
    if x_frame_options:
        if x_frame_options == "deny":
            return True
        if x_frame_options == "sameorigin" and not is_same_origin(parsed_url, PUBLIC_ORIGIN):
            return True
        if x_frame_options.startswith("allow-from "):
            allowed_origin = x_frame_options.removeprefix("allow-from ").strip()
            return normalize_origin(allowed_origin) != normalize_origin(PUBLIC_ORIGIN)

    for csp_header in get_all_headers(headers, "Content-Security-Policy"):
        frame_ancestors = get_csp_directive(csp_header, "frame-ancestors")
        if frame_ancestors is not None and not frame_ancestors_allows_public_origin(frame_ancestors, parsed_url):
            return True

    return False


def get_all_headers(headers, name):
    values = headers.get_all(name) if hasattr(headers, "get_all") else None
    if values:
        return values

    value = headers.get(name)
    return [value] if value else []


def get_csp_directive(csp_header, directive_name):
    for directive in str(csp_header or "").split(";"):
        parts = directive.strip().split()
        if parts and parts[0].lower() == directive_name:
            return [part.strip() for part in parts[1:]]
    return None


def frame_ancestors_allows_public_origin(sources, parsed_url):
    if not sources:
        return False

    public_origin = normalize_origin(PUBLIC_ORIGIN)
    target_origin = normalize_origin(f"{parsed_url.scheme}://{parsed_url.netloc}")

    for source in sources:
        normalized_source = source.strip().strip('"').lower()
        if normalized_source == "*":
            return True
        if normalized_source == "'none'":
            return False
        if normalized_source == "'self'" and public_origin == target_origin:
            return True
        if source_allows_origin(normalized_source, public_origin):
            return True

    return False


def source_allows_origin(source, origin):
    source = source.strip().strip("'")
    if not source:
        return False

    parsed_origin = urlparse(origin)
    if source in {"http:", "https:"}:
        return parsed_origin.scheme == source.rstrip(":")

    parsed_source = urlparse(source if "://" in source else f"//{source}", scheme="https")

    if parsed_source.scheme and parsed_source.scheme not in {"", parsed_origin.scheme}:
        return False

    source_host = parsed_source.hostname
    origin_host = parsed_origin.hostname
    if not source_host or not origin_host:
        return False

    source_port = parsed_source.port
    origin_port = parsed_origin.port
    if source_port and source_port != origin_port:
        return False

    if source_host.startswith("*."):
        suffix = source_host[1:]
        return origin_host.endswith(suffix)

    return source_host == origin_host


def is_same_origin(parsed_url, origin):
    return normalize_origin(f"{parsed_url.scheme}://{parsed_url.netloc}") == normalize_origin(origin)


def normalize_origin(origin):
    parsed = urlparse(origin)
    scheme = (parsed.scheme or "https").lower()
    host = (parsed.hostname or "").lower()
    port = f":{parsed.port}" if parsed.port else ""
    return f"{scheme}://{host}{port}"


def normalize_header(value):
    return " ".join(str(value or "").lower().split()).strip()


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
    entries = enrich_embed_metadata(load_entries())
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
