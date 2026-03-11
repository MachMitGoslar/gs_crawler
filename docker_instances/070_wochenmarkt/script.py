import requests
import json
import os
from datetime import datetime, timezone

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


# ── Static HTML pages ──────────────────────────────────────────────────────────
INDEX_HTML = """\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Wochenmarkt Goslar \u2013 Alle St\u00e4nde</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f0; color: #222; min-height: 100vh; }
    header { background: #2d6a2d; color: #fff; padding: 1.25rem 1rem 1rem; text-align: center; }
    header h1 { font-size: 1.4rem; font-weight: 700; }
    header p  { font-size: 0.9rem; opacity: 0.85; margin-top: 0.25rem; }
    #loading, #error { text-align: center; padding: 3rem 1rem; color: #666; }
    #error { color: #c0392b; }
    #count { padding: 0.75rem 1rem; font-size: 0.85rem; color: #555; background: #e8e8e4; border-bottom: 1px solid #ddd; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; padding: 1rem; }
    .card { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.1); overflow: hidden; display: flex; flex-direction: column; cursor: pointer; text-decoration: none; color: inherit; transition: box-shadow 0.15s; }
    .card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    .card-logo { width: 100%; height: 140px; object-fit: contain; background: #f0f0ea; padding: 1rem; }
    .card-logo-placeholder { width: 100%; height: 140px; background: #e8e8e4; display: flex; align-items: center; justify-content: center; font-size: 2.5rem; }
    .card-body { padding: 0.85rem 1rem 1rem; flex: 1; display: flex; flex-direction: column; gap: 0.3rem; }
    .card-name    { font-size: 1rem; font-weight: 600; }
    .card-address { font-size: 0.82rem; color: #666; }
    .card-arrow   { margin-top: auto; padding-top: 0.6rem; font-size: 0.8rem; color: #2d6a2d; font-weight: 600; }
  </style>
</head>
<body>
<header>
  <h1>Wochenmarkt Goslar</h1>
  <p>Alle St\u00e4nde im Blick</p>
</header>
<div id="loading">St\u00e4nde werden geladen\u2026</div>
<div id="error" style="display:none"></div>
<div id="count" style="display:none"></div>
<div class="grid" id="grid"></div>
<script>
  const BASE = location.href.substring(0, location.href.lastIndexOf('/') + 1);
  const INDEX_JSON  = BASE + '070_wochenmarkt_alle.json';
  const DETAIL_PAGE = BASE + '070_wochenmarkt_detail.html';

  async function load() {
    try {
      const res = await fetch(INDEX_JSON);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const vendors = await res.json();
      document.getElementById('loading').style.display = 'none';
      if (!vendors.length) {
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = 'F\u00fcr diesen Markt sind noch keine St\u00e4nde eingetragen.';
        return;
      }
      const countEl = document.getElementById('count');
      countEl.style.display = 'block';
      countEl.textContent = vendors.length + ' Stand' + (vendors.length !== 1 ? 'e' : '');
      const grid = document.getElementById('grid');
      for (const v of vendors) {
        const uuid = extractUuid(v.call_to_action_url);
        const href = uuid ? DETAIL_PAGE + '?id=' + uuid : '#';
        const a = document.createElement('a');
        a.className = 'card';
        a.href = href;
        const logoHtml = v.image_url
          ? '<img class="card-logo" src="' + esc(v.image_url) + '" alt="' + esc(v.title) + '" loading="lazy" onerror="this.replaceWith(ph())">'
          : '<div class="card-logo-placeholder">\ud83c\udfea</div>';
        a.innerHTML = logoHtml + '<div class="card-body"><div class="card-name">' + esc(v.title) + '</div><div class="card-address">' + esc(v.description) + '</div><div class="card-arrow">Details \u2192</div></div>';
        grid.appendChild(a);
      }
    } catch (e) {
      document.getElementById('loading').style.display = 'none';
      document.getElementById('error').style.display = 'block';
      document.getElementById('error').textContent = 'Daten konnten nicht geladen werden: ' + e.message;
    }
  }
  function extractUuid(url) {
    if (!url) return null;
    const m = url.match(/070_wochenmarkt_([0-9a-f-]{36})\.json/i) || url.match(/[?&]id=([0-9a-f-]{36})/i);
    return m ? m[1] : null;
  }
  function esc(str) { return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
  function ph() { const d = document.createElement('div'); d.className = 'card-logo-placeholder'; d.textContent = '\ud83c\udfea'; return d; }
  load();
</script>
</body>
</html>
"""

DETAIL_HTML = """\
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Stand \u2013 Wochenmarkt Goslar</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f5f0; color: #222; min-height: 100vh; }
    header { background: #2d6a2d; color: #fff; padding: 1rem; display: flex; align-items: center; gap: 0.75rem; }
    header a { color: #fff; text-decoration: none; font-size: 1.3rem; line-height: 1; }
    header h1 { font-size: 1.1rem; font-weight: 600; }
    #loading, #error { text-align: center; padding: 3rem 1rem; color: #666; }
    #error { color: #c0392b; }
    .card { max-width: 520px; margin: 1.25rem auto; background: #fff; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.1); overflow: hidden; }
    .logo-wrap { width: 100%; background: #f0f0ea; display: flex; align-items: center; justify-content: center; padding: 1.5rem; min-height: 160px; }
    .logo-wrap img { max-width: 100%; max-height: 160px; object-fit: contain; }
    .logo-placeholder { font-size: 4rem; }
    .body { padding: 1.25rem 1.25rem 1.5rem; }
    .vendor-name { font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; }
    .summary { font-size: 0.9rem; color: #555; margin-bottom: 1rem; }
    .description { font-size: 0.92rem; line-height: 1.6; color: #333; }
    .description p { margin-bottom: 0.5rem; }
    .back-link { display: block; text-align: center; margin: 0 1rem 1.5rem; padding: 0.75rem; background: #2d6a2d; color: #fff; border-radius: 8px; text-decoration: none; font-size: 0.95rem; font-weight: 600; }
    .back-link:hover { background: #245424; }
  </style>
</head>
<body>
<header>
  <a id="back-btn" href="070_wochenmarkt_index.html">\u2190</a>
  <h1>Stand Details</h1>
</header>
<div id="loading">Stand wird geladen\u2026</div>
<div id="error" style="display:none"></div>
<div id="content" style="display:none">
  <div class="card">
    <div class="logo-wrap" id="logo-wrap"><div class="logo-placeholder">\ud83c\udfea</div></div>
    <div class="body">
      <div class="vendor-name" id="vendor-name"></div>
      <div class="summary"     id="vendor-summary"></div>
      <div class="description" id="vendor-description"></div>
    </div>
  </div>
  <a class="back-link" id="back-link" href="070_wochenmarkt_index.html">\u2190 Alle St\u00e4nde</a>
</div>
<script>
  const BASE = location.href.substring(0, location.href.lastIndexOf('/') + 1);
  const INDEX_PAGE = BASE + '070_wochenmarkt_index.html';
  document.getElementById('back-btn').href  = INDEX_PAGE;
  document.getElementById('back-link').href = INDEX_PAGE;

  async function load() {
    const params = new URLSearchParams(location.search);
    const id = params.get('id');
    if (!id) { showError('Kein Stand angegeben.'); return; }
    try {
      const res = await fetch(BASE + '070_wochenmarkt_' + id + '.json');
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const v = await res.json();
      document.title = (v.title ?? 'Stand') + ' \u2013 Wochenmarkt Goslar';
      document.getElementById('vendor-name').textContent    = v.title ?? '';
      document.getElementById('vendor-summary').textContent = v.summary ?? '';
      if (v.description) document.getElementById('vendor-description').innerHTML = v.description;
      const imgs = v.images ?? [];
      if (imgs.length && imgs[0].url) {
        const img = document.createElement('img');
        img.src = imgs[0].url;
        img.alt = v.title ?? 'Logo';
        img.onerror = () => { img.replaceWith(ph()); };
        const wrap = document.getElementById('logo-wrap');
        wrap.innerHTML = '';
        wrap.appendChild(img);
      }
      document.getElementById('loading').style.display = 'none';
      document.getElementById('content').style.display = 'block';
    } catch (e) { showError('Stand konnte nicht geladen werden: ' + e.message); }
  }
  function showError(msg) {
    document.getElementById('loading').style.display = 'none';
    const el = document.getElementById('error');
    el.style.display = 'block';
    el.textContent = msg;
  }
  function ph() { const d = document.createElement('div'); d.className = 'logo-placeholder'; d.textContent = '\ud83c\udfea'; return d; }
  load();
</script>
</body>
</html>
"""


# ── Helpers ────────────────────────────────────────────────────────────────────
def get_token() -> str:
    resp = requests.post(TOKEN_URL, data={
        "grant_type":    "client_credentials",
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope":         SCOPE,
    })
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


def write_html(filename: str, content: str) -> None:
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path}")


def vendor_address(vendor: dict) -> tuple[str, str]:
    """Return (address_line, city_line) for a vendor dict."""
    street = " ".join(p for p in [vendor.get("street", ""), vendor.get("houseNumber", "")] if p).strip()
    city   = " ".join(p for p in [vendor.get("zip", ""),    vendor.get("city", "")]          if p).strip()
    return street, city


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    now_str = datetime.now().isoformat(sep="T", timespec="minutes")

    # Always deploy the HTML pages so they're available alongside the JSON files
    write_html("070_wochenmarkt_index.html",  INDEX_HTML)
    write_html("070_wochenmarkt_detail.html", DETAIL_HTML)

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
    event      = events[0]
    event_id   = event["id"]
    market     = event.get("market") or {}
    start_dt   = parse_dt(event["start"])
    end_dt     = parse_dt(event["end"])

    market_name  = market.get("name")        or "Wochenmarkt Goslar"
    market_image = market.get("imageFileUrl")
    market_loc   = market.get("location")    or "Goslar"

    date_label = german_date(start_dt)
    time_range = f"{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')} Uhr"

    print(f"Fetching attendances for event {event_id}...")
    attendances   = get_attendances(token, event_id)
    vendor_count  = len(attendances)

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
