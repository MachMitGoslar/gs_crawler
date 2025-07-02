import requests
from bs4 import BeautifulSoup
import random
import json
from datetime import datetime
from urllib.parse import urljoin
import re
import os

# URLs
crawler_url = "https://kunst-in-ar.de/crawler.html"
base_url = "https://kunst-in-ar.de"
save_jsonfile = "017-kunst-in-ar-single.json"

# 1. HTML laden
response = requests.get(crawler_url)
soup = BeautifulSoup(response.text, "html.parser")

# Speicherpfad
output_dir = "output/"
os.makedirs(output_dir, exist_ok=True)

# Tabelle und Kopfzeile einlesen
table = soup.find("table")
headers = [th.get_text(strip=True) for th in table.find_all("th")]

kuenstler_liste = []

# 2. Künstler-Daten aus Zeilen extrahieren
for tr in table.find_all("tr")[1:]:  # Kopfzeile überspringen
    tds = tr.find_all("td")
    if len(tds) >= len(headers):
        daten = {headers[i]: tds[i].get_text(strip=True) for i in range(len(headers))}
        
        name = daten.get("Name", "").strip()
        bilder = [daten.get(f"Bild{i}", "").strip() for i in range(1, 5)]
        bilder = [b for b in bilder if b.startswith("http")]  # Nur gültige URLs behalten

        if name and bilder:
            kuenstler_liste.append({
                "name": name,
                "bilder": bilder
            })

# 3. Zufälliger Künstler
if kuenstler_liste:
    auswahl = random.choice(kuenstler_liste)
    name = auswahl["name"]
    bild = random.choice(auswahl["bilder"])

    # 4. Künstler-URL generieren
    def name_to_slug(n):
        n = n.lower()
        n = n.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        parts = re.findall(r"\w+", n)
        return "-".join(parts)

    slug = name_to_slug(name)
    kuenstler_url = f"{base_url}/{slug}"

    # 5. Künstlerseite laden und "Über mich" extrahieren
    ueber_mich = ""
    try:
        detail_response = requests.get(kuenstler_url)
        print(kuenstler_url)
        detail_soup = BeautifulSoup(detail_response.text, "html.parser")

        # Anker finden
        ueber_anchor = detail_soup.find("a", href="#ueber-mich")
        print(ueber_anchor)
        if ueber_anchor:
            wrapper = ueber_anchor.find_next("div", class_="wpb_wrapper")
            if wrapper:
                p_tag = wrapper.find("p")
                if p_tag:
                    ueber_mich = p_tag.get_text(strip=True)
    except Exception as e:
        ueber_mich = ""

    # 6. Beschreibung kürzen
    beschreibung = f"Über {name}<br>: {ueber_mich[:100]}…" if ueber_mich else f"{name}: Keine Beschreibung gefunden."

    # 7. JSON zusammenbauen
    output = {
        "title": "Kunst in AR",
        "description": beschreibung,
        "image_url": bild,
        "call_to_action_url": kuenstler_url,
        "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
    }

    # 8. JSON speichern & ausgeben
    with open(os.path.join(output_dir, save_jsonfile), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ Künstlerdaten gespeichert in '{save_jsonfile}'")
    print(json.dumps(output, ensure_ascii=False, indent=2))
else:
    print("❌ Keine Künstler gefunden")
