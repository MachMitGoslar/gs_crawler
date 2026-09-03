import requests
from PIL import Image
from io import BytesIO
import os
from datetime import datetime
from bs4 import BeautifulSoup
import json
from helpers import ensure_directory_exists
# Pfade
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "output", "019_was_app.json")
ensure_directory_exists(output_path)

# === MACHMIT.WASAPP ===
url_wasapp = "https://machmit.goslar.de/projects/01-goslar-app"
response = requests.get(url_wasapp)
soup = BeautifulSoup(response.text, "html.parser")

timeline_container = soup.find("div", class_="project-step-timeline-container")
headline = timeline_container.find_next("h4", class_="project-step-timeline-title") if timeline_container  else None
print(headline.get_text(strip=True) if headline else None)
description_element_wrapper = timeline_container.find_next("div", class_="project-step-timeline-text") if timeline_container else None
print(description_element_wrapper.get_text(strip=True) if description_element_wrapper else None)
description_element = description_element_wrapper.find_next("p") if description_element_wrapper else None
print(description_element.get_text(strip=True) if description_element else None)
image_div = soup.find("div", class_="c-hero")
image_url = image_div.find("img")["src"] if image_div and image_div.find("img") else "" 
jetzt = datetime.now()
timeline_date_entry = timeline_container.find("div", class_="project-step-timeline-date") if timeline_container else None
published_at = jetzt.strftime("%Y-%m-%dT%H:00")

description_text = " ".join([
    headline.get_text(strip=True) if headline else "",
    description_element.get_text(strip=True) if description_element else ""
]).strip()

# datensaetze = []
if description_text:
            
    datensatz = {
        "published_at": timeline_date_entry.get_text(strip=True) if timeline_date_entry else published_at,
        "title": "WasApp?",
        "description": description_text,
        "image_url": image_url,
        "call_to_action_url": "https://machmit.goslar.de/projects/01-goslar-app"
    }

    # os.makedirs("ergebnis", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(datensatz, f, ensure_ascii=False, indent=2)

    print(str(jetzt) + " - 019: " + description_text)
    print("✅ 1 Eintrag aus WasApp-Tabelle gespeichert.")
else:
    print("❌ Tabelle auf der WasApp-Seite nicht gefunden.")

