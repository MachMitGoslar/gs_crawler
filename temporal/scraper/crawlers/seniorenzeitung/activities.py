from dataclasses import dataclass
import logging
import os
import re
from lxml import html
from xml.etree import ElementTree as ET
from datetime import datetime

from temporalio import activity, workflow
from dataclasses import dataclass

with workflow.unsafe.imports_passed_through():
    import requests

# Konfiguration
URL = "https://www.goslar.de/leben-in-goslar/senioren/seniorenzeitung"
FILE_PATH = "./output/001_senioren_feed.xml"

def ensure_directory_exists(path: str, permissions: int = 0o755) -> bool:
    if os.path.isdir(path):
        return True
    try:
        os.makedirs(path, mode=permissions, exist_ok=True)
        return True
    except Exception:
        return False


def load_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return html.fromstring(response.content)
    except Exception as e:
        print(f"Fehler beim Laden der Seite: {e}")
        exit(1)


def create_new_feed():
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Seniorenzeitung der Stadt Goslar"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = "RSS Feed der Seniorenzeitung der Stadt Goslar"
    ET.SubElement(channel, "copyright").text = f"Stadt Goslar {datetime.now().year}"
    ET.SubElement(channel, "language").text = "de-DE"
    return rss, channel


def find_existing_links(channel):
    return set(
        (item.find("link").text or "").strip()
        for item in channel.findall("item")
    )

@dataclass
class CrawlerResultItem:
    link: str
    description: str

@dataclass
class CrawlerResult:
    image: None | str
    items: list[CrawlerResultItem]

@activity.defn
async def crawl_senioren() -> CrawlerResult:
    dom = load_html(URL)

    pdf_links = dom.xpath('//a[contains(@href, ".pdf")]')

    items: list[CrawlerResultItem] = []
    image: None | str = None

    for link in pdf_links:
        href = link.get("href")
        if "seniorenzeitung" not in href:
            continue

        full_url = f"https://goslar.de{href}".strip()
        for child in link.iterdescendants():
            class_name = child.get("class", "")
            if "image" in class_name:
                img_tag = child.find(".//img")
                if img_tag is not None and img_tag.get("src"):
                    image = "https://goslar.de" + img_tag.get("src")
            elif "description" in class_name:
                desc = re.sub(r"[^A-Za-z0-9\-äöüÄÖÜß ]", " ", child.text_content())
                items.append(CrawlerResultItem(full_url, desc))

    return CrawlerResult(image, items)

@activity.defn
async def save_senioren(out: CrawlerResult):
    if not ensure_directory_exists(os.path.dirname(FILE_PATH)):
        raise SystemError("could not create output directory")
    
    if os.path.exists(FILE_PATH):
        logging.info("Found existing file at %s" % FILE_PATH)
        tree = ET.parse(FILE_PATH)
        rss = tree.getroot()
        channel = rss.find("channel")
        set_or_create(channel, "lastBuildDate", datetime.now().strftime("%Y-%m-%d %H:%M"))
        image = channel.find("image")
    else:
        logging.info("Could not find file %s" % FILE_PATH)
        rss, channel = create_new_feed()
        image = ET.SubElement(channel, "image")

    if out.image is not None:
        set_or_create(image, "url", out.image)
        set_or_create(image, "title", "Neuste Ausgabe")
        set_or_create(image, "link", URL)

    existing_links = find_existing_links(channel)
    for outItem in out.items:
        if outItem.link in existing_links:
            continue
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "link").text = outItem.link


        ET.SubElement(item, "description").text = outItem.description
        ET.SubElement(item, "pubDate").text = datetime.now().strftime("%Y-%m-%d %H:%M")
        ET.SubElement(item, "title").text = "Eine neue Ausgabe der Seniorenzeitung ist erschienen!"

    tree = ET.ElementTree(rss)
    tree.write(FILE_PATH, encoding="utf-8", xml_declaration=True)

def set_or_create(parent, tag, text):
    node = parent.find(tag)
    if node is None:
        node = ET.SubElement(parent, tag)
    node.text = text
