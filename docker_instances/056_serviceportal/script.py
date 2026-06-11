import json
import os
import shutil
from datetime import datetime

IMAGE_URL = "https://crawler.goslar.app/senioren/jsonapp/023-serviceportal.png"
OUTPUT_DIR = "output/"
EXPORT_JSON_FILE = "056-serviceportal.json"
EXPORT_HTML_FILES = ["056_serviceportal_index.html", "056_serviceportal_termin.html"]
INDEX_HTML_URL = "https://crawler.goslar.app/crawler/056_serviceportal_index.html"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for html_file in EXPORT_HTML_FILES:
    if os.path.exists(html_file):
        shutil.copyfile(html_file, os.path.join(OUTPUT_DIR, html_file))

entry = {
    "title": "Online-Dienstleistungen der Stadt Goslar",
    "description": "Termine buchen, Anträge stellen und weitere Online Dienstleistungen - probier uns aus!",
    "image_url": IMAGE_URL,
    "call_to_action_url": INDEX_HTML_URL,
    "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
}

with open(os.path.join(OUTPUT_DIR, EXPORT_JSON_FILE), "w", encoding="utf-8") as json_file:
    json.dump(entry, json_file, ensure_ascii=False, indent=2)

print("Erfolgreich gespeichert:", entry["title"])
