import requests
from bs4 import BeautifulSoup
import random
import json
from datetime import datetime
import locale
import os
from datetime import date, timedelta

# Optional: Deutsches Datumsformat setzen (z. B. für "April")
try:
    locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
except:
    pass  # ignorieren, wenn z. B. Windows ohne Locale

# Zielseite
url = "https://www.goslarer-geschichten.de/forum.php"
base_url = "https://www.goslarer-geschichten.de"
image_url = "https://machmit.goslar.de/fileadmin/media-machmit/goslar-app/einmarsch.gif"
export_jsonfile = "031-goslarer_geschichten.json"

# HTML abrufen
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Ausgabe-Ordner
output_dir = "output/"
os.makedirs(output_dir, exist_ok=True)

# Tabelle mit class="blockbody" finden
table = soup.find("table", class_="blockbody")
if not table:
    print("❌ Tabelle nicht gefunden.")
    exit()

# Alle Datenzeilen (ohne Überschrift)
rows = table.find_all("tr")[1:]

eintraege = []

for row in rows:
    cols = row.find_all("td")
    if len(cols) >= 4:
        # Spalte 1: <a> Text + Link
        link_tag = cols[1].find("a")
        if not link_tag:
            continue  # Überspringen, wenn kein Link
        beschreibung = link_tag.get_text(strip=True)
        link_url = link_tag.get("href", "").strip()
        if link_url.startswith("/"):
            link_url = base_url + link_url

        # Spalte 4: Datum & Uhrzeit
        datum_raw = cols[2].get_text(strip=True).replace("Letzter Beitrag: ", "")

        if datum_raw[:5] == "Heute":
            heute_str = date.today().strftime("%d.%m.%Y")
            datum_raw = datum_raw.replace("Heute", heute_str)
        elif datum_raw[:7] == "Gestern":
            heute_str = date.today().strftime("%d.%m.%Y")
            heute_str = datetime.strptime(heute_str, "%d.%m.%Y") - timedelta(days=1)
            heute_str = heute_str.strftime("%d.%m.%Y")
            datum_raw = datum_raw.replace("Gestern", heute_str)

        kurz = datum_raw[:15]  # ergibt "09.05.202515:31"
    
        dt = datetime.strptime(kurz, "%d.%m.%Y%H:%M")

        try:            
            # Ausgabeformat: ISO 8601
            published_at = dt.strftime("%Y-%m-%dT%H:%M")
        except Exception:
            published_at = datetime.now().strftime("%Y-%m-%dT%H:%M")  # Fallback

        eintraege.append({
            "title": "Goslarer Geschichten – Forum",
            "description": beschreibung,
            "image_url": image_url,
            "call_to_action_url": link_url,
            "published_at": published_at
        })

# Zufälligen Eintrag wählen
if eintraege:
    eintrag = random.choice(eintraege)

    with open(os.path.join(output_dir, export_jsonfile), "w", encoding="utf-8") as f:
        json.dump(eintrag, f, ensure_ascii=False, indent=2)

    print("✅ Zufälliger Eintrag gespeichert:")
    print(json.dumps(eintrag, ensure_ascii=False, indent=2))
else:
    print("❌ Keine gültigen Datenzeilen gefunden.")
