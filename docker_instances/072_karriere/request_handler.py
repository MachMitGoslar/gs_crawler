"""HTTP-Handler für HTML-, JSON-, Logo- und Detail-Endpunkte."""

import json
from http.server import BaseHTTPRequestHandler
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

from api_clients import fetch_logo
from config import DEFAULT_LOCATION, LOGO_PLACEHOLDER_SVG
from jobs_logic import (
    build_bundesapi_job_detail_payload,
    build_jobs_payload,
    first_query_value,
    parse_filter_params,
    render_detail_html_page,
    render_html_page,
)


class JobRequestHandler(BaseHTTPRequestHandler):
    """Bedient alle GET-Endpunkte des lokalen Job-Portals."""

    server_version = "JobsProxy/1.0"

    def do_GET(self) -> None:
        """Routet eingehende GET-Requests auf HTML-, JSON- und Asset-Endpunkte."""
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        filters = parse_filter_params(query)
        location = filters.get("wo", DEFAULT_LOCATION)

        if parsed.path in {"/", "/jobs.html"}:
            self.send_html(200, render_html_page(location))
            return

        if parsed.path == "/favicon.ico":
            self.send_empty(204)
            return

        if parsed.path == "/job-detail.html":
            self.send_html(200, render_detail_html_page())
            return

        if parsed.path == "/health":
            self.send_json(200, {"status": "ok"})
            return

        if parsed.path in {"/job-details", "/job-details-data"}:
            self.handle_job_details_data_request(query)
            return

        if parsed.path == "/logo":
            self.handle_logo_request(query)
            return

        if parsed.path != "/jobs":
            self.send_json(
                404,
                {
                    "error": "Not found",
                    "available_endpoints": [
                        "/",
                        "/jobs.html?location=Goslar",
                        "/job-detail.html?source=bundesapi&id=REFNR",
                        "/job-details-data?source=bundesapi&id=REFNR",
                        "/health",
                        "/jobs?location=Goslar",
                    ],
                },
            )
            return

        self.send_json(200, build_jobs_payload(filters))

    def handle_job_details_data_request(self, query: dict[str, list[str]]) -> None:
        """Liefert die JSON-Daten für die interne Detailansicht eines BA-Jobs."""
        source = first_query_value(query, "source")
        job_id = first_query_value(query, "id")
        if source != "bundesapi" or not job_id:
            self.send_json(400, {"error": "Missing or unsupported job detail parameters"})
            return
        try:
            self.send_json(200, build_bundesapi_job_detail_payload(job_id))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
            self.send_json(502, {"error": f"Job detail request failed: {exc}"})

    def handle_logo_request(self, query: dict[str, list[str]]) -> None:
        """Proxyt Arbeitgeberlogos und fällt bei 404 auf ein Placeholder-SVG zurück."""
        source = first_query_value(query, "source")
        logo_hash = first_query_value(query, "hash")
        if source != "bundesapi" or not logo_hash:
            self.send_json(400, {"error": "Missing or unsupported logo parameters"})
            return
        try:
            body, content_type = fetch_logo(logo_hash)
            self.send_bytes(200, body, content_type)
        except HTTPError as exc:
            if exc.code == 404:
                self.send_bytes(200, LOGO_PLACEHOLDER_SVG, "image/svg+xml; charset=utf-8")
                return
            self.send_json(502, {"error": f"Logo request failed: {exc}"})
        except (URLError, TimeoutError, RuntimeError) as exc:
            self.send_json(502, {"error": f"Logo request failed: {exc}"})

    def send_json(self, status_code: int, payload: dict[str, Any]) -> None:
        """Serialisiert ein Python-Dictionary als JSON-HTTP-Response."""
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_bytes(status_code, body, "application/json; charset=utf-8")

    def send_html(self, status_code: int, html: str) -> None:
        """Sendet HTML mit passendem Content-Type."""
        self.send_bytes(status_code, html.encode("utf-8"), "text/html; charset=utf-8")

    def send_empty(self, status_code: int) -> None:
        """Sendet eine leere Response ohne Body."""
        self.send_response(status_code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def send_bytes(self, status_code: int, body: bytes, content_type: str) -> None:
        """Sendet rohe Bytes mit Statuscode, Content-Type und Content-Length."""
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        """Unterdrückt das Standard-Logging des BaseHTTPRequestHandler."""
        return
