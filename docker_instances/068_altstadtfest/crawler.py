"""Crawler für das Altstadtfest Goslar.

Lädt https://www.meingoslar.de/veranstaltungen/altstadtfest, parst das
Bühnenprogramm (Datum, Bühne, Uhrzeit, Titel, Beschreibung) sowie die
zusätzlichen Programm-Highlights (Flohmarkt, Entenrennen, Kinderprogramm, ...)
und schreibt das Ergebnis nach data.json.
"""

import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.meingoslar.de/veranstaltungen/altstadtfest"
BASE_URL = "https://www.meingoslar.de"
DATA_FILE = "data.json"

# Server läuft in Produktion mit GMT; crawled_at muss aber dieselbe lokale
# Zeitbasis wie die Programmzeiten haben, damit app.py sie vergleichbar bleiben.
BERLIN_TZ = ZoneInfo("Europe/Berlin")

MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}
WEEKDAYS = "Montag|Dienstag|Mittwoch|Donnerstag|Freitag|Samstag|Sonntag"
STAGE_RE = re.compile(r"^(\d{1,2})\.\s*(.+?)\s*\|\s*(.+)$")
DAY_RE = re.compile(r"^(?:%s),?\s*(\d{1,2})\.\s*([A-Za-zÄÖÜäöü]+)\.?\s*(\d{4})?" % WEEKDAYS)
TIME_RE = re.compile(r"(\d{1,2})[:.](\d{2})")

# Programmpunkte, die per Titel-Schlagwort als "Highlight" markiert werden.
HIGHLIGHT_KEYWORDS = [
    "fassanstich", "eröffnung", "ndr", "hit-radio", "hit radio", "nightspot",
    "polizei bigband", "entenrennen", "feuerwerk",
]

# Zusätzliche Abschnitte (kein Bühnenprogramm mit Uhrzeiten), die als
# eigenständige Highlights übernommen werden.
HIGHLIGHT_SECTION_TITLES = [
    "9. FLOHMARKT", "10. Unternehmens",
    "Krümelmonster", '"Das Gretzo"', "Härr Georg", "FlowSchule", "Entenrennen",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; GoslarAppCrawler/1.0; +https://goslar.app)"
}


def fetch_html():
    response = requests.get(SOURCE_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.text


def parse_time_range(text):
    times = TIME_RE.findall(text)
    if not times:
        return None, None
    start = (int(times[0][0]), int(times[0][1]))
    end = (int(times[1][0]), int(times[1][1])) if len(times) > 1 else None
    return start, end


def build_datetime(day_date, hm):
    hour, minute = hm
    if hour == 24:
        hour, minute = 23, 59
    return datetime.combine(day_date, datetime.min.time()).replace(hour=hour, minute=minute)


def parse_day_header(text, default_year):
    match = DAY_RE.match(text.strip())
    if not match:
        return None
    day = int(match.group(1))
    month = MONTHS.get(match.group(2).lower())
    year = int(match.group(3)) if match.group(3) else default_year
    if not month or not year:
        return None
    try:
        return datetime(year, month, day).date()
    except ValueError:
        return None


def parse_program(soup):
    """Parst das Bühnenprogramm (Stufen 1-7) in einzelne Programmpunkte."""
    events = []
    current_stage = None
    current_day = None
    default_year = None
    started = False

    for tag in soup.find_all(["h2", "h3", "p", "table"]):
        text = tag.get_text(" ", strip=True)

        if tag.name in ("h2", "h3"):
            stage_match = STAGE_RE.match(text)
            if stage_match:
                if int(stage_match.group(1)) >= 8:
                    break
                started = True
                current_stage = f"{stage_match.group(2).strip()} ({stage_match.group(3).strip()})"
                current_day = None
                continue

        if not started:
            continue

        if tag.name in ("h2", "p") and len(text) < 80:
            day_date = parse_day_header(text, default_year)
            if day_date:
                default_year = default_year or day_date.year
                current_day = day_date
                continue

        if tag.name == "table" and current_stage and current_day:
            for row in tag.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 2:
                    continue

                time_text = cells[0].get_text(" ", strip=True)
                start_hm, end_hm = parse_time_range(time_text)
                if start_hm is None:
                    continue

                title_tag = cells[1].find("strong")
                full_text = cells[1].get_text(" ", strip=True)
                title = title_tag.get_text(" ", strip=True) if title_tag else full_text[:80]
                description = full_text
                if title and description.startswith(title):
                    description = description[len(title):].strip(" -–:")

                start_dt = build_datetime(current_day, start_hm)
                end_dt = build_datetime(current_day, end_hm) if end_hm else start_dt + timedelta(minutes=30)
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                events.append({
                    "Datum": current_day.strftime("%d.%m.%Y"),
                    "Bühne": current_stage,
                    "Uhrzeit": time_text,
                    "Programm": title,
                    "Beschreibung": description,
                    "start": start_dt.isoformat(timespec="minutes"),
                    "end": end_dt.isoformat(timespec="minutes"),
                    "highlight": any(k in title.lower() for k in HIGHLIGHT_KEYWORDS),
                })

    return events


def parse_extra_highlights(soup):
    """Parst zusätzliche Programm-Highlights ohne festes Bühnen-Zeitraster."""
    highlights = []
    seen = set()
    for tag in soup.find_all(["h2", "h3"]):
        text = tag.get_text(" ", strip=True)
        if text in seen or not any(text.startswith(t) for t in HIGHLIGHT_SECTION_TITLES):
            continue
        seen.add(text)

        parts = []
        for sib in tag.find_all_next():
            if sib.name in ("h2", "h3"):
                break
            if sib.name == "p":
                s = sib.get_text(" ", strip=True)
                if s:
                    parts.append(s)
            if len(" ".join(parts)) > 320:
                break

        description = " ".join(parts)[:320].rsplit(" ", 1)[0].rstrip(",.;") + "…"
        highlights.append({"title": text, "description": description})
    return highlights


def parse_meta(soup):
    """Header-Bild und Kernbeschreibung der Veranstaltung."""
    image_url = None
    h1 = soup.find("h1")
    if h1:
        section = h1.find_parent("section")
        img = section.find("img") if section else None
        if img and img.get("src"):
            image_url = BASE_URL + img["src"]
    return {"image_url": image_url}


def build_data():
    html = fetch_html()
    soup = BeautifulSoup(html, "html.parser")

    events = parse_program(soup)
    highlights = parse_extra_highlights(soup)
    meta = parse_meta(soup)

    dates = sorted({datetime.strptime(e["Datum"], "%d.%m.%Y").date() for e in events})

    return {
        "source_url": SOURCE_URL,
        "image_url": meta["image_url"] or f"{BASE_URL}/fileadmin/_processed_/a/e/csm_altstadtfest_header_2465a82a5e.webp",
        "crawled_at": datetime.now(BERLIN_TZ).replace(tzinfo=None).isoformat(timespec="minutes"),
        "first_day": dates[0].isoformat() if dates else None,
        "last_day": dates[-1].isoformat() if dates else None,
        "events": events,
        "highlights": highlights,
    }


def save_data(data, path=DATA_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def crawl_and_save(path=DATA_FILE):
    data = build_data()
    save_data(data, path)
    return data


if __name__ == "__main__":
    result = crawl_and_save()
    print(f"{len(result['events'])} Programmpunkte und {len(result['highlights'])} Highlights gespeichert.")
    print(f"Zeitraum: {result['first_day']} bis {result['last_day']}")
