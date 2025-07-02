import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import random
import os

# Ziel-URL
url = "https://www.vhs-goslar.de/"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
export_jsonfile= "051_vhs.json"
export_alle_jsonfile = "051_vhs-alle.json"

# Ausgabe-Ordner
output_dir = "output/"
os.makedirs(output_dir, exist_ok=True)

# Hauptcontainer mit Kursen finden
hauptbereich = soup.find("div", class_="kw-highlight")
eintraege = []

if hauptbereich:
    for index,row in enumerate(hauptbereich.find_all("div", class_="kw-table-row")):
        a_tag = row.find("a")
        span_tag = row.find("span")

        if a_tag and a_tag.has_attr("href") and span_tag:
            eintrag = {
                "id": index + 1,  # ID hinzufügen
                "title": a_tag.get_text(strip=True) + "\n" + span_tag.get_text(strip=True),
                "description": span_tag.get_text(strip=True),
                "call_to_action_url": url + a_tag["href"],
                "image_url": None,
                "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
            }
            eintraege.append(eintrag)

if eintraege:
    # Alle speichern
    with open(os.path.join(output_dir, export_alle_jsonfile), "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)

    # Zufällig einen auswählen und speichern
    zufall = random.choice(eintraege)
    zufall["call_to_action_url"] = "https://crawler.goslar.app/crawler/" + export_alle_jsonfile
    with open(os.path.join(output_dir, export_jsonfile), "w", encoding="utf-8") as f:
        json.dump(zufall, f, ensure_ascii=False, indent=2)
    print(zufall)

    print("✅ Erfolgreich gespeichert.")
else:
    print("❌ Keine passenden Einträge gefunden.")
