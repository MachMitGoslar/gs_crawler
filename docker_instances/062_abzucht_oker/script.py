# $Id: Abzucht-Pegel.py
# Author: Luksch, Klaus-J <klaus.luksch@icloud.com> für Goslar App
# Copyright: ( c )  2025.
#
# Abzucht-Pegel
# =============
#
#
# Allgemeine Programmdokumentation und Info
# -----------------------------------------
#
#    Programm:
#    ---------
#                      Liest aus der offiziellen Website des Niedersächsischen
#                      Landesbetriebs für Wasserwirtschaft, Küsten- und Naturschutz
#                      aktuelle Pegelstände des für Goslar relevanten
#                      Pegels der Abzucht (Gose) "Oker".
#
#    Version:  1.0
#    -------------
#                      2025-09-03
#
#
#   Version history:
#    ---------------
#                      1.0: Initiales Release
#
#
#    Author:
#    ------
#                      Luksch, Klaus-J
#
#
#    License:
#    -------
#                      Opensource / Freeware
#
#
#
#    Arguments/Parameter:
#    -------------------
#                      keine
#
#
#    Zusätzl. Info:
#    --------------
#
#                      Die Webseite meldet keine "offiziellen" Meldestufen und Warnstufen.
#                      Die sind die "inoffiziellen" Meldestufen, die im Programm gesetzt
#                      werden.
#                      Meldestufe 1: 360 cm / NN + 59,59 m
#                      Meldestufe 2: 440 cm / NN + 60,39 m
#                      Meldestufe 3: 480 cm / NN + 60,79 m
#
#
#    Description:
#    -----------
#
#            Das Programm kann über cron zyklisch gestartet werden
#
#
#
#
#    Bekannte Probleme:
#    ------------------
#
#            Derzeit keine bekannt.
#
############################################################################################
#
# Libraries
import os
import re
import sys
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

# Optional: Pfade für Datei-Outputs (wenn gewünscht)
OUTPUT_FILE = None  # z. B. "../Hochwasser.txt"

# Logging (auskommentieren / anpassen wenn nicht gewünscht)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

# Ziel-URL
# URL der Quelle
URL = "https://www.pegelonline.nlwkn.niedersachsen.de/Messwerte"
imageurl = "./output/062-Hochwasser.png"

# Ausgabeordner
output_dir = "output/"
os.makedirs(output_dir, exist_ok=True)

try:
# --- Hilfsfunktionen ---
    def parse_number(text: str) -> Optional[float]:
        """Finde die erste Zahl (mit optionalem Komma/Punkt) und gib int oder float zurück."""
        if not text:
            return None
        m = re.search(r'[-+]?\d+[.,]?\d*', text)
        if not m:
            return None
        s = m.group(0).replace(',', '.')
        return float(s) if '.' in s else int(s)

    def fetch_soup(url: str, timeout: int = 10) -> BeautifulSoup:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; AbzuchtPegel/1.0; +https://example.org/)"
        }
        # logging.info("Hole URL: %s", url)
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def find_abzucht_row(soup: BeautifulSoup):
        """Finde die TR-Zeile, in der Spalte 1 'Abzucht' steht."""
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 9 and tds[1].get_text(strip=True).lower() == "abzucht":
                return tds
        return None

    def parse_row(tds) -> Tuple[dict, bool]:
        """Parsen der bekannten Indizes (wie in deinem Beispiel der Webseite)."""
        # Indices nach Beispiel:
        # 0: Station (Oker)
        # 1: Bezeichnung (Abzucht)
        # 2: Typ (Binnenpegel)
        # 3: ID
        # 4: Datum+Uhrzeit ("04.09.2025 07:00")
        # 5: Wasserstand in cm (125)
        # 6: NN + m (202,37)
        # 7: Veränderung ("0 cm")
        # 8: Trend ("gleichbleibend")
        out = {}
        try:
            out["station"] = tds[0].get_text(strip=True)
            out["bezeichnung"] = tds[1].get_text(strip=True)
            out["station_type"] = tds[2].get_text(strip=True)
            out["station_id"] = tds[3].get_text(strip=True)
            out["datum_uhr"] = tds[4].get_text(strip=True)
            out["wasserstand_cm"] = parse_number(tds[5].get_text())
            out["nn_m"] = parse_number(tds[6].get_text())
            out["veraenderung_cm"] = parse_number(tds[7].get_text())
            out["veraenderung_trend"] = tds[8].get_text(strip=True)

            # Datum parsen (falls möglich)
            try:
                out["zeitpunkt"] = datetime.strptime(out["datum_uhr"], "%d.%m.%Y %H:%M")
            except Exception:
                out["zeitpunkt"] = None

            return out, True
        except Exception as e:
            logging.exception("Fehler beim Parsen der Zeile: %s", e)
            return {}, False

    def compute_meldestufe(wasserstand_cm: Optional[float]) -> Tuple[Optional[int], str, Optional[int]]:
        """Berechne Hochwasser (cm-basiert) und Meldestufe/symbol.
        Rückgabe: (hochwasser_cm, symbol_str, stufe_int)"""
        if wasserstand_cm is None:
            return None, "❌", None

        hochwasser = int(wasserstand_cm) - 132
        # Bedingungen in absteigender Reihenfolge
        if hochwasser >= 79:
            stufe, symbol = 3, "🟠"
        elif hochwasser >= 59:
            stufe, symbol = 2, "🟣"
        elif hochwasser >= 39:
            stufe, symbol = 1, "🟡"
        else:
            stufe, symbol = 0, "🟢"
        return hochwasser, symbol, stufe

    def maybe_write_file(path: Optional[str], content: str):
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            logging.exception("Fehler beim Schreiben der Datei %s", path)

    def save_block_png(symbol: str, hochwasser: int, filename: str = "062-Hochwasser.png", title: str = None):
        # Farbzuordnung nach Symbol
        color_map = {
            "🟢": (0, 200, 0),      # grün
            "🟡": (255, 215, 0),    # gelb
            "🟣": (186, 85, 211),   # violett
            "🟠": (255, 69, 0),     # orange/rot
        }
        bg_color = color_map.get(symbol, (128, 128, 128))  # default: grau
        text_color = (255, 255, 255)  # weiß

        # Größe des Blocks
        width, height = 200, 120
        img = Image.new("RGB", (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Schrift setzen (Fallback, wenn keine TTF-Schrift gefunden wird → default)
        try:
            font_big = ImageFont.truetype("Arial.ttf", 32)
            font_small = ImageFont.truetype("Arial.ttf", 20)
        except IOError:
            font_big = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Erst optionalen Titel oben zentriert zeichnen
        if title:
            bbox_title = draw.textbbox((0, 0), title, font=font_small)
            title_w = bbox_title[2] - bbox_title[0]
            pos_title = ((width - title_w) // 2, 5)  # 5 Pixel Abstand oben
            draw.text(pos_title, title, font=font_small, fill=text_color)

        # Hauptwert (z. B. "123 cm") in der Mitte
        text = f"{hochwasser} cm"
        bbox = draw.textbbox((0, 0), text, font=font_big)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        pos_value = ((width - text_w) // 2, (height - text_h) // 2 + 10)
        draw.text(pos_value, text, font=font_big, fill=text_color)

        img.save(filename)
        print(f"\nGrafik gespeichert: {filename}")

    def save_text_block(text_lines, symbol, stufe, filename="062-Hochwasser-Textblock.png"):
        # Hintergrundfarbe und Textfarbe
        bg_color = (255,255,255)
        text_color = (0,0,0)

        # Farbzuordnung für Kästchen
        color_map = {
            "🟢": (0, 200, 0),
            "🟡": (255, 215, 0),
            "🟣": (186, 85, 211),
            "🟠": (255, 69, 0),
        }
        box_color = color_map.get(symbol, (128, 128, 128))

        # Schrift
        try:
            font = ImageFont.truetype("Courier New.ttf", 20)
        except IOError:
            font = ImageFont.load_default()

        # Textgröße berechnen
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        max_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in text_lines)
        line_height = draw.textbbox((0, 0), "Test", font=font)[3] + 6

        img_height = line_height * len(text_lines) + 20
        img_width = max_width + 80  # etwas mehr Platz für das Kästchen
        img = Image.new("RGB", (img_width, img_height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Zeilen schreiben
        y = 10
        for line in text_lines:
            if line.startswith("Meldestufe:"):
                # Label-Spalte sauber setzen
                label = "Meldestufe:".ljust(20)
                draw.text((20, y), label, font=font, fill=text_color)

                # Pixelbreite des Labels bestimmen
                bbox_label = draw.textbbox((20, y), label, font=font)
                label_width = bbox_label[2] - bbox_label[0]

                # Position für Kasten: direkt hinter der Label-Spalte
                x_box = 20 + label_width + 5
                draw.rectangle([x_box, y, x_box+20, y+20], fill=box_color)

                # Stufe daneben
                draw.text((x_box+30, y), str(stufe), font=font, fill=text_color)
            else:
                draw.text((20, y), line, font=font, fill=text_color)
            y += line_height
        img.save(filename)
        print(f"Textblock gespeichert: {filename}")
        
# --- Main ---
    def main():
        try:
            soup = fetch_soup(URL)
        except Exception as e:
            logging.error("HTTP-Fehler oder Timeout: %s", e)
            return 2

        tds = find_abzucht_row(soup)
        if tds is None:
            logging.error("Keine Zeile mit 'Abzucht' gefunden.")
            return 3

        data, ok = parse_row(tds)
        if not ok:
            logging.error("Parsing schlug fehl.")
            return 4

        hochwasser, symbol, stufe = compute_meldestufe(data.get("wasserstand_cm"))

        # Ausgabe (konkret wie gewünscht)
        out_lines = [
            "Pegel der Abzucht in Oker",
            "von https://www.pegelonline.nlwkn.niedersachsen.de/Pegel/Binnenpegel/ID/794",
            "===========================================================================",
            f"{'Station:':20} {data.get('station')} {data.get('station_id')}",
             f"{'Bezeichnung:':20} {data.get('bezeichnung')}",
            f"{'Datum/Uhr:':20} {data.get('datum_uhr')}",
            f"{'Wasserstand (cm):':20} {data.get('wasserstand_cm')}",
            f"{'NN + m:':20} {data.get('nn_m')}",
            f"{'Δ in cm:':20} {data.get('veraenderung_cm')}",
            f"{'Trend:':20} {data.get('veraenderung_trend')}",
            f"{'Hochwasser (cm):':20} {hochwasser}",
            f"{'Meldestufe:':20} {symbol} {stufe}",
        ]
        output = "\n".join(out_lines)
        print(output)

        # optional: in Dateien schreiben (falls Pfade oben gesetzt)
        maybe_write_file(OUTPUT_FILE, output + "\n")

        save_block_png(symbol, hochwasser, "062-Hochwasser-Grafik.png", title="Abzucht-Pegel Oker")
        save_text_block(out_lines, symbol, stufe, "062-Hochwasser-Text.png")

except requests.RequestException as e:
    print("❌ Fehler beim Laden der Seite:", e)

if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
