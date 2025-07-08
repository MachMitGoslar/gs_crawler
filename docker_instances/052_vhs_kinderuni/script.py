import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import random
import os

# Ziel-URL
url = "https://www.vhs-goslar.de/programm/junge-vhs-kurse-fuer-kinder-und-jugendliche/kategorie/Junge+vhs+-+Kurse+fuer+Kinder+und+Jugendliche/41"
url_base = "https://www.vhs-goslar.de" 
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
export_jsonfile = "052_vhs_kinderuni.json"
export_alle_jsonfile = "052_vhs_kinderuni_alle.json"

# Ausgabe-Ordner
output_dir = "output/"
os.makedirs(output_dir, exist_ok=True)

# Hauptcontainer mit Kursen finden
hauptbereich = soup.find("div", class_="kw-kursuebersicht")
eintraege = []

if hauptbereich:
    for index, row in enumerate(hauptbereich.find_all("div", class_="kw-table-row")):
        a_tag = row.find("a")
        span_tag = row.find("div", class_="col-sm-4")

        if a_tag and a_tag.has_attr("href") and span_tag:
            eintrag = {
                "id": index + 1,  # ID hinzufügen
                "title": span_tag.get_text(strip=True),
                "description": "",
                "call_to_action_url": url_base + a_tag["href"],
                "image_url": None,
                "published_at": None
            }
            eintraege.append(eintrag)

if eintraege:
    # Alle speichern
    with open(os.path.join(output_dir, export_alle_jsonfile), "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)

    # Zufällig einen auswählen und speichern
    zufall = random.choice(eintraege)
    zufall["description"] = zufall["title"] + " " + zufall["description"]
    zufall["title"] = "VHS Kinderuni"
    zufall["published_at"] = None    
    zufall["call_to_action_url"] = "https://crawler.goslar.app/crawler/" + export_alle_jsonfile
    with open(os.path.join(output_dir, export_jsonfile), "w", encoding="utf-8") as f:
        json.dump(zufall, f, ensure_ascii=False, indent=2)
    print(zufall)

    print("✅ Erfolgreich gespeichert.")
else:
    print("❌ Keine passenden Einträge gefunden.")
