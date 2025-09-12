from unittest import case
import requests
from PIL import Image
from io import BytesIO
import os
import random
from datetime import datetime, timedelta
import json
import random
from flask import Flask, jsonify, request, render_template
from logging import getLogger
# from helpers import ensure_directory_exists

app = Flask(__name__)
logger = getLogger(__name__)


class EventStatus:
    BEFORE = "before"
    RUNNING = "running"
    UPCOMING = "upcoming"
    PAST = "past"
    ERROR = "error"

BASE_URL = "http://crawler.goslar.app/api/"

def parse_time_safe(timestr: str):
    """Hilfsfunktion: Wandelt Zeitstring in time-Objekt, behandelt '24:00' als 23:59."""
    timestr = timestr.strip()
    if timestr == "24:00":
        timestr = "23:59"
    return datetime.strptime(timestr, "%H:%M").time()

def get_events_for_checktime(events, check_datetime=None):
    if check_datetime is None:
        check_datetime = datetime.now()
    print(f"Checkzeitpunkt: {check_datetime}")
    # Veranstaltungen nach Datum gruppieren
    events_by_date = {}
    all_event_dates = []
    for event in events:
        try:
            event_date = datetime.strptime(event["Datum"], "%d.%m.%Y").date()
            all_event_dates.append(event_date)
            events_by_date.setdefault(event_date, []).append(event)
        except Exception as e:
            print(f"Fehler bei Event {event}: {e}")

    if not all_event_dates:
        return {
            "status": EventStatus.ERROR,
            "message": {
                "published_at": check_datetime.isoformat(sep='T', timespec='minutes'),
                "title": "Problem",
                "description": "Aktuell gibt es Probleme bei der Anzeige der Veranstaltungen.",
                "call_to_action_url": "https://www.meingoslar.de/veranstaltungen/altstadtfest",
                "image_url": "https://www.meingoslar.de/fileadmin/_processed_/a/e/csm_altstadtfest_header_2465a82a5e.webp"
            }, 
            "events": []
            }

    first_day = min(all_event_dates)
    last_day = max(all_event_dates)
    current_day = check_datetime.date()

    # --- Regel 3: nach letztem Veranstaltungstag
    if current_day > last_day:

        return {
            "status": EventStatus.PAST,
            "message": {
                "published_at": last_day.isoformat(sep='T', timespec='minutes'),
                "title": "Wir sehen uns nächstes Jahr!",
                "description": "Das Altstadtfest in Goslar findet nächstes Jahr wieder statt. Bis dahin, bleibt gesund!",
                "call_to_action_url": "https://www.meingoslar.de/veranstaltungen/altstadtfest",
                "image_url": "https://www.meingoslar.de/fileadmin/_processed_/a/e/csm_altstadtfest_header_2465a82a5e.webp"
                },
            "events": []
        }

    # --- Regel 2: vor erstem Veranstaltungstag
    if current_day < first_day:

        day_events = events_by_date[first_day]
        return {
                "status": EventStatus.BEFORE,
                "message": {
                    "published_at": first_day.isoformat(sep='T', timespec='minutes'),
                    "title": "Das Altstadtfest in Goslar startet bald!",
                    "description": "Freut euch auf tolle Veranstaltungen beim Altstadtfest in Goslar. Bis dahin, bleibt gesund!",
                    "call_to_action_url": "https://www.meingoslar.de/veranstaltungen/altstadtfest",
                    "image_url": "https://www.meingoslar.de/fileadmin/_processed_/a/e/csm_altstadtfest_header_2465a82a5e.webp"
                },
                "events": []       
            }

    # --- Regel 1: Tag = Veranstaltungstag
    if current_day in events_by_date:
        # Events des Tages nach Startzeit sortieren
        day_events = sorted(
            events_by_date[current_day],
            key=lambda e: parse_time_safe(e["Uhrzeit"].split("-")[0])
        )
                


        # Prüfen ob Matches zum Abfragezeitpunkt laufen
        running = []
        for ev in day_events:

            start_str, end_str = ev["Uhrzeit"].split("-")
            start_dt = datetime.combine(current_day, parse_time_safe(start_str))
            if start_dt > check_datetime:
                running.append(ev)

        return { 
            "status": EventStatus.RUNNING,
            "message": "",
            "events": running,
        }

        return []  # keine Matches und keine kommenden mehr → leer

    return []


def load_events():
    """Lädt Events aus der JSON-Quelle"""
    """json_data = BASE_URL + "events.json"""

    with open('./events.json') as json_data:
        try:
            d = json.load(json_data)
            print("Events geladen")
            json_data.close()
            return d
        except Exception as e:
            print(f"Fehler beim Laden der Events: {e}")
            return []

    
def format_event(event):
    # Felder aus JSON holen
    print("Event:", event)
    datum = event.get("Datum", "")
    bühne = event.get("Bühne", "")
    uhrzeit = event.get("Uhrzeit", "")
    programm = event.get("Programm", "")

    # neue Struktur
    return ({
        "published_at": datum+"T"+uhrzeit.split("-")[0],

        "title": "Empfehlung",
        "description": f"{uhrzeit} | {bühne} | {programm}",
        "call_to_action_url": "https://www.meingoslar.de/veranstaltungen/altstadtfest",
        "image_url": "https://www.meingoslar.de/fileadmin/_processed_/a/e/csm_altstadtfest_header_2465a82a5e.webp"
    })

def format_events(events):
    """Formatiert Events in die gewünschte Struktur"""
    results = []
    for ev in events:
        results.append(format_event(ev))
    return results


@app.route('/api/card.json')
def api_current():
    """API Endpoint für die aktuelle oder nächste Veranstaltung"""
    events = load_events()
    if not events:
        return jsonify({"error": "Keine Veranstaltungen verfügbar"}), 404
    
    now = datetime.now()
    logger.info(f"Aktueller Checkzeitpunkt: {now}")
    result_structure = get_events_for_checktime(events, now)

    match result_structure['status']:
        case EventStatus.ERROR:
            return jsonify(result_structure["message"]), 500
        case EventStatus.PAST:
            return jsonify(result_structure["message"])
        case EventStatus.BEFORE:
            return jsonify(result_structure["message"])
        case EventStatus.UPCOMING:
            pass
        case EventStatus.RUNNING:
            pass
            # Weiterverarbeitung unten

    if len(result_structure["events"]) > 0:
        formatted_events = format_events(result_structure["events"])
        
        r_number = random.randint(0, len(formatted_events) - 1)
        selected_event = formatted_events[r_number]
        selected_event["call_to_action_url"] = BASE_URL + "programm.html"
        selected_event["description"] = "Empfehlung: " + selected_event["description"]
        return jsonify(selected_event)

    if len(result_structure["events"]) == 0:
         return jsonify({
                    "published_at": datetime.now().isoformat(sep='T', timespec='minutes'),
                    "title": "Das Altstadtfest in Goslar ist für heute vorbei!",
                    "description": "Das Altstadtfest in Goslar ist für heute vorbei. Wir sehen uns morgen wieder! Mehr zu unserem Programm",
                    "call_to_action_url": "https://www.meingoslar.de/veranstaltungen/altstadtfest",
                    "image_url": "https://www.meingoslar.de/fileadmin/_processed_/a/e/csm_altstadtfest_header_2465a82a5e.webp"
         })

    formatted_events = format_events(result_structure)
    
@app.route('/api/programm.html')
def api_programm():
    """API Endpoint für das Programm"""
    events = load_events()
    if not events:
        return jsonify({"error": "Keine Veranstaltungen verfügbar"}), 404

    return render_template("test.html", events=events)

@app.route('/health')
def health():
    """Health Check Endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "altstadtfest-api"
    })


if __name__ == "__main__":
    print("🎪 Altstadtfest API gestartet auf http://0.0.0.0:5000")
    print("Endpoints:")
    print("  / - Alle kommenden Veranstaltungen")
    print("  /api/current - Aktuelle/nächste Veranstaltung")
    print("  /api/events - Alle kommenden Veranstaltungen")
    print("  /api/random - Zufällige Veranstaltung")
    print("  /health - Health Check")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

