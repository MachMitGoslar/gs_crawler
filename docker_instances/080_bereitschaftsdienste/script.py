import json
import math
import ssl
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path("/app/output")

EXPORT_JSON_FILE = "080_bereitschaftsdienste_card.json"
INDEX_HTML_FILE = "080_bereitschaftsdienste_index.html"
MEDICAL_HTML_FILE = "080_bereitschaftsdienste_medizinisch.html"
PHARMACY_CACHE_FILE = "080_bereitschaftsdienste_apotheke_cache.json"
DOCTOR_CACHE_FILE = "080_bereitschaftsdienste_arztpraxis_cache.json"
INDEX_HTML_URL = "https://crawler.goslar.app/crawler/080_bereitschaftsdienste_index.html"
CACHE_VERSION = 4

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
LOCAL_TZ = ZoneInfo("Europe/Berlin")

entry = {
    "title": "Bereitschaftsdienste",
    "description": "Alle Notdienste der Stadt Goslar auf einen Blick – schnell finden, direkt erreichen und im Ernstfall sofort handeln.",
    "image_url": "",
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


def write_medical_file(pharmacy: dict[str, str], doctor: dict[str, str]) -> None:
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
        "__PHARMACY_EXTERNAL_HREF__": "https://www.aponet.de/notdienstsuche/Goslar%20Altstadt",
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


def normalize_phone(value: str) -> str:
    return "+49" + "".join(ch for ch in value if ch.isdigit()).lstrip("0")


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
    write_json()
    copy_index_file()
    write_medical_file(pharmacy, doctor)
    print("Erfolgreich gespeichert:", entry["title"])


if __name__ == "__main__":
    main()
