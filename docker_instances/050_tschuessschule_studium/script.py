import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import time
import random


# variablen
json_all = "050-tschuessschule-studium-alle.json"
json_one = "050-tschuessschule-studium.json"
title = "Studienangebote"

# Zielseite
url = "https://tschuessschule.de/studienangebote/"
url_short = "https://tschuessschule.de"
page = requests.get(url)

soup = BeautifulSoup(page.text, "html.parser")

# Speicherpfad
output_dir = "output/"
os.makedirs(output_dir, exist_ok=True)

eintraege = []

# Alle <div class="container">-Blöcke durchlaufen
container_divs = soup.find_all("div", class_="container")

for container in container_divs:
    # Beschreibung aus <h3>
    beschreibung_tag = container.find("h3")
    beschreibung = beschreibung_tag.get_text(strip=True) if beschreibung_tag else title

    # Untereinträge mit class="unternehmen"
    unternehmen_divs = container.find_all("div", class_="unternehmen")

    for unternehmen in unternehmen_divs:
        veranstaltungen = unternehmen.find_all("div", class_="veranstaltung")
        if len(veranstaltungen) >= 2:
            # Bild
            img_tag = veranstaltungen[0].find("img")
            image_url = url_short + img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

            # Link
            call_to_action_url = url + "#" + unternehmen["id"] 

            # Datensatz anlegen
            eintraege.append({
                "title": title,
                "description": beschreibung,
                "image_url": image_url,
                "call_to_action_url": call_to_action_url,
                "published_at": ""
            })
for index,eintrag in enumerate(eintraege):
    eintrag["id"] = eintraege.index(eintrag) + 1  # ID hinzufügen

# JSON-Ausgabe
if eintraege:
    anzahl_eintraege = len(eintraege)
    zufall = random.choice(eintraege)
    zufall["description"] = str(anzahl_eintraege) + " Angebote, z. B.\n\n" + zufall["description"]
    zufall["call_to_action_url"] = "https://crawler.goslar.app/crawler/" + json_all

    with open(os.path.join(output_dir, json_all), "w", encoding="utf-8") as f_all:
        json.dump(eintraege, f_all, ensure_ascii=False, indent=2)

    with open(os.path.join(output_dir, json_one), "w", encoding="utf-8") as f_one:
        json.dump(zufall, f_one, ensure_ascii=False, indent=2)

    print("✅ JSON-Dateien erfolgreich gespeichert.")
else:
    print("❌ Keine Praktikumsangebote gefunden.")