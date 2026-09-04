import json
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

if Path("/app/output").exists():
    OUTPUT_DIR = Path("/app/output/046_bio_stadt_goslar")
else:
    OUTPUT_DIR = REPO_ROOT / "httpdocs" / "crawler" / "046_bio_stadt_goslar"

CARD_FILE = "046_bio_stadt_goslar_card.json"
ALLE_FILE = "046_bio_stadt_goslar_alle.json"
STANDORTE_FILE = "046_bio_stadt_goslar_standorte.json"
INDEX_HTML_FILE = "046_bio_stadt_goslar_index.html"
DETAIL_HTML_FILE = "046_bio_stadt_goslar_detail.html"
UI_KIT_FILES = ["goslar-ui.css", "goslar-ui.js"]

# JSON-Routing wie bei 070_wochenmarkt: card.json verlinkt auf alle.json,
# jeder Einkaufsführer-Eintrag in alle.json verlinkt auf eine eigene
# Detail-JSON-Datei (statt auf die HTML-Seiten unten).
BASE_URL = "https://crawler.goslar.app/crawler/046_bio_stadt_goslar"

# HTML-Index/Detail bleiben vorerst in der Hinterhand: werden weiterhin
# gebaut und aktuell gehalten, aber (noch) nicht verlinkt.
INDEX_HTML_URL = f"{BASE_URL}/{INDEX_HTML_FILE}"

SOURCE_URL = (
    "https://www.goslar.de/wirtschafts-und-zukunftsort/"
    "klima-umwelt-gewaesserschutz/umweltschutz/biostadt-goslar"
)

# Die 4 Unterseiten der Biostadt-Goslar-Seite: nur Teaser + Link raus,
# kein eigenes Detailelement (siehe Absprache).
ARTICLE_SLUGS = [
    "warum-bio",
    "wie-erkenne-ich-bio",
    "warum-sind-bio-lebensmittel-teurer",
    "veranstaltungen",
]

# Der auf der Seite verlinkte PDF-Bio-Einkaufsführer basiert auf dieser
# ArcGIS-Karte ("Bio Einkaufsführer"). Der FeatureServer ist öffentlich
# abfragbar und liefert strukturierte Daten statt PDF-Parsing.
ARCGIS_QUERY_URL = (
    "https://services3.arcgis.com/X0EQlGp2g40JN62M/arcgis/rest/services/"
    "Bio_Einkaufsführer_WFL1/FeatureServer/0/query"
)

REQUEST_HEADERS = {"User-Agent": "gs_crawler-046-bio_stadt_goslar/1.0 (+https://goslar-app.de)"}

TEASER_MAX_LENGTH = 260


def fetch_soup(url):
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def truncate_teaser(text):
    text = " ".join(text.split())
    if len(text) <= TEASER_MAX_LENGTH:
        return text
    cut = text[:TEASER_MAX_LENGTH].rsplit(" ", 1)[0]
    return cut.rstrip(",.;:") + "…"


def first_content_paragraph(main):
    for p in main.find_all("p"):
        text = " ".join(p.get_text(strip=True).split())
        if len(text) > 40:
            return text
    return ""


def first_content_image(main, page_url):
    img = main.find("img")
    if img and img.get("src"):
        return urljoin(page_url, img["src"])
    return None


def scrape_hub():
    """Haupt-Seite Biostadt Goslar: Intro-Text + Banner-Bild."""
    soup = fetch_soup(SOURCE_URL)
    main = soup.find("main") or soup
    intro = first_content_paragraph(main)
    image_url = first_content_image(main, SOURCE_URL)
    return intro, image_url


def scrape_articles():
    """Die 4 Unterseiten als kurze Teaser-Kacheln mit Link zur Originalseite."""
    articles = []
    for index, slug in enumerate(ARTICLE_SLUGS, start=1):
        url = f"{SOURCE_URL}/{slug}"
        try:
            soup = fetch_soup(url)
        except requests.RequestException as exc:
            print(f"⚠️  Unterseite nicht erreichbar ({url}): {exc}")
            continue

        main = soup.find("main") or soup
        title = soup.title.get_text(strip=True) if soup.title else slug
        teaser = truncate_teaser(first_content_paragraph(main))
        image_url = first_content_image(main, url)

        articles.append(
            {
                "id": index,
                "slug": slug,
                "title": title,
                "teaser": teaser,
                "image_url": image_url,
                "call_to_action_url": url,
            }
        )
    return articles


def fetch_einkaufsfuehrer():
    """Bio-Einkaufsführer: Standorte aus der öffentlichen ArcGIS-Karte."""
    response = requests.get(
        ARCGIS_QUERY_URL,
        headers=REQUEST_HEADERS,
        params={"where": "1=1", "outFields": "*", "returnGeometry": "false", "f": "json"},
        timeout=20,
    )
    response.raise_for_status()
    features = response.json().get("features", [])

    items = []
    for feature in features:
        attrs = feature.get("attributes", {})
        name = (attrs.get("Name") or "").strip()
        if not name:
            continue

        category = (attrs.get("Kategorie") or "").strip()
        address = (attrs.get("Adresse") or "").strip() or None
        opening_hours = (attrs.get("Öffnungszeiten") or "").strip() or None
        website = (attrs.get("Website") or "").strip() or None
        image_url = (attrs.get("Foto") or "").strip() or None

        item_id = int(attrs.get("ID") or attrs.get("OBJECTID"))
        description = " · ".join(part for part in [category, address] if part)

        items.append(
            {
                "id": item_id,
                "title": name,
                "category": category or None,
                "address": address,
                "opening_hours": opening_hours,
                "website": website,
                "image_url": image_url,
                "description": description,
                # Für die HTML-Reserve-Ansicht (?id=...), siehe write_html().
                "call_to_action_url": f"{DETAIL_HTML_FILE}?id={item_id}",
            }
        )

    items.sort(key=lambda item: item["title"].lower())
    return items


def shop_detail_filename(item_id):
    return f"046_bio_stadt_goslar_{item_id}.json"


def build_top_index_entries(articles, shop_count, banner_image_url, published_at):
    """Flache Liste für alle.json: Artikel-Teaser (Link raus) + eine Kachel
    'Bio-Einkaufsführer', die auf die eigene Standorte-Index-Datei verlinkt."""
    entries = []

    for article in articles:
        entries.append(
            {
                "id": f"artikel-{article['slug']}",
                "title": article["title"],
                "description": article["teaser"],
                "image_url": article["image_url"],
                "call_to_action_url": article["call_to_action_url"],
                "published_at": published_at,
            }
        )

    entries.append(
        {
            "id": "einkaufsfuehrer",
            "title": "Bio-Einkaufsführer",
            "description": f"{shop_count} Orte in und um Goslar, an denen Sie Bio-Lebensmittel kaufen können.",
            "image_url": banner_image_url,
            "call_to_action_url": "https://goslar.maps.arcgis.com/apps/instant/sidebar/index.html?appid=17912453a9f34f748f28252602e41d15&center=10.4386;51.915&level=10",
            # Preparation for Stacked Index View
            # "call_to_action_url": f"{BASE_URL}/{STANDORTE_FILE}",
            "published_at": published_at,
        }
    )

    return entries


def build_standorte_index(shops, published_at):
    """Eigene Index-Datei nur für die Bio-Einkaufsführer-Standorte, jeweils
    mit Link auf ihre eigene Detail-JSON-Datei — Routing wie bei 070_wochenmarkt."""
    return [
        {
            "id": shop["id"],
            "title": shop["title"],
            "description": shop["description"],
            "image_url": shop["image_url"],
            "call_to_action_url": f"{BASE_URL}/{shop_detail_filename(shop['id'])}",
            "published_at": published_at,
        }
        for shop in shops
    ]


def build_shop_detail(shop, published_at):
    parts = [
        f"<p>{shop['title']} ist Teil des Bio-Einkaufsführers Goslar"
        + (f" ({shop['category']})" if shop["category"] else "")
        + ".</p>"
    ]
    if shop["address"]:
        parts.append(f"<p>Adresse: {shop['address']}</p>")
    if shop["opening_hours"]:
        parts.append(f"<p>Öffnungszeiten: {shop['opening_hours']}</p>")

    images = [{"url": shop["image_url"]}] if shop["image_url"] else []

    return {
        "id": shop["id"],
        "title": shop["title"],
        "summary": shop["description"],
        "description": "".join(parts),
        "images": images,
        "call_to_action_url": shop["website"],
        "published_at": published_at,
    }


def cleanup_shop_detail_files(current_ids):
    """Entfernt Detail-JSON-Dateien von Orten, die nicht mehr im aktuellen
    Einkaufsführer-Lauf vorkommen (Standorte können sich ändern)."""
    if not OUTPUT_DIR.is_dir():
        return

    keep_filenames = {CARD_FILE, ALLE_FILE, STANDORTE_FILE, INDEX_HTML_FILE, DETAIL_HTML_FILE}
    current_filenames = {shop_detail_filename(item_id) for item_id in current_ids}

    for path in OUTPUT_DIR.glob("046_bio_stadt_goslar_*.json"):
        if path.name in keep_filenames or path.name in current_filenames:
            continue
        path.unlink()
        print(f"Removed stale file: {path}")


def build_html_bundle(intro, banner_image_url, articles, shops, shop_count, published_at):
    """Datenstruktur für die HTML-Reserve-Ansicht (Index+Detail mit UI-Kit)."""
    map_text = (
        f"Aktuell listet der Bio-Einkaufsführer {shop_count} Orte in und um Goslar, "
        "an denen Sie Bio-Lebensmittel kaufen können."
    )
    return {
        "title": "Biostadt Goslar",
        "intro": intro,
        "image_url": banner_image_url,
        "source_url": SOURCE_URL,
        "artikel": articles,
        "einkaufsfuehrer": {
            "count": shop_count,
            "map_text": map_text,
            "items": shops,
        },
        "published_at": published_at,
    }


def json_for_script(data):
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace('\u2028', "\\u2028")
        .replace('\u2029', "\\u2029")
    )


def write_json(filename, payload):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Written: {path}")


def write_html(filename, data):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    html = (SCRIPT_DIR / filename).read_text(encoding="utf-8")
    html = html.replace("__BIOSTADT_JSON__", json_for_script(data))
    target = OUTPUT_DIR / filename
    target.write_text(html, encoding="utf-8")
    print(f"Written: {target}")


def resolve_ui_kit_dir():
    image_ui_kit_dir = Path("/app/ui-kit")
    if image_ui_kit_dir.exists():
        return image_ui_kit_dir
    return REPO_ROOT / "base_images" / "python_basic_crawler"


def copy_ui_kit():
    target_dir = OUTPUT_DIR / "ui-kit"
    target_dir.mkdir(parents=True, exist_ok=True)
    source_dir = resolve_ui_kit_dir()
    for filename in UI_KIT_FILES:
        target = target_dir / filename
        shutil.copyfile(source_dir / filename, target)
        print(f"Copied: {target}")


def main():
    intro, banner_image_url = scrape_hub()
    articles = scrape_articles()
    shops = fetch_einkaufsfuehrer()

    if not shops:
        print("ArcGIS-Feature-Service lieferte keine Einkaufsführer-Einträge. Breche ab, ohne Output zu überschreiben.")
        return

    shop_count = len(shops)
    published_at = datetime.now().strftime("%Y-%m-%dT%H:%M")

    # ── JSON-Routing (wie 070_wochenmarkt) ──────────────────────────────────
    card = {
        "title": "Biostadt Goslar",
        "description": f"Bio-Einkaufsführer mit aktuell {shop_count} Orten sowie Infos rund um Bio in Goslar.",
        "image_url": banner_image_url,
        "call_to_action_url": f"{BASE_URL}/{ALLE_FILE}",
        "published_at": published_at,
    }
    write_json(CARD_FILE, card)
    write_json(ALLE_FILE, build_top_index_entries(articles, shop_count, banner_image_url, published_at))
    write_json(STANDORTE_FILE, build_standorte_index(shops, published_at))

    for shop in shops:
        write_json(shop_detail_filename(shop["id"]), build_shop_detail(shop, published_at))
    cleanup_shop_detail_files([shop["id"] for shop in shops])

    # ── UI-Strategie in der Hinterhand (nicht verlinkt, aber aktuell) ───────
    html_bundle = build_html_bundle(intro, banner_image_url, articles, shops, shop_count, published_at)
    write_html(INDEX_HTML_FILE, html_bundle)
    write_html(DETAIL_HTML_FILE, html_bundle)
    copy_ui_kit()


if __name__ == "__main__":
    main()
