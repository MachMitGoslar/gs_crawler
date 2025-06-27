import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import random
import os

# URL der Quelle
url = "https://dg-wiedelah.de/category/arbeitseinsaetze/"

# Anfrage und HTML parsen
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Alle Einträge finden
container = soup.find("div", id="categort-posts-widget-5")
widget = container.find("div", class_="widget-container") if container else None
ul = widget.find("ul") if widget else None
li_tags = ul.find_all("li") if ul else []

entries = []
for index, li in enumerate(li_tags):
    div = li.find("div")
    a_tag = div.find("a", href=True) if div else None
    call_to_action_url = a_tag["href"] if a_tag else ""
    
    img_tag = a_tag.find("img") if a_tag else None
    image_url = img_tag["src"] if img_tag else ""

    h3 = li.find("h3") if div else None
    
    a_tag = h3.find("a") if div else None
    description = a_tag.get_text(strip=True) if a_tag else ""

    # call_to_action_url = a_tag["href"] if a_tag else ""

    span_tag = li.find("span", class_="tie-date")
    date_text = span_tag.get_text(strip=True) if span_tag else ""

    # Datum umwandeln in datetime-Objekt (mit deutschem Format)
    try:
        date_obj = datetime.strptime(date_text, "%d. %B %Y")
    except ValueError:
        # Fallback für Monatsnamen (z. B. Juni) ins Englische konvertieren
        month_map = {
            "Januar": "January", "Februar": "February", "März": "March",
            "April": "April", "Mai": "May", "Juni": "June",
            "Juli": "July", "August": "August", "September": "September",
            "Oktober": "October", "November": "November", "Dezember": "December"
        }
        for de, en in month_map.items():
            date_text = date_text.replace(de, en)
        date_obj = datetime.strptime(date_text, "%d. %B %Y")

    # Datum ins Format yyyy-mm-ddThh:00 umwandeln
    published_at = date_obj.strftime("%Y-%m-%dT%H:00")

    entry = {
        "id": index,
        "title": published_at,
        "description": description,
        "call_to_action_url": call_to_action_url,
        "image_url": image_url,
        "published_at": published_at
    }
    entries.append(entry)

# Unterverzeichnis erstellen
os.makedirs("output", exist_ok=True)

# Zufälligen Eintrag speichern
if entries:
    zufall = random.choice(entries)
    with open("output/044-wiedelah.json", "w", encoding="utf-8") as f:
        json.dump(zufall, f, ensure_ascii=False, indent=2)
    print(zufall)
    print("✅ JSON-Datensatz erfolgreich gespeichert in 'ergebnis/arbeitseinsaetze_eintrag.json'")
    with open("output/044-wiedelah_alle.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
else:
    print("❌ Keine Arbeitseinsätze gefunden.")
