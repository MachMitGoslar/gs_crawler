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
url_wasapp = "https://machmit.goslar.de/wasapp"
response = requests.get(url_wasapp)
soup = BeautifulSoup(response.text, "html.parser")

h1_tag = soup.find("section", class_="takuma_teaser")
wasapp_table = h1_tag.find_next("span", class_="headline small") if h1_tag else None
print(wasapp_table)
jetzt = datetime.now()
published_at = jetzt.strftime("%Y-%m-%dT%H:00")

# datensaetze = []
if wasapp_table:
            
    datensatz = {
        "published_at": published_at,
        "title": wasapp_table.get_text(strip=True) if wasapp_table else None,
        "description": "",
        "image_url": "",
        "call_to_action_url": "https://machmit.goslar.de/wasapp#c8489"
    }

    # os.makedirs("ergebnis", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(datensatz, f, ensure_ascii=False, indent=2)

    print(str(jetzt) + " - 019: " + wasapp_table.get_text(strip=True))
    print("✅ 1 Eintrag aus WasApp-Tabelle gespeichert.")
else:
    print("❌ Tabelle auf der WasApp-Seite nicht gefunden.")

