"""Geschäftslogik für Normalisierung, Filterung und Payload-Erzeugung."""

import json
from typing import Any
from urllib.parse import quote

from config import (
    ALLOWED_BUNDESAPI_FILTERS,
    DEFAULT_LOCATION,
    DETAIL_HTML_TEMPLATE_PATH,
    FIXED_RADIUS_KM,
    HTML_TEMPLATE_PATH,
    LANDKREIS_GOSLAR_LOCATION_TOKENS,
    LANDKREIS_GOSLAR_POSTAL_PREFIXES,
    OPEN_DATA_SOURCE_LABELS,
    SOURCE_CATEGORY_LABELS,
)
from api_clients import fetch_job_detail, fetch_jobs, fetch_studium


def normalize_bundesapi_job(job: dict[str, Any]) -> dict[str, Any]:
    """Normalisiert ein reguläres Jobsuche-Angebot in das gemeinsame Kartenformat."""
    work_location = job.get("arbeitsort") or {}
    logo_hash = job.get("kundennummerHash")
    detail_url = job.get("externeUrl")
    fallback_url = f"/job-detail.html?source=bundesapi&id={quote(str(job.get('refnr') or ''))}"
    return {
        "source": "bundesapi",
        "source_label": OPEN_DATA_SOURCE_LABELS["bundesapi"],
        "category": "jobs",
        "category_label": SOURCE_CATEGORY_LABELS["jobs"],
        "id": job.get("refnr"),
        "title": job.get("titel") or job.get("beruf"),
        "employer": job.get("arbeitgeber"),
        "published_at": job.get("aktuelleVeroeffentlichungsdatum"),
        "starts_at": job.get("eintrittsdatum"),
        "location": {
            "city": work_location.get("ort"),
            "postal_code": work_location.get("plz"),
            "street": work_location.get("strasse"),
            "region": work_location.get("region"),
            "country": work_location.get("land"),
        },
        "detail_url": detail_url,
        "click_url": detail_url or fallback_url,
        "fallback_url": fallback_url,
        "logo_url": f"/logo?source=bundesapi&hash={quote(logo_hash)}" if logo_hash else None,
        "raw": job,
    }


def normalize_bundesapi_ausbildung(job: dict[str, Any]) -> dict[str, Any]:
    """Markiert ein Jobsuche-Angebot als Ausbildungsstelle."""
    normalized = normalize_bundesapi_job(job)
    normalized["source"] = "ausbildung"
    normalized["source_label"] = OPEN_DATA_SOURCE_LABELS["ausbildung"]
    normalized["category"] = "ausbildung"
    normalized["category_label"] = SOURCE_CATEGORY_LABELS["ausbildung"]
    return normalized


def normalize_bundesapi_studium_job(job: dict[str, Any]) -> dict[str, Any]:
    """Markiert ein Jobsuche-Angebot als studiennahes Angebot."""
    normalized = normalize_bundesapi_job(job)
    normalized["source"] = "studium"
    normalized["source_label"] = OPEN_DATA_SOURCE_LABELS["studium"]
    normalized["category"] = "studium"
    normalized["category_label"] = SOURCE_CATEGORY_LABELS["studium"]
    return normalized


def normalize_bundesapi_selbststaendigkeit(job: dict[str, Any]) -> dict[str, Any]:
    """Markiert ein Jobsuche-Angebot als Selbständigkeitsangebot."""
    normalized = normalize_bundesapi_job(job)
    normalized["source"] = "selbststaendigkeit"
    normalized["source_label"] = OPEN_DATA_SOURCE_LABELS["selbststaendigkeit"]
    normalized["category"] = "selbststaendigkeit"
    normalized["category_label"] = SOURCE_CATEGORY_LABELS["selbststaendigkeit"]
    return normalized


def normalize_bundesapi_praktikum(job: dict[str, Any]) -> dict[str, Any]:
    """Markiert ein Jobsuche-Angebot als Praktikum/Trainee/Werkstudent."""
    normalized = normalize_bundesapi_job(job)
    normalized["source"] = "praktikum"
    normalized["source_label"] = OPEN_DATA_SOURCE_LABELS["praktikum"]
    normalized["category"] = "praktikum"
    normalized["category_label"] = SOURCE_CATEGORY_LABELS["praktikum"]
    return normalized


def is_studium_job(job: dict[str, Any]) -> bool:
    """Erkennt studiennahe Jobsuche-Treffer heuristisch über Titel und Rohdaten."""
    text = " ".join(
        [
            str(job.get("titel", "")),
            str(job.get("beruf", "")),
            str(job.get("arbeitgeber", "")),
            json.dumps(job, ensure_ascii=False),
        ]
    ).casefold()
    markers = (
        "duales studium",
        "dual stud",
        "bachelor",
        "master",
        "hochschule",
        "studiengang",
        "student ",
        "studentin",
        "diplom",
    )
    return any(marker in text for marker in markers)


def normalize_studium_offer(offer: dict[str, Any]) -> dict[str, Any]:
    """Normalisiert ein Studiensuche-Angebot in das gemeinsame Kartenformat."""
    provider = offer.get("studienanbieter") or {}
    logo = provider.get("logo") or {}
    location = offer.get("studienort") or {}
    external_links = offer.get("externalLinks") or []
    return {
        "source": "studium",
        "source_label": OPEN_DATA_SOURCE_LABELS["studium"],
        "category": "studium",
        "category_label": SOURCE_CATEGORY_LABELS["studium"],
        "id": offer.get("id"),
        "title": offer.get("studiBezeichnung") or offer.get("titel") or offer.get("bezeichnung") or "Studienangebot",
        "employer": provider.get("name"),
        "published_at": None,
        "starts_at": offer.get("studiBeginn"),
        "location": {
            "city": location.get("ort"),
            "postal_code": location.get("postleitzahl"),
            "street": location.get("strasse"),
            "region": location.get("bundesland"),
            "country": location.get("staat"),
        },
        "detail_url": external_links[0] if external_links else None,
        "click_url": external_links[0] if external_links else None,
        "logo_url": logo.get("externalURL"),
        "raw": offer,
    }


def build_location_label(job: dict[str, Any]) -> str:
    """Erzeugt ein kompaktes Standortlabel aus den normalisierten Ortsdaten."""
    location = job.get("location") or {}
    parts = [str(part) for part in (location.get("postal_code"), location.get("city"), location.get("region")) if part]
    return " · ".join(parts)


def render_html_page(location: str) -> str:
    """Lädt die Übersichtsseite und setzt den Default-Ort ein."""
    with open(HTML_TEMPLATE_PATH, encoding="utf-8") as html_file:
        html = html_file.read()
    return html.replace("__DEFAULT_LOCATION__", json.dumps(location))


def render_detail_html_page() -> str:
    """Lädt die HTML-Vorlage für die interne Detailseite."""
    with open(DETAIL_HTML_TEMPLATE_PATH, encoding="utf-8") as html_file:
        return html_file.read()


def build_jobs_payload(filters: dict[str, str]) -> dict[str, Any]:
    """Aggregiert alle aktiven Kategorien in einen API-Response für `/jobs`."""
    sources: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    combined_jobs: list[dict[str, Any]] = []
    location = filters.get("wo") or filters.get("location") or DEFAULT_LOCATION
    requested_categories = {
        item.strip()
        for item in (filters.get("categories") or "").split(";")
        if item.strip()
    }

    should_load_jobs = not requested_categories or "jobs" in requested_categories
    should_load_ausbildung = not requested_categories or "ausbildung" in requested_categories
    should_load_studium = not requested_categories or "studium" in requested_categories
    should_load_selbststaendigkeit = not requested_categories or "selbststaendigkeit" in requested_categories
    should_load_praktikum = not requested_categories or "praktikum" in requested_categories

    if should_load_jobs:
        try:
            bundesapi_jobs = fetch_jobs(filters)
            normalized_bundesapi_jobs = [normalize_bundesapi_job(job) for job in bundesapi_jobs]
            normalized_bundesapi_jobs = filter_jobs_to_landkreis_goslar(normalized_bundesapi_jobs)
            combined_jobs.extend(normalized_bundesapi_jobs)
            sources.append({"name": "bundesapi", "count": len(normalized_bundesapi_jobs)})
        except Exception as exc:
            errors.append({"source": "bundesapi", "message": str(exc)})

    if should_load_ausbildung or should_load_studium:
        try:
            ausbildung_jobs = fetch_jobs(dict(filters), offer_type="4")
            studium_jobs = [job for job in ausbildung_jobs if is_studium_job(job)]
            klassische_ausbildung_jobs = [job for job in ausbildung_jobs if not is_studium_job(job)]

            if should_load_ausbildung:
                normalized_ausbildung_jobs = [normalize_bundesapi_ausbildung(job) for job in klassische_ausbildung_jobs]
                normalized_ausbildung_jobs = filter_jobs_to_landkreis_goslar(normalized_ausbildung_jobs)
                normalized_ausbildung_jobs = filter_normalized_jobs(normalized_ausbildung_jobs, filters)
                combined_jobs.extend(normalized_ausbildung_jobs)
                sources.append({"name": "ausbildung", "count": len(normalized_ausbildung_jobs)})

            if should_load_studium:
                normalized_studium_jobs = [normalize_bundesapi_studium_job(job) for job in studium_jobs]
                normalized_studium_jobs = filter_jobs_to_landkreis_goslar(normalized_studium_jobs)
                normalized_studium_jobs = filter_normalized_jobs(normalized_studium_jobs, filters)
                combined_jobs.extend(normalized_studium_jobs)
                sources.append({"name": "studium_jobs", "count": len(normalized_studium_jobs)})
        except Exception as exc:
            source_name = "studium/ausbildung" if should_load_ausbildung and should_load_studium else ("ausbildung" if should_load_ausbildung else "studium")
            errors.append({"source": source_name, "message": str(exc)})

    if should_load_selbststaendigkeit:
        try:
            jobs = fetch_jobs(dict(filters), offer_type="2")
            normalized_jobs = [normalize_bundesapi_selbststaendigkeit(job) for job in jobs]
            normalized_jobs = filter_jobs_to_landkreis_goslar(normalized_jobs)
            normalized_jobs = filter_normalized_jobs(normalized_jobs, filters)
            combined_jobs.extend(normalized_jobs)
            sources.append({"name": "selbststaendigkeit", "count": len(normalized_jobs)})
        except Exception as exc:
            errors.append({"source": "selbststaendigkeit", "message": str(exc)})

    if should_load_praktikum:
        try:
            jobs = fetch_jobs(dict(filters), offer_type="34")
            normalized_jobs = [normalize_bundesapi_praktikum(job) for job in jobs]
            normalized_jobs = filter_jobs_to_landkreis_goslar(normalized_jobs)
            normalized_jobs = filter_normalized_jobs(normalized_jobs, filters)
            combined_jobs.extend(normalized_jobs)
            sources.append({"name": "praktikum", "count": len(normalized_jobs)})
        except Exception as exc:
            errors.append({"source": "praktikum", "message": str(exc)})

    if should_load_studium:
        try:
            raw_studium_offers = fetch_studium(filters)
            normalized_studium_offers = [normalize_studium_offer(item) for item in raw_studium_offers]
            normalized_studium_offers = filter_jobs_to_landkreis_goslar(normalized_studium_offers)
            normalized_studium_offers = filter_normalized_jobs(normalized_studium_offers, filters)
            combined_jobs.extend(normalized_studium_offers)
            sources.append({"name": "studium_api", "count": len(normalized_studium_offers)})
        except Exception as exc:
            errors.append({"source": "studium_api", "message": str(exc)})

    return {
        "location": location,
        "total_results": len(combined_jobs),
        "sources": sources,
        "errors": errors,
        "filters": filters,
        "results": combined_jobs,
    }


def filter_normalized_jobs(jobs: list[dict[str, Any]], filters: dict[str, str]) -> list[dict[str, Any]]:
    """Filtert bereits normalisierte Angebote anhand der aktiven Suchparameter."""
    text = (filters.get("was") or "").casefold()
    employer = (filters.get("arbeitgeber") or "").casefold()
    arbeitszeit = (filters.get("arbeitszeit") or "").casefold()
    befristung = (filters.get("befristung") or "").casefold()

    filtered: list[dict[str, Any]] = []
    for job in jobs:
        haystack = " ".join(
            [
                str(job.get("title", "")),
                str(job.get("employer", "")),
                str(job.get("category_label", "")),
                str(job.get("source_label", "")),
                build_location_label(job),
                json.dumps(job.get("raw", {}), ensure_ascii=False),
            ]
        ).casefold()
        if text and text not in haystack:
            continue
        if employer and employer not in str(job.get("employer", "")).casefold():
            continue
        if arbeitszeit and arbeitszeit not in haystack:
            continue
        if befristung and befristung not in haystack:
            continue
        filtered.append(job)
    return filtered


def filter_jobs_to_landkreis_goslar(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Beschränkt Angebote auf Orte und Postleitzahlen im Landkreis Goslar."""
    filtered: list[dict[str, Any]] = []
    for job in jobs:
        location = job.get("location") or {}
        postal_code = str(location.get("postal_code", "")).strip()
        search_blob = " ".join(
            [
                str(location.get("city", "")),
                str(location.get("region", "")),
                str(location.get("street", "")),
                json.dumps(job.get("raw", {}), ensure_ascii=False),
            ]
        ).casefold()
        if postal_code.startswith(LANDKREIS_GOSLAR_POSTAL_PREFIXES):
            filtered.append(job)
            continue
        if any(token in search_blob for token in LANDKREIS_GOSLAR_LOCATION_TOKENS):
            filtered.append(job)
    return filtered


def build_bundesapi_job_detail_payload(refnr: str) -> dict[str, Any]:
    """Baut den Detail-Response für die interne BundesAPI-Detailansicht."""
    detail = fetch_job_detail(refnr)
    logo_hash = detail.get("arbeitgeberKundennummerHash")
    location_parts = []
    for place in detail.get("arbeitsorte") or []:
        location_parts.append(" ".join([str(place.get("plz", "")).strip(), str(place.get("ort", "")).strip()]).strip())
    return {
        "id": refnr,
        "title": detail.get("stellenangebotsTitel") or refnr,
        "employer": detail.get("arbeitgeberName") or detail.get("arbeitgeber") or "BundesAPI",
        "summary": detail.get("beruf") or detail.get("titel") or "",
        "description_html": str(detail.get("stellenangebotsBeschreibung") or "Keine Detailbeschreibung vorhanden."),
        "published_at": detail.get("aktuelleVeroeffentlichungsdatum"),
        "location": " · ".join([part for part in location_parts if part]),
        "external_url": detail.get("externeUrl"),
        "logo_url": f"/logo?source=bundesapi&hash={quote(str(logo_hash))}" if logo_hash else None,
        "raw": detail,
    }


def first_query_value(query: dict[str, list[str]], key: str, default: str = "") -> str:
    """Liest den ersten Query-Parameterwert aus einer parse_qs-Struktur."""
    return query.get(key, [default])[0].strip()


def parse_filter_params(query: dict[str, list[str]]) -> dict[str, str]:
    """Normalisiert Query-Parameter in das interne Filtermodell der Anwendung."""
    filters: dict[str, str] = {
        "location": DEFAULT_LOCATION,
        "wo": DEFAULT_LOCATION,
        "umkreis": FIXED_RADIUS_KM,
    }
    for key in ALLOWED_BUNDESAPI_FILTERS - {"wo"}:
        if key == "umkreis":
            continue
        value = first_query_value(query, key, "")
        if value:
            filters[key] = value
    for key in ("categories", "sort"):
        value = first_query_value(query, key, "")
        if value:
            filters[key] = value
    return filters
