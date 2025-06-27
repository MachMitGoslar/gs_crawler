import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import json

# Ziel-URL
url = "https://jerstedt.de"

# HTTP-Anfrage senden
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Ergebnisverzeichnis
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Ziel-Container ul#tab-recent-2 und erstes li-Element
ul = soup.find("ul", id="tab-recent-2")
if ul:
    first_li = ul.find("li")
else:
    first_li = None

if first_li:
    # call_to_action_url aus a href
    a_tag = first_li.find("a", href=True)
    call_to_action_url = a_tag["href"] if a_tag else None

    # image_url aus img src
    img_tag = a_tag.find("img") if a_tag else None
    image_url = img_tag["src"] if img_tag else None

    # description aus p.tab-item-title
    desc_tag = first_li.find("p", class_="tab-item-title")
    description = desc_tag.get_text(strip=True) if desc_tag else None

    # published_at aus p.tab-item-date
    date_tag = first_li.find("p", class_="tab-item-date")
    if date_tag:
        date_text = date_tag.get_text(strip=True)
        try:
            dt = datetime.strptime(date_text, "%d. %B %Y")
            published_at = dt.strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            published_at = None
    else:
        published_at = None

    # Daten zusammenstellen
    data = {
        "title": "Stadtteilverein Jerstedt",
        "description": description,
        "call_to_action_url": call_to_action_url,
        "image_url": image_url,
        "published_at": published_at
    }

    # JSON-Datei speichern
    output_path = os.path.join(output_dir, "048_jerstedt.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Beitrag gespeichert unter: {output_path}")
    print(json.dumps(data, ensure_ascii=False, indent=2))
else:
    print("❌ Kein Beitrag im ul#tab-recent-2 gefunden.")
