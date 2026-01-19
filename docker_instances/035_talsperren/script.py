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
from matplotlib.colors import LinearSegmentedColormap
import os

# Setup (optional: Headless-Modus aktivieren)
options = Options()
options.add_argument("--headless")
service = FirefoxService(GeckoDriverManager().install())
driver = webdriver.Firefox(options=options, service=service, )

# Ziel-URL
base_url = "https://www.harzwasserwerke.de"
url = f"{base_url}/infoservice/aktuelle-talsperrendaten/"
output_path = "output/"
export_jsonfile = "035-talsperren_alle.json"

os.makedirs(output_path, exist_ok=True)

try:
    driver.get(url)
    time.sleep(5)  # Warten auf JS-Inhalte
    soup = BeautifulSoup(driver.page_source, "html.parser")

    result_div = soup.find("div", class_="slick-track")
    if not result_div:
        print("❌ slick-track nicht gefunden.")
        driver.quit()
        exit()

    # Messzeitpunkt auslesen
    messzeitpunkt_tag = soup.find_all("span", class_="datum")
    messzeitpunkt = messzeitpunkt_tag[1].get_text(strip=True) if messzeitpunkt_tag else "Messzeitpunkt unbekannt"

    stauhoehe_summe = 0.0  # Maximalinhalt
    stauinhalt_summe = 0.0  # Aktueller Inhalt

    for li in result_div.find_all("li"):
        hoehe_tag = li.find("strong", class_="data_stauhoehe")
        inhalt_tag = li.find("strong", class_="data_stauinhalt")

        if hoehe_tag and inhalt_tag:
            try:
                hoehe = float(hoehe_tag.get_text(strip=True).replace(",", "."))
                inhalt = float(inhalt_tag.get_text(strip=True).replace(",", "."))
                stauhoehe_summe += hoehe
                stauinhalt_summe += inhalt
            except ValueError:
                continue

    if stauhoehe_summe > 0:
        fuellstand_prozent = (stauinhalt_summe / stauhoehe_summe) * 100
        description = "Summe der Füllstände aller Talsperren der Harzwasserwerke in Prozent"
    else:
        fuellstand_prozent = 0
        description = "Keine gültigen Füllstandsdaten gefunden."

    # PNG erzeugen mit Prozentwert groß und Messzeitpunkt darunter
    png_filename = "fuellstand_prozent.png"

    cmap = LinearSegmentedColormap.from_list("percent_cmap", ["red", "yellow", "green"])
    farbe = cmap(min(max(fuellstand_prozent / 100, 0), 1))  # Clamp zwischen 0 und 1

    plt.figure(figsize=(3, 3), dpi=100)
    plt.axis("off")

    # Prozentwert groß, mittig leicht nach oben
    # Prozentwert groß, farblich angepasst
    plt.text(
    0.5, 0.6, f"{fuellstand_prozent:.1f}%",
    fontsize=36, ha='center', va='center',
    color='black',
    bbox=dict(facecolor=farbe, edgecolor='none', boxstyle='round,pad=0.6'))

    # plt.text(0.5, 0.6, f"{fuellstand_prozent:.1f}%", fontsize=36, ha='center', va='center')

    # Messzeitpunkt klein darunter
    plt.text(0.5, 0.3, messzeitpunkt, fontsize=12, ha='center', va='center')

    # Speichern ohne tight_layout, dafür bbox_inches nutzen
    plt.savefig(os.path.join(output_path, png_filename), dpi=100, bbox_inches="tight", pad_inches=0)
    plt.close()

    # JSON erzeugen
    daten = {
        "title": messzeitpunkt,
        "description": description,
        "image_url": "https://crawler.goslar.app/crawler/fuellstand_prozent.png",
        "call_to_action_url": url,
        "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
    }

    with open(os.path.join(output_path, export_jsonfile), "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

    print("✅ JSON erfolgreich erstellt:")
    print(json.dumps(daten, ensure_ascii=False, indent=2))

finally:
    driver.quit()
