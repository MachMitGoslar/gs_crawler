import json
import math
import re
import ssl
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path("/app/output")
UI_KIT_DIR = SCRIPT_DIR / "ui-kit"

EXPORT_JSON_FILE = "080_bereitschaftsdienste_card.json"
CARD_IMAGE_FILE = "080_bereitschaftsdienste_card.png"
UI_CSS_FILE = "goslar-ui.css"
UI_JS_FILE = "goslar-ui.js"
UI_OUTPUT_DIR = "ui-kit"
INDEX_HTML_FILE = "080_bereitschaftsdienste_index.html"
MEDICAL_HTML_FILE = "080_bereitschaftsdienste_medizinisch.html"
SAFETY_HTML_FILE = "080_bereitschaftsdienste_sicherheit.html"
CITY_HTML_FILE = "080_bereitschaftsdienste_staedtisch.html"
PHARMACY_CACHE_FILE = "080_bereitschaftsdienste_apotheke_cache.json"
DOCTOR_CACHE_FILE = "080_bereitschaftsdienste_arztpraxis_cache.json"
DENTIST_CACHE_FILE = "080_bereitschaftsdienste_zahnarzt_cache.json"
INDEX_HTML_URL = "https://crawler.goslar.app/crawler/080_bereitschaftsdienste_index.html"
CARD_IMAGE_URL = "https://crawler.goslar.app/crawler/080_bereitschaftsdienste_card.png"
CACHE_VERSION = 11

GOSLAR_LAT = 51.90355041574386
GOSLAR_LON = 10.436801399999984
APOTHEKEN_API_URL = (
    "https://suche.apotheken.de/search"
    "?around=51.90355041574386%2C10.436801399999984"
    "&radius=29&emergencyDays=1&orderBy=distanceAsc"
)
APOTHEKEN_AUTH_TOKEN = "uKs1pxszpo7IGpkOXwH1HFDSyEs1Fqmr"
DOCTOR_API_URL = "https://bereitschaftspraxen.116117.de/api/data"
DOCTOR_AUTH_TOKEN = "YmRwczpma3I0OTNtdmdfZg=="
DOCTOR_REQ_VAL = "MzEyMjAwNw=="
DENTIST_SERVICE_URL = "https://www.schaabner-haase.de/service.php"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
LOCAL_TZ = ZoneInfo("Europe/Berlin")


entry = {
    "title": "Bereitschaftsdienste",
    "description": "Alle Notdienste der Stadt Goslar auf einen Blick – schnell finden, direkt erreichen und im Ernstfall sofort handeln.",
    "image_url": CARD_IMAGE_URL,
    "call_to_action_url": INDEX_HTML_URL,
    "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M"),
}


def write_json() -> None:
    path = OUTPUT_DIR / EXPORT_JSON_FILE
    with path.open("w", encoding="utf-8") as handle:
        json.dump(entry, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Gespeichert: {path}")


def copy_index_file() -> None:
    source = SCRIPT_DIR / INDEX_HTML_FILE
    target = OUTPUT_DIR / INDEX_HTML_FILE
    shutil.copyfile(source, target)
    print(f"Kopiert: {target}")


def copy_card_image_file() -> None:
    source = SCRIPT_DIR / CARD_IMAGE_FILE
    target = OUTPUT_DIR / CARD_IMAGE_FILE
    shutil.copyfile(source, target)
    print(f"Kopiert: {target}")


def copy_ui_kit_files() -> None:
    target_dir = OUTPUT_DIR / UI_OUTPUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    for filename in [UI_CSS_FILE, UI_JS_FILE]:
        source = UI_KIT_DIR / filename
        target = target_dir / filename
        shutil.copyfile(source, target)
        print(f"Kopiert: {target}")


def copy_safety_file() -> None:
    source = SCRIPT_DIR / SAFETY_HTML_FILE
    target = OUTPUT_DIR / SAFETY_HTML_FILE
    shutil.copyfile(source, target)
    print(f"Kopiert: {target}")


def copy_city_file() -> None:
    source = SCRIPT_DIR / CITY_HTML_FILE
    target = OUTPUT_DIR / CITY_HTML_FILE
    shutil.copyfile(source, target)
    print(f"Kopiert: {target}")


def write_medical_file(pharmacy: dict[str, str], doctor: dict[str, str], dentist: dict[str, str]) -> None:
    source = SCRIPT_DIR / MEDICAL_HTML_FILE
    target = OUTPUT_DIR / MEDICAL_HTML_FILE
    html = source.read_text(encoding="utf-8")
    replacements = {
        "__PHARMACY_NAME__": pharmacy.get("name") or "Keine Notdienstapotheke gefunden",
        "__PHARMACY_ADDRESS__": pharmacy.get("address") or "Adresse nicht verfügbar",
        "__PHARMACY_DISTANCE__": pharmacy.get("distance_label") or "- km entfernt",
        "__PHARMACY_PHONE__": pharmacy.get("telephone") or "Keine Telefonnummer",
        "__PHARMACY_TEL_HREF__": pharmacy.get("telephone_href") or "#",
        "__PHARMACY_ROUTE_HREF__": pharmacy.get("route_href") or "#",
        "__PHARMACY_EXTERNAL_HREF__": "https://www.apotheken.de/apotheken-und-notdienste-suchen/goslar/",
        "__PHARMACY_LAT__": pharmacy.get("latitude") or "",
        "__PHARMACY_LON__": pharmacy.get("longitude") or "",
        "__DOCTOR_NAME__": doctor.get("name") or "Keine Bereitschaftspraxis gefunden",
        "__DOCTOR_ADDRESS__": doctor.get("address") or "Adresse nicht verfügbar",
        "__DOCTOR_DISTANCE__": doctor.get("distance_label") or "- km entfernt",
        "__DOCTOR_PHONE__": doctor.get("telephone") or "116117",
        "__DOCTOR_TEL_HREF__": doctor.get("telephone_href") or "tel:116117",
        "__DOCTOR_ROUTE_HREF__": doctor.get("route_href") or "#",
        "__DOCTOR_EXTERNAL_HREF__": "https://bereitschaftspraxen.116117.de/",
        "__DOCTOR_LAT__": doctor.get("latitude") or "",
        "__DOCTOR_LON__": doctor.get("longitude") or "",
        "__DENTIST_NAME__": dentist.get("name") or "Kein zahnärztlicher Notdienst gefunden",
        "__DENTIST_ADDRESS__": dentist.get("address") or "Adresse nicht verfügbar",
        "__DENTIST_DISTANCE__": dentist.get("distance_label") or "- km entfernt",
        "__DENTIST_PHONE__": dentist.get("telephone") or "Keine Telefonnummer",
        "__DENTIST_TEL_HREF__": dentist.get("telephone_href") or "#",
        "__DENTIST_ROUTE_HREF__": dentist.get("route_href") or "#",
        "__DENTIST_EXTERNAL_HREF__": dentist.get("external_href") or DENTIST_SERVICE_URL,
        "__DENTIST_LAT__": dentist.get("latitude") or "",
        "__DENTIST_LON__": dentist.get("longitude") or "",
        "__DENTIST_DATE__": dentist.get("date_label") or "",
    }
    for key, value in replacements.items():
        html = html.replace(key, escape_html(value))
    target.write_text(html, encoding="utf-8")
    print(f"Gerendert: {target}")


def get_current_pharmacy() -> dict[str, str]:
    cached = read_valid_pharmacy_cache()
    if cached:
        print("Notdienstapotheke aus Cache verwendet bis", cached.get("duty_end"))
        return cached

    try:
        pharmacy = fetch_current_pharmacy()
        write_pharmacy_cache(pharmacy)
        return pharmacy
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"Apotheken API fehlgeschlagen: {exc}")
        fallback = read_pharmacy_cache(ignore_expiry=True)
        if fallback:
            print("Abgelaufenen Apotheken-Cache als Fallback verwendet")
            return fallback
        return fallback_pharmacy()


def get_current_doctor_practice() -> dict[str, str]:
    cached = read_valid_doctor_cache()
    if cached:
        print("Bereitschaftspraxis aus Cache verwendet bis", cached.get("duty_end"))
        return cached

    try:
        doctor = fetch_current_doctor_practice()
        write_doctor_cache(doctor)
        return doctor
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        print(f"116117 API fehlgeschlagen: {exc}")
        fallback = read_doctor_cache(ignore_expiry=True)
        if fallback:
            print("Abgelaufenen Bereitschaftspraxis-Cache als Fallback verwendet")
            return fallback
        return fallback_doctor_practice()


def get_current_dentist_service() -> dict[str, str]:
    cached = read_valid_dentist_cache()
    if cached:
        print("Zahnärztlicher Notdienst aus Cache verwendet bis", cached.get("duty_end"))
        return cached

    try:
        dentist = fetch_current_dentist_service()
        write_dentist_cache(dentist)
        return dentist
    except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
        print(f"Zahnarzt-Notdienst Scrape fehlgeschlagen: {exc}")
        fallback = read_dentist_cache(ignore_expiry=True)
        if fallback and fallback.get("cache_version") == CACHE_VERSION:
            print("Abgelaufenen Zahnarzt-Cache als Fallback verwendet")
            return fallback
        return fallback_dentist_service()


def read_valid_pharmacy_cache() -> dict[str, str] | None:
    cached = read_pharmacy_cache()
    if not cached:
        return None
    if cached.get("cache_version") != CACHE_VERSION:
        return None
    duty_end = parse_datetime(cached.get("duty_end"))
    if duty_end and datetime.now(timezone.utc) < duty_end:
        return cached
    return None


def read_valid_doctor_cache() -> dict[str, str] | None:
    cached = read_doctor_cache()
    if not cached:
        return None
    if cached.get("cache_version") != CACHE_VERSION:
        return None
    duty_end = parse_datetime(cached.get("duty_end"))
    if duty_end and datetime.now(timezone.utc) < duty_end:
        return cached
    return None


def read_valid_dentist_cache() -> dict[str, str] | None:
    cached = read_dentist_cache()
    if not cached:
        return None
    if cached.get("cache_version") != CACHE_VERSION:
        return None
    duty_end = parse_datetime(cached.get("duty_end"))
    if duty_end and datetime.now(timezone.utc) < duty_end:
        return cached
    return None


def read_pharmacy_cache(ignore_expiry: bool = False) -> dict[str, str] | None:
    path = OUTPUT_DIR / PHARMACY_CACHE_FILE
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if ignore_expiry:
        return cached
    return cached if isinstance(cached, dict) else None


def read_doctor_cache(ignore_expiry: bool = False) -> dict[str, str] | None:
    path = OUTPUT_DIR / DOCTOR_CACHE_FILE
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if ignore_expiry:
        return cached
    return cached if isinstance(cached, dict) else None


def read_dentist_cache(ignore_expiry: bool = False) -> dict[str, str] | None:
    path = OUTPUT_DIR / DENTIST_CACHE_FILE
    if not path.exists():
        return None
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if ignore_expiry:
        return cached
    return cached if isinstance(cached, dict) else None


def write_pharmacy_cache(pharmacy: dict[str, str]) -> None:
    path = OUTPUT_DIR / PHARMACY_CACHE_FILE
    with path.open("w", encoding="utf-8") as handle:
        json.dump(pharmacy, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Apotheken-Cache gespeichert: {path}")


def write_doctor_cache(doctor: dict[str, str]) -> None:
    path = OUTPUT_DIR / DOCTOR_CACHE_FILE
    with path.open("w", encoding="utf-8") as handle:
        json.dump(doctor, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Bereitschaftspraxis-Cache gespeichert: {path}")


def write_dentist_cache(dentist: dict[str, str]) -> None:
    path = OUTPUT_DIR / DENTIST_CACHE_FILE
    with path.open("w", encoding="utf-8") as handle:
        json.dump(dentist, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Zahnarzt-Cache gespeichert: {path}")


def fetch_current_pharmacy() -> dict[str, str]:
    req = Request(
        APOTHEKEN_API_URL,
        headers={
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Authorization": f"Bearer {APOTHEKEN_AUTH_TOKEN}",
            "Referer": "https://www.apotheken.de/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.5 Safari/605.1.15",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        if not isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise
        with urlopen(req, timeout=20, context=ssl._create_unverified_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Apotheken response")

    now = datetime.now(timezone.utc)
    candidates: list[tuple[float, dict]] = []
    for item in payload:
        duty = select_active_duty(item, now)
        if not duty:
            continue
        end = duty["end"]
        begin = duty["begin"]
        distance = distance_km(GOSLAR_LAT, GOSLAR_LON, float(item.get("latitude") or 0), float(item.get("longitude") or 0))
        candidates.append((distance, build_pharmacy_payload(item, begin, end, distance)))

    if not candidates:
        raise RuntimeError("No active emergency pharmacy found")

    candidates.sort(key=lambda row: row[0])
    return candidates[0][1]


def fetch_current_doctor_practice() -> dict[str, str]:
    body = json.dumps({
        "r": 900,
        "locType": "LATLON",
        "lat": 51.90605493505083,
        "lon": 10.429078449719238,
        "plz": None,
        "osmId": None,
        "osmType": None,
        "filterSelections": [],
        "locOrigin": "BROWSER_AUTO",
        "searchTrigger": "INITIAL",
        "viaDeeplink": False,
    }).encode("utf-8")
    req = Request(
        DOCTOR_API_URL,
        data=body,
        method="POST",
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Authorization": f"Basic {DOCTOR_AUTH_TOKEN}",
            "Content-Type": "application/json",
            "Referer": "https://bereitschaftspraxen.116117.de/",
            "req-val": DOCTOR_REQ_VAL,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.5 Safari/605.1.15",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        if not isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise
        with urlopen(req, timeout=20, context=ssl._create_unverified_context()) as response:
            payload = json.loads(response.read().decode("utf-8"))

    practices = payload.get("arztPraxisDatas") if isinstance(payload, dict) else None
    if not isinstance(practices, list):
        raise RuntimeError("Unexpected 116117 response")

    now = datetime.now(timezone.utc)
    candidates: list[tuple[float, dict]] = []
    for item in practices:
        lat = float(item.get("lat") or 0)
        lon = float(item.get("lon") or 0)
        distance = distance_km(GOSLAR_LAT, GOSLAR_LON, lat, lon)
        slot = select_doctor_slot(item, now)
        if not slot:
            continue
        payload_item = build_doctor_payload(item, slot["begin"], slot["end"], distance)
        candidates.append((distance, payload_item))

    if candidates:
        candidates.sort(key=lambda row: row[0])
        return candidates[0][1]
    raise RuntimeError("No current or upcoming doctor practice found")


def fetch_current_dentist_service() -> dict[str, str]:
    req = Request(
        DENTIST_SERVICE_URL,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.5 Safari/605.1.15",
        },
    )
    try:
        with urlopen(req, timeout=20) as response:
            html = response.read().decode("utf-8", errors="replace")
    except URLError as exc:
        if not isinstance(exc.reason, ssl.SSLCertVerificationError):
            raise
        with urlopen(req, timeout=20, context=ssl._create_unverified_context()) as response:
            html = response.read().decode("utf-8", errors="replace")

    entries = parse_dentist_entries(html)
    if not entries:
        raise RuntimeError("No dentist emergency entries found")

    now_local = datetime.now(LOCAL_TZ)
    selected = select_dentist_entry(entries, now_local)
    lat, lon = geocode_dentist_address(selected["address"])
    distance = distance_km(GOSLAR_LAT, GOSLAR_LON, lat, lon) if lat and lon else None
    return build_dentist_payload(selected, lat, lon, distance)


def parse_dentist_entries(html: str) -> list[dict[str, str]]:
    match = re.search(r"<h4[^>]*>\s*Zahnärztlicher Notdienst\s*</h4>(.*?)<h4[^>]*>\s*Apotheken Notdienst\s*</h4>", html, re.S | re.I)
    if not match:
        return []
    block = re.sub(r"<!--.*?-->", "", match.group(1), flags=re.S)
    pattern = re.compile(r"<strong>\s*([^<]+?)\s*</strong>\s*([^<]+?)(?:<br\s*/?>)", re.I)
    entries: list[dict[str, str]] = []
    for date_label, details in pattern.findall(block):
        details_text = clean_html_text(details)
        if not details_text or "wird noch" in details_text.casefold():
            continue
        parsed = parse_dentist_details(details_text)
        if parsed:
            parsed["date_label"] = clean_html_text(date_label)
            entries.append(parsed)
    return entries


def parse_dentist_details(details: str) -> dict[str, str] | None:
    match = re.match(r"(?P<name>.*?),\s*(?P<address>.*?),\s*Tel\.?\s*:?\s*(?P<phone>.+)$", details, re.I)
    if not match:
        return None
    name = match.group("name").strip()
    address = normalize_dentist_address(match.group("address").strip())
    phone = match.group("phone").strip()
    return {
        "name": name,
        "address": address,
        "telephone": phone,
    }


def normalize_dentist_address(address: str) -> str:
    normalized = re.sub(r"\s+", " ", address).strip()
    normalized = re.sub(r"\b\d{5}\s*", "", normalized).strip(" ,")
    normalized = re.sub(r",?\s*Goslar\s*$", "", normalized, flags=re.I).strip(" ,")
    return normalized + ", Goslar"


def select_dentist_entry(entries: list[dict[str, str]], now_local: datetime) -> dict[str, str]:
    candidates: list[tuple[bool, datetime, dict[str, str]]] = []
    for entry in entries:
        start, end = parse_dentist_date_range(entry["date_label"], now_local.year)
        if not start or not end:
            continue
        if end < now_local:
            start, end = parse_dentist_date_range(entry["date_label"], now_local.year + 1)
        enriched = dict(entry)
        enriched["duty_begin"] = start.astimezone(timezone.utc).isoformat()
        enriched["duty_end"] = end.astimezone(timezone.utc).isoformat()
        enriched["date_label"] = format_dentist_date_label(start, end)
        candidates.append((start <= now_local <= end, start, enriched))
    if not candidates:
        raise RuntimeError("No matching dentist emergency entry found")
    candidates.sort(key=lambda row: (not row[0], row[1]))
    return candidates[0][2]


def parse_dentist_date_range(value: str, year: int) -> tuple[datetime | None, datetime | None]:
    match = re.match(r"\s*(\d{1,2})\.-(\d{1,2})\.(\d{1,2})\.?\s*$", value)
    if not match:
        return None, None
    start_day = int(match.group(1))
    end_day = int(match.group(2))
    month = int(match.group(3))
    start = datetime(year, month, start_day, 0, 0, tzinfo=LOCAL_TZ)
    end = datetime(year, month, end_day, 23, 59, 59, tzinfo=LOCAL_TZ)
    if end < start:
        end += timedelta(days=31)
    return start, end


def format_dentist_date_label(start: datetime, end: datetime) -> str:
    return start.strftime("%d.%m.%Y") + " - " + end.strftime("%d.%m.%Y")


def geocode_dentist_address(address: str) -> tuple[float | None, float | None]:
    query = normalize_dentist_address(address)
    url = NOMINATIM_URL + "?" + urlencode({"q": query, "format": "json", "limit": "1", "countrycodes": "de"})
    req = Request(url, headers={"User-Agent": "machmitgoslar-gs-crawler/080"})
    try:
        with urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        if not isinstance(exc.reason, ssl.SSLCertVerificationError):
            return None, None
        try:
            with urlopen(req, timeout=10, context=ssl._create_unverified_context()) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return None, None
    except (HTTPError, TimeoutError, json.JSONDecodeError):
        return None, None
    if not payload:
        return None, None
    try:
        return float(payload[0]["lat"]), float(payload[0]["lon"])
    except (KeyError, TypeError, ValueError):
        return None, None


def build_dentist_payload(entry: dict[str, str], lat: float | None, lon: float | None, distance: float | None) -> dict[str, str]:
    query = quote_plus(entry.get("address") or entry.get("name") or "Zahnarzt Notdienst Goslar")
    telephone = entry.get("telephone") or ""
    return {
        "name": entry.get("name") or "Zahnärztlicher Notdienst",
        "address": entry.get("address") or "",
        "date_label": entry.get("date_label") or "",
        "distance_label": format_distance(distance) if distance is not None else "- km entfernt",
        "telephone": format_dentist_phone(telephone),
        "telephone_href": "tel:" + normalize_phone(telephone) if telephone else "#",
        "route_href": f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving" if lat and lon else f"https://www.google.com/maps/search/?api=1&query={query}",
        "external_href": DENTIST_SERVICE_URL,
        "latitude": str(lat or ""),
        "longitude": str(lon or ""),
        "duty_begin": entry.get("duty_begin") or "",
        "duty_end": entry.get("duty_end") or "",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "cache_version": CACHE_VERSION,
    }


def select_active_duty(item: dict, now: datetime) -> dict[str, datetime] | None:
    duties: list[dict[str, datetime]] = []
    for duty in item.get("emergencyDuties") or []:
        for time_range in duty.get("times") or []:
            begin = parse_datetime(time_range.get("begin"))
            end = parse_datetime(time_range.get("end"))
            if begin and end and begin <= now < end:
                duties.append({"begin": begin, "end": end})
    if not duties:
        return None
    duties.sort(key=lambda duty: duty["end"])
    return duties[0]


def build_pharmacy_payload(item: dict, begin: datetime, end: datetime, distance: float) -> dict[str, str]:
    street = str(item.get("street") or "").strip()
    city = " ".join(part for part in [str(item.get("zip") or "").strip(), str(item.get("city") or "").strip()] if part)
    address = ", ".join(part for part in [street, city] if part)
    lat = item.get("latitude")
    lon = item.get("longitude")
    query = quote_plus(address or str(item.get("name") or "Apotheke"))
    telephone = str(item.get("telephone") or "").strip()
    external = str(item.get("website") or "").strip() or "https://www.aponet.de/apotheke/notdienstsuche"
    if external and not external.startswith(("http://", "https://")):
        external = "https://" + external
    return {
        "name": str(item.get("name") or "Notdienstapotheke").strip(),
        "address": address,
        "distance_label": format_distance(distance),
        "telephone": telephone,
        "telephone_href": "tel:" + normalize_phone(telephone) if telephone else "#",
        "route_href": f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving" if lat and lon else f"https://www.google.com/maps/search/?api=1&query={query}",
        "external_href": external,
        "latitude": str(lat or ""),
        "longitude": str(lon or ""),
        "duty_begin": begin.isoformat(),
        "duty_end": end.isoformat(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "cache_version": CACHE_VERSION,
    }


def select_doctor_slot(item: dict, now: datetime) -> dict[str, datetime] | None:
    slots: list[dict[str, datetime]] = []
    for day in item.get("tsz") or []:
        date_value = str(day.get("d") or "").strip()
        if not date_value:
            continue
        for typed in day.get("typTsz") or []:
            for sprechzeit in typed.get("sprechzeiten") or []:
                begin, end = parse_local_time_range(date_value, sprechzeit.get("z"))
                if begin and end and end > now:
                    slots.append({"begin": begin, "end": end})
    if not slots:
        return None
    slots.sort(key=lambda slot: (not (slot["begin"] <= now < slot["end"]), slot["begin"]))
    return slots[0]


def parse_local_time_range(date_value: str, range_value: str | None) -> tuple[datetime | None, datetime | None]:
    if not range_value or " - " not in str(range_value):
        return None, None
    start_text, end_text = [part.strip() for part in str(range_value).split(" - ", 1)]
    try:
        start_hour, start_minute = [int(part) for part in start_text.split(":", 1)]
        end_hour, end_minute = [int(part) for part in end_text.split(":", 1)]
        year, month, day = [int(part) for part in date_value.split("-", 2)]
    except ValueError:
        return None, None
    begin_local = datetime(year, month, day, start_hour, start_minute, tzinfo=LOCAL_TZ)
    end_local = datetime(year, month, day, end_hour, end_minute, tzinfo=LOCAL_TZ)
    if end_local <= begin_local:
        end_local += timedelta(days=1)
    return begin_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def build_doctor_payload(item: dict, begin: datetime, end: datetime, distance: float) -> dict[str, str]:
    street = " ".join(part for part in [str(item.get("strasse") or "").strip(), str(item.get("hausnummer") or "").strip()] if part)
    city = " ".join(part for part in [str(item.get("plz") or "").strip(), str(item.get("ort") or "").strip()] if part)
    address = ", ".join(part for part in [street, city] if part)
    lat = item.get("lat")
    lon = item.get("lon")
    telephone = str(item.get("tel") or "116117").strip() or "116117"
    external = str(item.get("web") or "").strip() or "https://bereitschaftspraxen.116117.de/"
    if external and not external.startswith(("http://", "https://")):
        external = "https://" + external
    query = quote_plus(address or str(item.get("name") or "Bereitschaftspraxis"))
    return {
        "name": str(item.get("name") or "Bereitschaftspraxis").strip(),
        "address": address,
        "distance_label": format_distance(distance),
        "telephone": telephone,
        "telephone_href": "tel:" + normalize_phone(telephone) if telephone else "#",
        "route_href": f"https://www.google.com/maps/dir/?api=1&destination={lat},{lon}&travelmode=driving" if lat and lon else f"https://www.google.com/maps/search/?api=1&query={query}",
        "external_href": external,
        "latitude": str(lat or ""),
        "longitude": str(lon or ""),
        "duty_begin": begin.isoformat(),
        "duty_end": end.isoformat(),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "cache_version": CACHE_VERSION,
    }


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def format_distance(distance: float) -> str:
    return f"{distance:.1f}".replace(".", ",") + " km entfernt"


def clean_html_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    return (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&#228;", "ä")
        .replace("&#196;", "Ä")
        .strip()
    )


def normalize_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits == "116117":
        return "116117"
    if digits and not digits.startswith("0") and len(digits) <= 6:
        return "+495321" + digits
    return "+49" + digits.lstrip("0")


def format_dentist_phone(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits and not digits.startswith("0") and len(digits) <= 6:
        return "05321 " + digits
    return value


def fallback_pharmacy() -> dict[str, str]:
    return {
        "name": "Notdienstapotheke nicht verfügbar",
        "address": "Bitte externen Notdienst öffnen",
        "distance_label": "- km entfernt",
        "telephone": "Keine Telefonnummer",
        "telephone_href": "#",
        "route_href": "https://www.aponet.de/apotheke/notdienstsuche",
        "external_href": "https://www.aponet.de/apotheke/notdienstsuche",
        "duty_end": "",
    }


def fallback_doctor_practice() -> dict[str, str]:
    return {
        "name": "Bereitschaftspraxis nicht verfügbar",
        "address": "Bitte 116117 Bereitschaftspraxen öffnen",
        "distance_label": "- km entfernt",
        "telephone": "116117",
        "telephone_href": "tel:116117",
        "route_href": "https://bereitschaftspraxen.116117.de/",
        "external_href": "https://bereitschaftspraxen.116117.de/",
        "latitude": "",
        "longitude": "",
        "duty_end": "",
    }


def fallback_dentist_service() -> dict[str, str]:
    return {
        "name": "Zahnärztlicher Notdienst nicht verfügbar",
        "address": "Bitte Notdienstseite öffnen",
        "date_label": "",
        "distance_label": "- km entfernt",
        "telephone": "Keine Telefonnummer",
        "telephone_href": "#",
        "route_href": DENTIST_SERVICE_URL,
        "external_href": DENTIST_SERVICE_URL,
        "latitude": "",
        "longitude": "",
        "duty_end": "",
    }


def escape_html(value: str) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pharmacy = get_current_pharmacy()
    doctor = get_current_doctor_practice()
    dentist = get_current_dentist_service()
    write_json()
    copy_card_image_file()
    copy_ui_kit_files()
    copy_index_file()
    copy_city_file()
    copy_safety_file()
    write_medical_file(pharmacy, doctor, dentist)
    print("Erfolgreich gespeichert:", entry["title"])


if __name__ == "__main__":
    main()
