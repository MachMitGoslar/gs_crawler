import json
import random
import threading
from datetime import datetime, timedelta
from logging import getLogger
from pathlib import Path

from flask import Flask, jsonify, render_template

import crawler

app = Flask(__name__)
logger = getLogger(__name__)

DATA_FILE = Path("data.json")
REFRESH_INTERVAL = timedelta(hours=6)

_refresh_lock = threading.Lock()
_refreshing = False


class EventStatus:
    BEFORE = "before"
    RUNNING = "running"
    PAST = "past"
    ERROR = "error"


def load_data():
    if not DATA_FILE.exists():
        return None
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fehler beim Laden von {DATA_FILE}: {e}")
        return None


def is_stale(data):
    crawled_at = data.get("crawled_at") if data else None
    if not crawled_at:
        return True
    return datetime.now() - datetime.fromisoformat(crawled_at) > REFRESH_INTERVAL


def refresh_in_background():
    global _refreshing
    with _refresh_lock:
        if _refreshing:
            return
        _refreshing = True

    def _run():
        global _refreshing
        try:
            logger.info("Aktualisiere Altstadtfest-Daten im Hintergrund...")
            crawler.crawl_and_save(DATA_FILE)
            logger.info("Altstadtfest-Daten aktualisiert.")
        except Exception as e:
            logger.error(f"Hintergrund-Crawl fehlgeschlagen: {e}")
        finally:
            with _refresh_lock:
                _refreshing = False

    threading.Thread(target=_run, daemon=True).start()


def get_data():
    """Liefert die zwischengespeicherten Daten und stößt bei Bedarf einen
    Hintergrund-Refresh an (stale-while-revalidate), damit Requests nie auf
    den Crawl warten müssen."""
    data = load_data()
    if data is None:
        try:
            data = crawler.crawl_and_save(DATA_FILE)
        except Exception as e:
            logger.error(f"Initialer Crawl fehlgeschlagen: {e}")
            return None
    elif is_stale(data):
        refresh_in_background()
    return data


def get_status(data, now=None):
    now = now or datetime.now()
    if not data or not data.get("events") or not data.get("first_day") or not data.get("last_day"):
        return EventStatus.ERROR

    first_day = datetime.fromisoformat(data["first_day"]).date()
    last_day = datetime.fromisoformat(data["last_day"]).date()
    today = now.date()

    if today < first_day:
        return EventStatus.BEFORE
    if today > last_day:
        return EventStatus.PAST
    return EventStatus.RUNNING


def find_current_or_next(events, now):
    """Sucht laufende Programmpunkte, sonst den/die nächsten für heute,
    sonst den/die ersten des nächsten Tags mit Programm."""
    today_str = now.strftime("%d.%m.%Y")
    todays = [e for e in events if e["Datum"] == today_str]

    running = [e for e in todays if datetime.fromisoformat(e["start"]) <= now <= datetime.fromisoformat(e["end"])]
    if running:
        return "running", running

    upcoming_today = sorted(
        (e for e in todays if datetime.fromisoformat(e["start"]) > now),
        key=lambda e: e["start"],
    )
    if upcoming_today:
        next_start = upcoming_today[0]["start"]
        return "next", [e for e in upcoming_today if e["start"] == next_start]

    future = sorted(
        (e for e in events if datetime.fromisoformat(e["start"]) > now),
        key=lambda e: e["start"],
    )
    if future:
        next_start = future[0]["start"]
        return "tomorrow", [e for e in future if e["start"] == next_start]

    return "none", []


def make_card(title, description, image_url, published_at=None):
    return {
        "published_at": (published_at or datetime.now()).isoformat(sep="T", timespec="minutes"),
        "title": title,
        "description": description,
        "call_to_action_url": crawler.SOURCE_URL,
        "image_url": image_url,
    }


def highlight_pool(data):
    pool = list(data.get("highlights", []))
    for e in data.get("events", []):
        if e.get("highlight"):
            pool.append({
                "title": e["Programm"],
                "description": f"{e['Datum']} | {e['Uhrzeit']} | {e['Bühne']} – {e['Beschreibung']}",
            })
    return pool


def build_card(data):
    image_url = data.get("image_url")
    status = get_status(data)

    if status == EventStatus.BEFORE:
        pool = highlight_pool(data)
        chosen = random.choice(pool) if pool else None
        description = (
            f"Highlight: {chosen['title']} – {chosen['description']}"
            if chosen else
            "Drei Tage Musik, Tanz und gute Laune erwarten euch in der Goslarer Altstadt."
        )
        return make_card("🏰 Das Altstadtfest Goslar steht vor der Tür!", description, image_url)

    if status == EventStatus.PAST:
        return make_card(
            "Danke, dass ihr dabei wart! 🎉",
            "Das Altstadtfest Goslar ist für dieses Jahr vorbei. Vielen Dank für drei wundervolle Tage "
            "Musik, Tanz und gute Laune in der Altstadt! Wir freuen uns über euer Feedback, damit das Fest "
            "im nächsten Jahr noch schöner wird.",
            image_url,
        )

    if status == EventStatus.ERROR:
        return make_card(
            "Problem beim Laden",
            "Aktuell gibt es Probleme bei der Anzeige der Programmpunkte zum Altstadtfest.",
            image_url,
        ), 500

    # RUNNING: während des Wochenendes
    now = datetime.now()
    kind, matches = find_current_or_next(data["events"], now)
    if not matches:
        last_day = datetime.fromisoformat(data["last_day"]).date()
        if now.date() >= last_day:
            # Letzter Programmpunkt des Festes ist bereits vorbei.
            return make_card(
                "Danke, dass ihr dabei wart! 🎉",
                "Das Altstadtfest Goslar ist für dieses Jahr vorbei. Vielen Dank für drei wundervolle Tage "
                "Musik, Tanz und gute Laune in der Altstadt! Wir freuen uns über euer Feedback, damit das Fest "
                "im nächsten Jahr noch schöner wird.",
                image_url,
            )
        return make_card(
            "Das Altstadtfest Goslar ist für heute vorbei!",
            "Für heute ist Schluss – wir sehen uns morgen wieder auf dem Altstadtfest!",
            image_url,
        )

    chosen = random.choice(matches)
    program_line = f"{chosen['Uhrzeit']} | {chosen['Bühne']} | {chosen['Programm']}"

    if kind == "running":
        title = "🎪 Jetzt live beim Altstadtfest"
        description = f"Gerade auf der Bühne: {program_line}"
    elif kind == "next":
        title = "🎪 Als Nächstes beim Altstadtfest"
        description = f"Kommt gleich: {program_line}"
    else:
        title = "🎪 Das Altstadtfest Goslar geht weiter"
        description = f"Für heute ist Schluss. Es geht weiter mit: {program_line}"

    return make_card(title, description, image_url, published_at=datetime.fromisoformat(chosen["start"]))


@app.route('/api/card.json')
def api_card():
    """API Endpoint für die Kachel: Highlights vorher, aktuelles Programm
    während, Dank & Feedback-Aufruf danach."""
    data = get_data()
    if not data:
        return jsonify(make_card(
            "Problem beim Laden",
            "Aktuell gibt es Probleme bei der Anzeige der Programmpunkte zum Altstadtfest.",
            None,
        )), 500

    result = build_card(data)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.route('/api/programm.html')
def api_programm():
    """Vollständige Programmübersicht nach Bühne und Tag gruppiert."""
    data = get_data()
    if not data:
        return jsonify({"error": "Keine Programmdaten verfügbar"}), 404

    stages = {}
    for event in data["events"]:
        stages.setdefault(event["Bühne"], {}).setdefault(event["Datum"], []).append(event)

    return render_template(
        "programm.html",
        stages=stages,
        highlights=data.get("highlights", []),
        image_url=data.get("image_url"),
        source_url=crawler.SOURCE_URL,
    )


@app.route('/health')
def health():
    """Health Check Endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "altstadtfest-api",
    })


if __name__ == "__main__":
    print("🎪 Altstadtfest API gestartet auf http://0.0.0.0:5000")
    print("Endpoints:")
    print("  /api/card.json    - Kachel (Highlights / aktuelles Programm / Danke & Feedback)")
    print("  /api/programm.html - Vollständige Programmübersicht")
    print("  /health            - Health Check")

    app.run(host='0.0.0.0', port=5000, debug=True)
