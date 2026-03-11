import requests
import json
import os
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────────
TOKEN_URL      = "https://backend.goslar-id.ceconsoft.de/connect/token"
CLIENT_ID      = os.environ["WOCHENMARKT_CLIENT_ID"]
CLIENT_SECRET  = os.environ["WOCHENMARKT_CLIENT_SECRET"]
SCOPE          = "markets.read"

EVENTS_URL      = "https://hsp-external-gateway-linux-cfethubabxayf7aq.westeurope-01.azurewebsites.net/api/external/market-events/upcoming"
ATTENDANCES_URL = "https://hsp-external-gateway-linux-cfethubabxayf7aq.westeurope-01.azurewebsites.net/api/external/market-events/{id}/attendances"

BASE_URL   = "https://crawler.goslar.app/crawler"
OUTPUT_DIR = "/app/output"

DAYS   = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni",
          "Juli", "August", "September", "Oktober", "November", "Dezember"]


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_token() -> str:
    print(f"Requesting token for client_id={CLIENT_ID!r} scope={SCOPE!r}")
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         SCOPE,
    })
    if not resp.ok:
        print(f"Token request failed: HTTP {resp.status_code}")
        print(f"Response body: {resp.text}")
        resp.raise_for_status()
    return resp.json()["access_token"]


def get_upcoming_events(token: str) -> list:
    resp = requests.get(EVENTS_URL, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def get_attendances(token: str, event_id: str) -> list:
    url = ATTENDANCES_URL.replace("{id}", event_id)
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()


def parse_dt(iso_str: str) -> datetime:
    """Parse ISO 8601 datetime, strip timezone for local display."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is not None:
        dt = dt.astimezone().replace(tzinfo=None)
    return dt


def german_date(dt: datetime) -> str:
    return f"{DAYS[dt.weekday()]}, {dt.day}. {MONTHS[dt.month - 1]} {dt.year}"


def write_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Written: {path}")


def vendor_address(vendor: dict) -> tuple[str, str]:
    """Return (street_line, city_line) for a vendor dict."""
    street = " ".join(p for p in [vendor.get("street", ""), vendor.get("houseNumber", "")] if p).strip()
    city   = " ".join(p for p in [vendor.get("zip", ""),    vendor.get("city", "")]          if p).strip()
    return street, city


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    now_str = datetime.now().isoformat(sep="T", timespec="minutes")

    print("Fetching OAuth token...")
    token = get_token()

    print("Fetching upcoming market events...")
    events = get_upcoming_events(token)

    if not events:
        print("No upcoming events — writing empty fallback.")
        write_json(os.path.join(OUTPUT_DIR, "070_wochenmarkt_card.json"), {
            "title":              "Wochenmarkt Goslar",
            "description":        "Aktuell sind keine kommenden Markttermine verfügbar.",
            "image_url":          None,
            "call_to_action_url": None,
            "published_at":       now_str,
        })
        write_json(os.path.join(OUTPUT_DIR, "070_wochenmarkt_alle.json"), [])
        return

    # Take the nearest upcoming event (API returns them sorted ascending)
    event     = events[0]
    event_id  = event["id"]
    market    = event.get("market") or {}
    start_dt  = parse_dt(event["start"])
    end_dt    = parse_dt(event["end"])

    market_name  = market.get("name")        or "Wochenmarkt Goslar"
    market_image = market.get("imageFileUrl")
    market_loc   = market.get("location")    or "Goslar"

    date_label = german_date(start_dt)
    time_range = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')} Uhr"

    print(f"Fetching attendances for event {event_id}...")
    attendances  = get_attendances(token, event_id)
    vendor_count = len(attendances)

    # ── Card ───────────────────────────────────────────────────────────────────
    card_desc = f"{market_name} am {date_label}, {time_range} auf dem {market_loc}."
    if vendor_count:
        card_desc += f" {vendor_count} Stände erwarten euch."

    write_json(os.path.join(OUTPUT_DIR, "070_wochenmarkt_card.json"), {
        "title":              f"{market_name} – {date_label}",
        "description":        card_desc,
        "image_url":          market_image,
        "call_to_action_url": f"{BASE_URL}/070_wochenmarkt_index.html",
        "published_at":       now_str,
    })

    # ── Index ──────────────────────────────────────────────────────────────────
    index = []
    for i, vendor in enumerate(attendances, start=1):
        vendor_id   = vendor["id"]
        vendor_name = vendor.get("name") or "Unbekannter Stand"
        street, city = vendor_address(vendor)
        description = ", ".join(p for p in [street, city] if p) or market_loc

        index.append({
            "id":                 i,
            "title":              vendor_name,
            "description":        description,
            "image_url":          vendor.get("logoFileUrl"),
            "call_to_action_url": f"{BASE_URL}/070_wochenmarkt_detail.html?id={vendor_id}",
            "published_at":       now_str,
        })

    write_json(os.path.join(OUTPUT_DIR, "070_wochenmarkt_alle.json"), index)

    # ── Detail files (one per vendor) ─────────────────────────────────────────
    for i, vendor in enumerate(attendances, start=1):
        vendor_id   = vendor["id"]
        vendor_name = vendor.get("name") or "Unbekannter Stand"
        street, city = vendor_address(vendor)
        full_address = ", ".join(p for p in [street, city] if p)
        summary      = full_address or f"Stand auf dem {market_name}"

        desc = f"<p>{vendor_name} ist beim {market_name} am {date_label} in {market_loc} dabei.</p>"
        if full_address:
            desc += f"<p>Adresse: {full_address}</p>"

        images = [{"url": vendor["logoFileUrl"]}] if vendor.get("logoFileUrl") else []

        write_json(os.path.join(OUTPUT_DIR, f"070_wochenmarkt_{vendor_id}.json"), {
            "id":                 i,
            "title":              vendor_name,
            "summary":            summary,
            "description":        desc,
            "images":             images,
            "call_to_action_url": None,
            "published_at":       now_str,
        })

    print(f"Done. {vendor_count} vendors written for '{market_name}' on {date_label}.")


if __name__ == "__main__":
    main()
