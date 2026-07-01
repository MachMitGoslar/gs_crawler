import json
import os
import shutil
from datetime import datetime

IMAGE_URL = "https://crawler.goslar.app/crawler/056_serviceportal_image.png"
EXPORT_JSON_FILE = "056-serviceportal.json"
EXPORT_HTML_FILES = ["056_serviceportal_index.html", "056_serviceportal_termin.html"]
EXPORT_ASSET_FILES = ["056_serviceportal_image.png"]
INDEX_HTML_URL = "https://crawler.goslar.app/crawler/056_serviceportal_index.html"

entry = {
    "title": "Online-Dienstleistungen der Stadt Goslar",
    "description": "Termine buchen, Anträge stellen und weitere Online Dienstleistungen - probier uns aus!",
    "image_url": IMAGE_URL,
    "call_to_action_url": INDEX_HTML_URL,
    "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
}

print("Erfolgreich gespeichert:", entry["title"])
