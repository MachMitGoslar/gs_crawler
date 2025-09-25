import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import random
import os

# URL der Quelle
url = "https://dg-wiedelah.de/category/berichte-von-veranstaltungen/"

# Anfrage und HTML parsen
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

# Alle Einträge finden
container = soup.find("div", id="main-content")
widget = container.find("div", class_="post-listing") if container else None
li_tags = widget.find_all("article") if widget else []

entries = []
for index, li in enumerate(li_tags):
    div = li.find("h2")
    a_tag = div.find("a", href=True) if div else None
    call_to_action_url = a_tag["href"] if a_tag else "https://dg-wiedelah.de/"
    
    img_tag = a_tag.find("img") if a_tag else None
    image_url = img_tag["src"] if img_tag else ""

    div_beschreibung = li.find("div", class_="entry") if div else None
    
    p_tag = div_beschreibung.find("p") if div else None
    description = p_tag.get_text(strip=True) if p_tag else ""

    # call_to_action_url = a_tag["href"] if a_tag else ""

    span_tag = li.find("span", class_="tie-date")
    date_text = span_tag.get_text(strip=True) if span_tag else ""

    # Datum leer
    published_at = ""

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
    # zufall = random.choice(entries)
    zufall = entries[0]
    with open("output/044-wiedelah.json", "w", encoding="utf-8") as f:
        json.dump(zufall, f, ensure_ascii=False, indent=2)
    print(zufall)
    print("✅ JSON-Datensatz erfolgreich gespeichert in 'ergebnis/arbeitseinsaetze_eintrag.json'")
    with open("output/044-wiedelah_alle.json", "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
else:
    print("❌ Keine Arbeitseinsätze gefunden.")

