from bs4 import BeautifulSoup
from datetime import datetime
import requests
import json
import os
import random


# Zielseite aufrufen
url = "https://www.goslarsche.de/lokales/Goslar"
site = requests.get(url)

# HTML holen und parsen
soup = BeautifulSoup(site.text, "html.parser")

# Speicherpfad vorbereiten
savemepath = os.path.join(os.getcwd(), "output")
os.makedirs(savemepath, exist_ok=True)

eintraege = []

# Alle relevanten Artikel finden
artikel = soup.find_all("article", class_="StoryPreviewBox")

for index,art in enumerate(artikel):
    # Bild
    image_url = None
    picture_container = art.find("div", class_="PictureContainer")
    if picture_container:
        img_tag = picture_container.find("img")
        if img_tag and img_tag.has_attr("src"):
            image_url = img_tag["src"]

    # Titel und Link
    title = ""
    call_to_action_url = ""
    heading = art.find("h2", class_="article-heading")
    if heading:
        a_tag = heading.find("a")
        if a_tag:
            title = a_tag.get_text(strip=True)
            call_to_action_url = a_tag.get("href", "")

    # Beschreibung
    description = ""
    desc_container = art.find("div", class_="article-preview")
    if desc_container and len(desc_container) > 1:
        description = desc_container.get_text(strip=True)

    # Datensatz speichern
    if title:
        eintraege.append({
            "id": index+1,
            "title": title,
            "description": description,
            "image_url": url + image_url,
            "call_to_action_url": url + call_to_action_url,
            "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
        })

# JSON-Dateien schreiben
if eintraege:
    with open(os.path.join(savemepath, "002_goslarsche-alle.json"), "w", encoding="utf-8") as f:
        json.dump(eintraege, f, ensure_ascii=False, indent=2)

    zufall = eintraege[0]
    zufall["call_to_action_url"] = "https://crawler.goslar.app/crawler/002_goslarsche-alle.json"
    with open(os.path.join(savemepath, "002_goslarsche.json"), "w", encoding="utf-8") as f:
        json.dump(zufall, f, ensure_ascii=False, indent=2)

    print("✅ Lead Artikel:", zufall)
else:
    print("❌ Keine passenden Artikel gefunden.")
