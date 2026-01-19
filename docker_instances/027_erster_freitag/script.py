import requests
from bs4 import BeautifulSoup
import random
import json
from urllib.parse import urljoin
import os
from datetime import datetime

def generateDefault(message, savemepath, filename):
    now = datetime.now()
    default_entry = {
        "title": "1. Freitag Goslar",
        "image_url": "https://www.meingoslar.de/fileadmin/_processed_/7/5/csm_csm_20250404_abendshopping_bettgefluester_032__img_9909__e099172733_e9af754d10.jpg",
        "description": "Der 1. Freitag in Goslar bietet Kunst, Kultur und Shopping bis in die Abendstunden.",
        "call_to_action_url": "https://www.meingoslar.de/erleben-und-geniessen/erster-freitag",
        "published_at": now.strftime("%d.%m.%Y %H:%M:%S")
    }
    with open(os.path.join(savemepath, filename), "w", encoding="utf-8") as f:
        json.dump(default_entry, f, ensure_ascii=False, indent=2)
    print(message + "\n Generiere Standard-Eintrag:")
    print(json.dumps(default_entry, indent=2, ensure_ascii=False))
    exit(0)


# URL und Zielseite
url = "https://insides.goslar-app.de/1-freitag-goslar"
call_to_action_url = "https://www.meingoslar.de/erleben-und-geniessen/erster-freitag"
filename = "027-erster-freitag.json"
# Seite laden
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
savemepath = "output/"

# nächsten Termin ermitteln
termine = ["2025-06-06T18:00", "2025-07-04T18:00", "2025-08-01T18:00", "2025-09-05T18:00", "2025-10-10T18:00", "2025-11-07T18:00"]
# In Datetime-Objekte umwandeln
termine_dt = [datetime.strptime(t, "%Y-%m-%dT%H:%M") for t in termine]

# Aktuelle Zeit
jetzt = datetime.now()

# Nur zukünftige Termine
zukuenftige = [t for t in termine_dt if t > jetzt]

# Nächsten Termin finden
if zukuenftige:
    naechster = min(zukuenftige)
    print("📅 Nächster Termin:", naechster.strftime("%Y-%m-%d %H:%M"))
else:
    generateDefault("Keine zukünftigen Termine gefunden.", savemepath, filename )



# Start: <div id="1-freitag-goslar">
start_div = soup.find("div", id="1-freitag-goslar")
if not start_div:
    generateDefault("Start-Div mit ID '1-freitag-goslar' nicht gefunden.")
    exit()

# Ergebnisse sammeln
eintraege = []

# Durch alle <div class="block_textimage"> nach start_div iterieren
current_div = start_div.find_next("div", class_="block_textimage")

while current_div:
    # Bild holen
    img_tag = current_div.find("img")
    image_url = urljoin(url, img_tag["src"]) if img_tag and img_tag.get("src") else None

    # Beschreibung holen
    beschreibung_tag = current_div.find_next("p")
    beschreibung = beschreibung_tag.get_text(strip=True) if beschreibung_tag else None

    if image_url and beschreibung:
        eintraege.append({
            "title": "1. Freitag Goslar",
            "image_url": image_url,
            "description": beschreibung,
            "call_to_action_url": call_to_action_url,
            "published_at": naechster.strftime("%Y-%m-%d %H:%M")
        })

    # Nächster block_textimage-Block
    current_div = current_div.find_next("div", class_="block_textimage")

# Zufälligen Eintrag wählen
if eintraege:
    zufall = random.choice(eintraege)

    # Optional speichern
    with open(os.path.join(savemepath, filename), "w", encoding="utf-8") as f:
        json.dump(zufall, f, ensure_ascii=False, indent=2)

    print("✅ Zufälliger Eintrag:")
    print(json.dumps(zufall, indent=2, ensure_ascii=False))

else:
    generateDefault("Keine passenden Einträge gefunden.")
