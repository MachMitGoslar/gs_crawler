import json
import os
import re
import time
from datetime import datetime

import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from matplotlib.patches import Wedge, FancyBboxPatch

# Ziel-URL
base_url = "https://www.harzwasserwerke.de"
url = f"{base_url}/infoservice/aktuelle-talsperrendaten/"
# Die Messwerte lädt die Seite per JavaScript aus diesem Theme-Endpoint nach
barrage_api = f"{base_url}/wp-content/themes/Avada-Child-Theme/barrageData/barrageDataCall.php"
talis_prefix = f"{base_url}/talis/"
# /app/output ist das eigene Ausgabeverzeichnis dieses Crawlers (öffentlich unter /crawler/035_talsperren/)
output_path = "output"
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


def parse_messwert(text):
    """API liefert Zahlen mit Punkt als Dezimaltrenner ('12.91'), fehlend/ungültig -> None"""
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def hole_messwerte(session, quell_url):
    """Aktuelle Messwerte einer Talsperre aus dem TALIS-Textfile (Theme-Endpoint der Seite)."""
    if not quell_url.startswith(talis_prefix):
        raise ValueError(f"unerwartete Quell-URL: {quell_url}")
    resp = session.get(barrage_api, timeout=30, params={
        "m": "getReducedAndSplittedTextData",
        "url": quell_url,
        "dateNow": int(time.time() * 1000),
    })
    resp.raise_for_status()
    return resp.json()


def main():
    session = requests.Session()
    session.headers["User-Agent"] = "Mozilla/5.0 (compatible; gs-crawler/035_talsperren)"

    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    slides = [li for li in soup.find_all("li", class_="slide") if li.find("span", class_="talsperrenname")]
    if not slides:
        print("❌ Keine Talsperren auf der Seite gefunden.")
        raise SystemExit(1)

    resp = session.get(barrage_api, params={"m": "getTsMap"}, timeout=30)
    resp.raise_for_status()
    quellen = resp.json()

    jetzt = datetime.now().strftime("%Y-%m-%dT%H:%M")
    talsperren = []

    for li in slides:
        name = li.find("span", class_="talsperrenname").get_text(strip=True)
        max_tag = li.find("strong", class_="data_stauhoehe")
        maximum = parse_zahl(max_tag.get_text()) if max_tag else None

        try:
            messwerte = hole_messwerte(session, quellen[name])
        except (KeyError, ValueError, requests.RequestException) as e:
            print(f"❌ {name}: Messwerte nicht abrufbar ({e}). Abbruch ohne Überschreiben.")
            raise SystemExit(1)

        inhalt = parse_messwert(messwerte.get("stauinhalt"))
        if not maximum or inhalt is None:
            print(f"❌ {name}: keine gültigen Daten. Abbruch ohne Überschreiben.")
            raise SystemExit(1)

        # Darstellung wie auf der Seite: "26.10.2026 – 21:00:00 Uhr"
        datum = messwerte["datum"].replace(" ", " – ", 1) + " Uhr" if messwerte.get("datum") else ""
        zufluss = parse_messwert(messwerte.get("zufluss"))
        uwabgabe = parse_messwert(messwerte.get("abgabe"))

        # Direkter Link auf die TALIS-Detailseite der einzelnen Talsperre
        link_tag = li.find("a", id="zurTalsperre")
        talsperre_url = base_url + link_tag["href"] if link_tag and link_tag.get("href") else url
        talis_url = f"{base_url}/infoservice/talis-talsperrendaten/talis-daten-{slugify(name)}talsperre/"

        talsperren.append({
            "name": name, "maximum": maximum, "inhalt": inhalt, "datum": datum,
            "prozent": inhalt / maximum * 100, "zufluss": zufluss, "uwabgabe": uwabgabe,
            "url": talis_url, "info_url": talsperre_url,
        })

    # Gesamt-Messzeitpunkt (erste Talsperre)
    messzeitpunkt = talsperren[0]["datum"] or "Messzeitpunkt unbekannt"

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


main()
