from dataclasses import dataclass
import logging
import os
import re
from datetime import datetime

from temporalio import activity, workflow
from dataclasses import dataclass
from bs4 import BeautifulSoup
import random
import json
from datetime import datetime
import re
import os

with workflow.unsafe.imports_passed_through():
    import requests

CRAWLER_URL = "https://kunst-in-ar.de/crawler.html"
BASE_URL = "https://kunst-in-ar.de"
FILE_PATH = "./output/017-kunst-in-ar-single.json"

@dataclass
class CrawlerResultItem:
    link: str
    description: str

@dataclass
class Artist:
    name: str
    images: list[str]

@dataclass
class ArtistDetails:
    description: str
    image_url: str
    cta_url: str


@activity.defn
async def crawl_artists() -> list[Artist]:
    response = requests.get(CRAWLER_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    headers = [th.get_text(strip=True) for th in table.find_all("th")]

    artists: list[Artist] = []

    for tr in table.find_all("tr")[1:]:  # skip first (header) row
        tds = tr.find_all("td")
        if len(tds) >= len(headers):
            daten = {headers[i]: tds[i].get_text(strip=True) for i in range(len(headers))}
            
            name = daten.get("Name", "").strip()
            images = [daten.get(f"Bild{i}", "").strip() for i in range(1, 5)]
            images = [b for b in images if b.startswith("http")]  # only keep valid urls

            if name and images:
                artists.append(Artist(name=name, images=images))

    return artists

@activity.defn
async def crawl_artist(artist: Artist) -> ArtistDetails:
    name = artist.name
    image_url = random.choice(artist.images)

    name = name.lower()
    name = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    parts = re.findall(r"\w+", name)
    cta_url = f"{BASE_URL}/{"-".join(parts)}"

    about_me = ""
    try:
        detail_response = requests.get(cta_url)
        activity.logger.debug(f"CTA URL: {cta_url}")
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        # Anker finden
        about_me_anchor = detail_soup.find("a", href="#ueber-mich")
        activity.logger.debug(f"about me anchor: {about_me_anchor}")
        if about_me_anchor:
            wrapper = about_me_anchor.find_next("div", class_="wpb_wrapper")
            if wrapper:
                p_tag = wrapper.find("p")
                if p_tag:
                    about_me = p_tag.get_text(strip=True)
    except Exception as e:
        about_me = ""

    return ArtistDetails(
        description=f"Über {name}<br>: {about_me[:100]}…" if about_me else f"{name}: Keine Beschreibung gefunden.",
        image_url=image_url,
        cta_url=cta_url
    )

@activity.defn
async def save_artist(artist_details: ArtistDetails):
    if not ensure_directory_exists(os.path.dirname(FILE_PATH)):
        raise SystemError("could not create output directory")
    output = {
        "title": "Kunst in AR",
        "description": artist_details.description,
        "image_url": artist_details.image_url,
        "call_to_action_url": artist_details.image_url,
        "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
    }

    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    activity.logger.info(f"✅ Künstlerdaten gespeichert in '{FILE_PATH}'")
    activity.logger.debug(json.dumps(output, ensure_ascii=False, indent=2))


def ensure_directory_exists(path: str, permissions: int = 0o755) -> bool:
    if os.path.isdir(path):
        return True
    try:
        os.makedirs(path, mode=permissions, exist_ok=True)
        return True
    except Exception:
        return False
