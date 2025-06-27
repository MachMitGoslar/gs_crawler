import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
from helpers import ensure_directory_exists

url = "https://immenro.de/"
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "output", "041_immenrode.json")
ensure_directory_exists(output_path)


response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

section = soup.find("section", {"id": "content"})

call_to_action_url = image_url = published_at = title = description = None

if section:
    a_tag = section.find("a", href=True)
    if a_tag:
        call_to_action_url = a_tag["href"]

    img_tag = section.find("img")
    if img_tag and img_tag.has_attr("src"):
        image_url = img_tag["src"]

    time_tag = section.find("time", {"datetime": True})
    if time_tag:
        try:
            dt = datetime.fromisoformat(time_tag["datetime"])
            published_at = dt.strftime("%Y-%m-%dT%H:%M")
        except ValueError:
            published_at = time_tag["datetime"]

    featured_div = section.find("div", class_="featured")
    if featured_div:
        h2_tag = featured_div.find("h2", class_="post-title entry-title")
        if h2_tag:
            title = h2_tag.get_text(strip=True)

        next_div = featured_div.find("div", class_="entry excerpt entry-summary")
        print(next_div)
        if next_div:
            p_tag = next_div.find("p")
            if p_tag:
                description = p_tag.get_text(strip=True)

# Ergebnis anzeigen
daten = {
    "call_to_action_url": call_to_action_url,
    "image_url": image_url,
    "published_at": published_at,
    "title": title,
    "description": description
}

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(daten, f, ensure_ascii=False, indent=2)

print(json.dumps(daten, ensure_ascii=False, indent=2))
