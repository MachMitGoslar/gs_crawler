import json
import os
import random
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

# Naturgefahrenportal (DWD/BBK) stellt die Warndaten, die seine Karte anzeigt,
# selbst als offenes JSON bereit (dieselbe Quelle, die das Frontend lädt).
# Das ist stabiler als HTML/CSS zu parsen, das sich bei jedem Frontend-Deploy
# ändern kann.
DWD_ALERTS_URL = "https://www.naturgefahrenportal.de/data/v2/alerts/dwd.json"
MOWAS_ALERTS_URL = "https://www.naturgefahrenportal.de/data/v2/alerts/mowas.json"
NATURGEFAHRENPORTAL_URL = "https://www.naturgefahrenportal.de/de/alerts"

INSIDES_URL = "https://insides.goslar-app.de/bevoelkerungsschutz"
FALLBACK_URL = "https://www.goslar.de/stadt-und-verwaltung/verwaltung/brand-und-katastrophenschutz/selbstschutz-und-notfallvorsorge"

ADRESSE = "Charley-Jacob-Str. 3, 38640 Goslar"
# Einmalig via Nominatim (OpenStreetMap) geokodiert. Die Adresse ist fix,
# daher wird hier nicht bei jedem Cron-Lauf erneut geokodiert.
ADRESSE_LAT = 51.9063874
ADRESSE_LON = 10.4301325

SEVERITY_LABELS = {
    1: "Geringe Warnstufe",
    2: "Mäßige Warnstufe",
    3: "Hohe Warnstufe",
    4: "Extreme Warnstufe",
}

REQUEST_HEADERS = {"User-Agent": "gs_crawler-045-naturgefahren/1.0 (+https://goslar-app.de)"}


def point_in_ring(x, y, ring):
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def point_in_polygon(x, y, coordinates):
    if not point_in_ring(x, y, coordinates[0]):
        return False
    return not any(point_in_ring(x, y, hole) for hole in coordinates[1:])


def point_in_geometry(x, y, geometry):
    gtype = geometry.get("type")
    if gtype == "Polygon":
        return point_in_polygon(x, y, geometry["coordinates"])
    if gtype == "MultiPolygon":
        return any(point_in_polygon(x, y, polygon) for polygon in geometry["coordinates"])
    return False


def is_active(properties, now):
    if properties.get("status") != "Actual" or properties.get("msgType") == "Cancel":
        return False
    expires = properties.get("expires")
    if expires:
        try:
            if datetime.fromisoformat(expires) < now:
                return False
        except ValueError:
            pass
    return True


def matching_warnings(alerts_url, lon, lat, now):
    response = requests.get(alerts_url, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()
    features = response.json().get("features", [])

    matches = []
    for feature in features:
        properties = feature.get("properties", {})
        if not is_active(properties, now):
            continue
        if point_in_geometry(lon, lat, feature.get("geometry", {})):
            matches.append(properties)
    return matches


def pick_strongest_warning(lon, lat):
    now = datetime.now(timezone.utc)
    matches = (
        matching_warnings(DWD_ALERTS_URL, lon, lat, now)
        + matching_warnings(MOWAS_ALERTS_URL, lon, lat, now)
    )
    if not matches:
        return None
    matches.sort(key=lambda p: p.get("severity", 0), reverse=True)
    return matches[0]


def fallback_bevoelkerungsschutz_artikel():
    try:
        response = requests.get(INSIDES_URL, headers=REQUEST_HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"⚠️  insides.goslar-app.de nicht erreichbar: {exc}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    hauptbereich = soup.find("div", id="bevoelkerungsschutz")
    eintraege = hauptbereich.find_all("div", class_="block_textimage") if hauptbereich else []
    if not eintraege:
        print("⚠️  Keine Bevölkerungsschutz-Einträge auf insides.goslar-app.de gefunden")
        return None

    result = random.choice(eintraege)
    text_div = result.find("div", class_="wrap_text_left")
    p_tags = text_div.find_all("p") if text_div else []
    beschreibung = p_tags[0].get_text(strip=True) if p_tags else ""
    a_tag = p_tags[1].find("a") if len(p_tags) >= 2 else None
    link = a_tag["href"] if a_tag and a_tag.has_attr("href") else FALLBACK_URL

    if not beschreibung:
        return None
    return beschreibung, link


zeitstempel = time.strftime("%d.%m.%Y - %H:%M")
warnung = pick_strongest_warning(ADRESSE_LON, ADRESSE_LAT)

if warnung:
    warnstufe = SEVERITY_LABELS.get(warnung.get("severity"), "Warnstufe")
    headline = (warnung.get("headline") or {}).get("de", "").strip()
    erlaeuterung = (warnung.get("description") or {}).get("de", "").strip()
    description = f"{zeitstempel}:\n{warnstufe}: {headline}\n{erlaeuterung}".strip()
    target_url = warnung.get("web") or NATURGEFAHRENPORTAL_URL
else:
    fallback = fallback_bevoelkerungsschutz_artikel()
    if fallback:
        beschreibung, target_url = fallback
        description = "aktuell keine Warnung: \n" + beschreibung
    else:
        description = f"{zeitstempel}: Es liegen keine Warnungen für {ADRESSE} vor."
        target_url = FALLBACK_URL

data = {
    "title": "Naturgefahren",
    "description": description,
    "call_to_action_url": target_url,
    "image_url": "https://crawler.goslar.app/crawler/045_naturgefahren/mowas.svg",
    "published_at": zeitstempel
}

os.makedirs("output", exist_ok=True)
os.makedirs("045_naturgefahren", exist_ok=True)
with open("/output/045_naturgefahren/045_naturgefahren_de.json", "x", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Ergebnis gespeichert in '{output_file}'")
print(json.dumps(data, ensure_ascii=False, indent=2))
