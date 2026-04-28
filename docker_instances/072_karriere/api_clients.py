"""HTTP-nahe API-Clients für Jobsuche, Studiensuche und Logo-Fetches."""

import json
import ssl
import subprocess
from base64 import b64encode
from typing import Any
from urllib.error import URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from config import (
    ALLOWED_BUNDESAPI_FILTERS,
    ARBEITGEBERLOGO_BASE_URL,
    BUNDESAPI_BASE_URL,
    BUNDESAPI_JOBDETAILS_BASE_URL,
    BUNDESAPI_KEY,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEOUT_SECONDS,
    LANDKREIS_GOSLAR_SEARCH_LOCATIONS,
    LANDKREIS_GOSLAR_SEARCH_PLACES,
    OPEN_DATA_BUNDESLAND_CODE_STUDIUM,
    SSL_RETRY_ERROR_MARKERS,
    STUDIUM_API_KEY,
    STUDIUM_API_URL,
)


def create_verified_ssl_context() -> ssl.SSLContext:
    """Erzeugt einen regulär verifizierenden SSL-Kontext, optional mit certifi."""
    try:
        import certifi
    except ImportError:
        return ssl.create_default_context()
    return ssl.create_default_context(cafile=certifi.where())


def create_insecure_ssl_context() -> ssl.SSLContext:
    """Erzeugt einen SSL-Kontext ohne Zertifikatsprüfung als Fallback."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def should_retry_without_verification(error: URLError) -> bool:
    """Erkennt SSL-Fehler, bei denen ein unverified Retry sinnvoll ist."""
    error_text = str(error.reason if getattr(error, "reason", None) else error)
    return any(marker in error_text for marker in SSL_RETRY_ERROR_MARKERS)


def open_url_with_ssl_fallback(request: Request, timeout: int):
    """Öffnet eine URL mit TLS-Prüfung und optionalem SSL-Fallback."""
    try:
        return urlopen(request, timeout=timeout, context=create_verified_ssl_context())
    except URLError as exc:
        if not should_retry_without_verification(exc):
            raise
        return urlopen(request, timeout=timeout, context=create_insecure_ssl_context())


def fetch_bytes(url: str, headers: dict[str, str], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> tuple[bytes, str]:
    """Lädt Binärdaten von einer URL und gibt Body plus Content-Type zurück."""
    request = Request(url, headers=headers, method="GET")
    with open_url_with_ssl_fallback(request, timeout) as response:
        content_type = response.headers.get("Content-Type", "application/octet-stream")
        return response.read(), content_type


def fetch_jobs(filters: dict[str, str], offer_type: str | None = None) -> list[dict[str, Any]]:
    """Lädt Jobtreffer aus der BA-Jobsuche für alle Landkreis-Goslar-Orte."""
    page = max(int(filters.get("page", "1") or "1"), 1)
    size = max(int(filters.get("size", str(DEFAULT_PAGE_SIZE)) or DEFAULT_PAGE_SIZE), 1)
    jobs_by_refnr: dict[str, dict[str, Any]] = {}

    for search_location in LANDKREIS_GOSLAR_SEARCH_LOCATIONS:
        query_params = build_job_query(filters, search_location, offer_type=offer_type)
        query_params["page"] = page
        query_params["size"] = size
        payload = fetch_bundesapi_json(f"{BUNDESAPI_BASE_URL}?{urlencode(query_params)}")
        for job in payload.get("stellenangebote", []):
            refnr = str(job.get("refnr") or "")
            if refnr and refnr not in jobs_by_refnr:
                jobs_by_refnr[refnr] = job

    return list(jobs_by_refnr.values())


def build_job_query(filters: dict[str, str], search_location: str, offer_type: str | None = None) -> dict[str, Any]:
    """Baut die Query-Parameter für einen Jobsuche-Request auf."""
    query: dict[str, Any] = {"angebotsart": offer_type or filters.get("angebotsart", "1")}
    for key in ALLOWED_BUNDESAPI_FILTERS:
        value = filters.get(key)
        if value not in (None, ""):
            query[key] = value
    query["wo"] = search_location
    return query


def fetch_job_detail(refnr: str) -> dict[str, Any]:
    """Lädt die Detaildaten eines Stellenangebots anhand der Referenznummer."""
    encoded_refnr = b64encode(refnr.encode("utf-8")).decode("ascii")
    return fetch_bundesapi_json(f"{BUNDESAPI_JOBDETAILS_BASE_URL}/{quote(encoded_refnr, safe='')}")


def fetch_bundesapi_json(url: str) -> dict[str, Any]:
    """Ruft einen JSON-Endpunkt der BA-Jobsuche per curl auf."""
    command = [
        "curl",
        "-sS",
        "-H",
        f"X-API-Key: {BUNDESAPI_KEY}",
        "-H",
        "Accept: application/json",
        url,
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"curl failed with exit code {completed.returncode}: {completed.stderr.strip()}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON from BundesAPI: {completed.stdout[:400]}") from exc


def fetch_logo(logo_hash: str) -> tuple[bytes, str]:
    """Lädt ein Arbeitgeberlogo aus dem BA-Logo-Service."""
    return fetch_bytes(
        f"{ARBEITGEBERLOGO_BASE_URL}/{quote(logo_hash, safe='')}",
        headers={"X-API-Key": BUNDESAPI_KEY, "Accept": "image/webp,image/png,*/*"},
    )


def fetch_studium(filters: dict[str, str]) -> list[dict[str, Any]]:
    """Lädt Studienangebote aus der Studiensuche für den Landkreis Goslar."""
    study_items: dict[str, dict[str, Any]] = {}
    search_word = filters.get("was", "").strip()

    for place in LANDKREIS_GOSLAR_SEARCH_PLACES:
        query = {
            "pg": 1,
            "orte": build_studium_place(place),
            "uk": "25",
            "re": OPEN_DATA_BUNDESLAND_CODE_STUDIUM,
        }
        if search_word:
            query["sw"] = search_word
        else:
            query["smo"] = 5

        payload = fetch_open_data_json(STUDIUM_API_URL, STUDIUM_API_KEY, query)
        for item in payload.get("items", []):
            offer = item.get("studienangebot") or {}
            offer_id = str(offer.get("id") or build_dedupe_key(offer))
            if offer_id and offer_id not in study_items:
                study_items[offer_id] = offer

    return list(study_items.values())


def build_studium_place(place: dict[str, str]) -> str:
    """Formatiert einen Ort in das von der Studiensuche erwartete Ortsformat."""
    return f"{place['city']}_{place['postal_code']}_{place['lon']}_{place['lat']}"


def build_dedupe_key(item: dict[str, Any]) -> str:
    """Erzeugt einen kurzen stabilen Fallback-Schlüssel für Deduplizierung."""
    return json.dumps(item, ensure_ascii=False, sort_keys=True)[:400]


def fetch_open_data_json(url: str, api_key: str, query: dict[str, Any]) -> dict[str, Any]:
    """Ruft einen JSON-Endpunkt der BundesAPI-Open-Data-Schnittstellen ab."""
    command = [
        "curl",
        "-sS",
        "-H",
        f"X-API-Key: {api_key}",
        "-H",
        "Accept: application/json, application/hal+json;q=0.9, */*;q=0.8",
        "-w",
        "\n%{http_code}",
        f"{url}?{urlencode(query)}",
    ]
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SECONDS,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"curl failed with exit code {completed.returncode}: {completed.stderr.strip()}")
    if "\n" not in completed.stdout:
        raise RuntimeError(f"invalid response from upstream: {completed.stdout[:300]}")
    body, status_code = completed.stdout.rsplit("\n", 1)
    if status_code != "200":
        raise RuntimeError(f"HTTP {status_code}: {body[:300]}")
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid JSON from upstream: {body[:400]}") from exc
