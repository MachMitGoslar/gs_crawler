import requests
from PIL import Image
from io import BytesIO
import os
from datetime import datetime
from bs4 import BeautifulSoup
import json
from helpers import ensure_directory_exists

# ---- Webcam-Teil bleibt erhalten ----

# === NEUE QUELLE: Harzer Panorama ===

url = "https://www.panorama-am-sonntag.de/"
FILE_PATH = "./output/040_hp.json"
ensure_directory_exists(FILE_PATH);

response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
ensure_directory_exists(os.path.dirname(FILE_PATH))

epaper_div = soup.find("div", class_="epaper")

link_tag = epaper_div.find("a", href=True) if epaper_div else None
if link_tag:
    call_to_action_url = f"https://www.panorama-am-sonntag.de/{link_tag['href']}"
    img_tag = link_tag.find("img")
    image_url = f"https://www.panorama-am-sonntag.de/{img_tag['src']}" if img_tag and img_tag.has_attr("src") else None

    daten = {
        "title": "Harzer Panorama",
        "description": "Aktuelle Ausgabe des Harzer Panorama",
        "image_url": image_url or "https://machmit.goslar.de/fileadmin/media-machmit/goslar-app/leider_keine_bild_720x720.png",
        "call_to_action_url": call_to_action_url,
        "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
    }


    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

    print("✅ Harzer Panorama JSON erstellt:")
    print(json.dumps(daten, ensure_ascii=False, indent=2))
else:
    print("❌ Kein PDF-Link gefunden auf der Panorama-Seite.")
