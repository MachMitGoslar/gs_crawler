"""Zentrale Konfiguration und Konstanten für das Job-Portal."""

import os


BASE_DIR = os.path.dirname(__file__)

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_LOCATION = "Goslar"
FIXED_RADIUS_KM = "60"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_PAGE_SIZE = 100

HTML_TEMPLATE_PATH = os.path.join(BASE_DIR, "jobs.html")
DETAIL_HTML_TEMPLATE_PATH = os.path.join(BASE_DIR, "job_detail.html")

BUNDESAPI_BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
BUNDESAPI_JOBDETAILS_BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobdetails"
BUNDESAPI_KEY = "jobboerse-jobsuche"
ARBEITGEBERLOGO_BASE_URL = "https://rest.arbeitsagentur.de/vermittlung/ag-darstellung-service/ct/v1/arbeitgeberlogo"

LANDKREIS_GOSLAR_SEARCH_LOCATIONS = (
    "Goslar",
    "Bad Harzburg",
    "Braunlage",
    "Clausthal-Zellerfeld",
    "Langelsheim",
    "Liebenburg",
    "Seesen",
)

LANDKREIS_GOSLAR_SEARCH_PLACES = (
    {"city": "Goslar", "postal_code": "38640", "lon": "10.4301", "lat": "51.9057"},
    {"city": "Bad Harzburg", "postal_code": "38667", "lon": "10.5582", "lat": "51.8821"},
    {"city": "Braunlage", "postal_code": "38700", "lon": "10.6115", "lat": "51.7260"},
    {"city": "Clausthal-Zellerfeld", "postal_code": "38678", "lon": "10.3406", "lat": "51.8090"},
    {"city": "Langelsheim", "postal_code": "38685", "lon": "10.3338", "lat": "51.9383"},
    {"city": "Liebenburg", "postal_code": "38704", "lon": "10.4314", "lat": "52.0210"},
    {"city": "Seesen", "postal_code": "38723", "lon": "10.1788", "lat": "51.8907"},
)

ALLOWED_BUNDESAPI_FILTERS = {
    "was",
    "wo",
    "berufsfeld",
    "page",
    "size",
    "arbeitgeber",
    "zeitarbeit",
    "veroeffentlichtseit",
    "pav",
    "angebotsart",
    "befristung",
    "behinderung",
    "corona",
    "umkreis",
    "arbeitszeit",
}

SOURCE_CATEGORY_LABELS = {
    "jobs": "Jobs",
    "studium": "Studium",
    "ausbildung": "Ausbildungsstellen",
    "selbststaendigkeit": "Selbständigkeit",
    "praktikum": "Praktikum/Trainee/Werkstudent",
}

OPEN_DATA_SOURCE_LABELS = {
    "bundesapi": "BundesAPI Jobs",
    "studium": "BundesAPI Studium",
    "ausbildung": "BundesAPI Ausbildungsstellen",
    "selbststaendigkeit": "BundesAPI Selbständigkeit",
    "praktikum": "BundesAPI Praktikum/Trainee",
}

OPEN_DATA_BUNDESLAND_CODE_STUDIUM = "NI"
STUDIUM_API_URL = "https://rest.arbeitsagentur.de/infosysbub/studisu/pc/v1/studienangebote"
STUDIUM_API_KEY = "infosysbub-studisu"

SSL_RETRY_ERROR_MARKERS = (
    "CERTIFICATE_VERIFY_FAILED",
    "self-signed certificate",
    "unable to get local issuer certificate",
)

LANDKREIS_GOSLAR_LOCATION_TOKENS = {
    "goslar",
    "bad harzburg",
    "braunlage",
    "clausthal-zellerfeld",
    "clausthal zellerfeld",
    "langelsheim",
    "liebenburg",
    "seesen",
    "altenau",
    "hahnenklee",
    "hahnenklee-bockswiese",
    "bockswiese",
    "oker",
    "vienenburg",
    "lautenthal",
    "wolfshagen",
    "sankt andreasberg",
    "st. andreasberg",
    "buntenbock",
    "hohegeiß",
    "hohegeiss",
}

LANDKREIS_GOSLAR_POSTAL_PREFIXES = ("386", "387")

LOGO_PLACEHOLDER_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="280" viewBox="0 0 640 280">
<rect width="640" height="280" fill="#f1f1f1"/>
</svg>""".encode("utf-8")
