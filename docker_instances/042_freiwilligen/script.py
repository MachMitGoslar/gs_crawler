import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import random

URL_RAW = "https://www.lachnit-software.de/query/iframe/"
BASE_URL = "https://www.lachnit-software.de/query/iframe/input-output.php"
URL_FWG = "https://www.freiwilligenagentur-goslar.de/index.php/fuer-freiwillige/angebote-fuer-freiwillige"
PARAMS = {
    "match_what[zielgruppen_p0]": "",
    "match_what[kenntnisse_p0]": "",
    "hideund": "1",
    "suchen": "",
    "submit": "Suchen",
    "agid": "25",
    "styleid": "2",
    "frametyp": "3",
    "do": "go",
    "apiKey": "",
    "page": 1
}

def extract_entries_from_page(soup, now):
    results = []
    for block in soup.find_all("div", class_="kopf_content_typ_1"):
        title_tag = block.find(class_="titel")
        desc_tag = block.find("div", class_="kurz")
        link_tag = block.find("a", href=True)
        if title_tag:
            results.append({
                "title": "Angebot " + title_tag.get_text(strip=True).split(".", 1)[0] + "\n" + title_tag.get_text(strip=True).split(".", 1)[1],
                "description": desc_tag.get_text(strip=True) if desc_tag else "",
                # "call_to_action_url": URL_FWG,
                "call_to_action_url": URL_RAW + link_tag["href"] if link_tag else "",
                "published_at": now
            })
    return results

def scrape_all_pages():
    all_entries = []
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    session = requests.Session()

    page = 1
    while True:
        PARAMS["page"] = page
        response = session.get(BASE_URL, params=PARAMS)
        soup = BeautifulSoup(response.text, "html.parser")

        entries = extract_entries_from_page(soup, now)
        if not entries:
            break

        all_entries.extend(entries)
        page += 1

    return all_entries

def save_results(entries):
    os.makedirs("output", exist_ok=True)
    all_path = "output/042-freiwilligenagentur-alle.json"
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    if entries:
        zufall = random.choice(entries)
        single_path = "output/042-freiwilligenagentur.json"
        with open(single_path, "w", encoding="utf-8") as f:
            json.dump(zufall, f, ensure_ascii=False, indent=2)
        print("✅ Zufallsdatensatz gespeichert.")
    print(f"✅ {len(entries)} Einträge gesamt gespeichert.")

if __name__ == "__main__":
    eintraege = scrape_all_pages()
    save_results(eintraege)
