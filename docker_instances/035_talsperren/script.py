from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge, FancyBboxPatch
import os
import re

# Setup (optional: Headless-Modus aktivieren)
options = Options()
options.add_argument("--headless")
service = FirefoxService(GeckoDriverManager().install())
driver = webdriver.Firefox(options=options, service=service, )

# Ziel-URL
base_url = "https://www.harzwasserwerke.de"
url = f"{base_url}/infoservice/aktuelle-talsperrendaten/"
output_path = "output/035_talsperren"
export_jsonfile = "035-talsperren_alle.json"
export_indexfile = "035-talsperren_index.json"
image_base = "https://crawler.goslar.app/crawler/035_talsperren"

os.makedirs(output_path, exist_ok=True)


def parse_zahl(text):
    """'1.234,5' / '13,27' -> float, '-' -> None"""
    text = (text or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def fmt(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def farbe_fuer(prozent):
    """Ampelfarben, gedeckt: niedrig = Rot, mittel = Amber, hoch = Blau/Grün-Teal."""
    if prozent < 30:
        return "#ff6b6b"
    if prozent < 60:
        return "#ffb84d"
    return "#3ddc97"


def slugify(name):
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        name = name.lower().replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-")


def draw_gauge(prozent, titel, untertitel, dateiname):
    """Ring-Gauge auf dunkler Karte: weiße Schrift auf Navy -> durchgehend hoher Kontrast."""
    bg, track, text_main, text_sub = "#0f2a43", "#27465f", "#ffffff", "#c9d8e6"

    fig = plt.figure(figsize=(3, 3), dpi=200)
    fig.patch.set_alpha(0)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.add_patch(FancyBboxPatch((0.02, 0.02), 0.96, 0.96,
                                boxstyle="round,pad=0,rounding_size=0.08",
                                facecolor=bg, edgecolor="none"))

    cx, cy, r, w = 0.5, 0.56, 0.31, 0.075
    ax.add_patch(Wedge((cx, cy), r, 0, 360, width=w, facecolor=track, edgecolor="none"))
    anteil = min(max(prozent, 0), 100) / 100
    if anteil > 0:
        ax.add_patch(Wedge((cx, cy), r, 90 - 360 * anteil, 90, width=w,
                           facecolor=farbe_fuer(prozent), edgecolor="none"))

    ax.text(cx, cy + 0.02, f"{fmt(prozent)}%", ha="center", va="center",
            fontsize=24 if prozent >= 99.95 else 27, fontweight="bold", color=text_main)
    ax.text(cx, cy - 0.11, "gefüllt", ha="center", va="center", fontsize=9, color=text_sub)
    ax.text(cx, 0.19, titel, ha="center", va="center", fontsize=12, fontweight="bold", color=text_main)
    ax.text(cx, 0.105, untertitel, ha="center", va="center", fontsize=8.5, color=text_sub)

    fig.savefig(os.path.join(output_path, dateiname), dpi=200, transparent=True)
    plt.close(fig)


try:
    driver.get(url)
    time.sleep(5)  # Warten auf JS-Inhalte
    soup = BeautifulSoup(driver.page_source, "html.parser")

    result_div = soup.find("div", class_="slick-track")
    if not result_div:
        print("❌ slick-track nicht gefunden.")
        driver.quit()
        exit()

    # Gesamt-Messzeitpunkt (Fallback für Talsperren ohne eigenes Datum)
    datum_tags = [t.get_text(strip=True) for t in soup.find_all("span", class_="datum")]
    datum_tags = [d for d in datum_tags if d and d != "-"]
    messzeitpunkt = datum_tags[0] if datum_tags else "Messzeitpunkt unbekannt"

    jetzt = datetime.now().strftime("%Y-%m-%dT%H:%M")
    talsperren = []

    for li in result_div.find_all("li", class_="slide"):
        name_tag = li.find("span", class_="talsperrenname")
        max_tag = li.find("strong", class_="data_stauhoehe")
        inhalt_tag = li.find("strong", class_="data_stauinhalt")
        if not (name_tag and max_tag and inhalt_tag):
            continue

        name = name_tag.get_text(strip=True)
        maximum = parse_zahl(max_tag.get_text())
        inhalt = parse_zahl(inhalt_tag.get_text())
        if not maximum or inhalt is None:
            print(f"⚠️ {name}: keine gültigen Daten, übersprungen.")
            continue

        datum_tag = li.find("span", class_="datum")
        datum = datum_tag.get_text(strip=True) if datum_tag else ""
        datum = datum if datum and datum != "-" else messzeitpunkt
        zufluss = parse_zahl(li.find("strong", class_="data_zufluss").get_text()) if li.find("strong", class_="data_zufluss") else None
        uwabgabe = parse_zahl(li.find("strong", class_="data_uwabgabe").get_text()) if li.find("strong", class_="data_uwabgabe") else None

        # Direkter Link auf die TALIS-Detailseite der einzelnen Talsperre
        link_tag = li.find("a", id="zurTalsperre")
        talsperre_url = base_url + link_tag["href"] if link_tag and link_tag.get("href") else url
        talis_url = f"{base_url}/infoservice/talis-talsperrendaten/talis-daten-{slugify(name)}talsperre/"

        talsperren.append({
            "name": name, "maximum": maximum, "inhalt": inhalt, "datum": datum,
            "prozent": inhalt / maximum * 100, "zufluss": zufluss, "uwabgabe": uwabgabe,
            "url": talis_url, "info_url": talsperre_url,
        })

    if not talsperren:
        print("❌ Keine gültigen Füllstandsdaten gefunden. Abbruch ohne Überschreiben.")
        raise SystemExit(1)

    # Gesamtfüllstand aller Talsperren (Frontansicht / Karte)
    summe_max = sum(t["maximum"] for t in talsperren)
    summe_inhalt = sum(t["inhalt"] for t in talsperren)
    fuellstand_prozent = summe_inhalt / summe_max * 100
    description = "Summe der Füllstände aller Talsperren der Harzwasserwerke in Prozent"

    draw_gauge(fuellstand_prozent, "Talsperren Harz", messzeitpunkt, "fuellstand_prozent.png")

    # Index-JSON: eine Kachel je Talsperre mit Deeplink
    index = []
    for i, t in enumerate(talsperren, start=1):
        bild = f"fuellstand_{slugify(t['name'])}.png"
        draw_gauge(t["prozent"], f"{t['name']}talsperre", t["datum"], bild)
        teile = [f"Füllstand {fmt(t['prozent'])} % ({fmt(t['inhalt'], 2)} von {fmt(t['maximum'], 2)} Mio. m³)"]
        if t["zufluss"] is not None:
            teile.append(f"Zufluss {fmt(t['zufluss'], 2)} m³/s")
        if t["uwabgabe"] is not None:
            teile.append(f"Unterwasserabgabe {fmt(t['uwabgabe'], 2)} m³/s")
        index.append({
            "id": i,
            "title": f"{t['name']}talsperre",
            "description": f"{t['datum']}: " + ", ".join(teile),
            "image_url": f"{image_base}/{bild}",
            "call_to_action_url": t["url"],
            "published_at": jetzt,
        })

    # Fügt eine Kachel mit Herkunft der Daten und Haftung hinzu
    index.append({
        "id": len(index) + 1,
        "title": "Datenquelle und Haftung",
        "description": "Die Füllstandsdaten stammen von den Harzwasserwerken. Es wird keine Haftung für die Richtigkeit der Daten übernommen.",
        "image_url": f"{image_base}/fuellstand_prozent.png",
        "call_to_action_url": f"{url}",
        "published_at": jetzt,
    })

    with open(os.path.join(output_path, export_indexfile), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    # Karten-JSON (Gesamtfüllstand)
    daten = {
        "title": "Talsperren",
        "description": f"{messzeitpunkt}: {description}",
        "image_url": f"{image_base}/fuellstand_prozent.png",
        "call_to_action_url": f"{image_base}/{export_indexfile}",
        "published_at": jetzt,
    }

    with open(os.path.join(output_path, export_jsonfile), "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

    print("✅ JSON erfolgreich erstellt:")
    print(json.dumps(daten, ensure_ascii=False, indent=2))
    print(json.dumps(index, ensure_ascii=False, indent=2))

finally:
    driver.quit()
