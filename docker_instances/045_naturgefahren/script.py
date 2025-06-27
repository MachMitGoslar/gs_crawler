from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

import time
import json
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import random


# Setup (optional: Headless-Modus aktivieren)
options = Options()
options.add_argument("--headless")
service = FirefoxService(GeckoDriverManager().install())
driver = webdriver.Firefox(options=options, service=service, )

insides_url = "https://insides.goslar-app.de/bevoelkerungsschutz"

try:
    driver.get("https://www.naturgefahrenportal.de/de/alerts")
    wait = WebDriverWait(driver, 50)


    search_box = wait.until(EC.visibility_of_any_elements_located((By.NAME, "searchlabelwarn")))[0]

    # Suchfeld finden)
    #search_box = wait.until(EC.element_to_be_clickable((By.NAME, "searchlabelwarn")))
    adresse = "Charley-Jacob-Str. 3, 38640 Goslar"

    # Adresse setzen
    search_box.send_keys(adresse)

    # Kurze Wartezeit, damit JS reagieren kann
    # time.sleep(1)

    # Leerzeichen + RETURN senden
    search_box.send_keys(" ")
    time.sleep(2)
    search_box.send_keys(Keys.RETURN)

    # Warten bis Antwort geladen ist
    zeitstempel = time.strftime("%d.%m.%Y - %H:%M")
    target_url = "https://www.goslar.de/stadt-und-verwaltung/verwaltung/brand-und-katastrophenschutz/selbstschutz-und-notfallvorsorge"

    description_elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2.mb-1.text-xl")))
    try:
        description_warn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h3.flex-1.text-left"))
        )
        warn_text = description_warn.text.strip()
    except TimeoutException:
        warn_text = None
        print("Element ist NICHT vorhanden")

    # description_warn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h3.flex-1.text-left")))
    description = description_elem.text.strip()
    description = description.replace("Für Charley-Jacob-Straße 3, 38640 Goslar", zeitstempel + ": Es")

    print(description)
    if warn_text:
        description = zeitstempel + ":\n" + warn_text
        target_url = driver.current_url
    else:
        if description.find("Es liegen keine Warnungen vor"):
            # insides durchforsten und zufälligen Link wählen
            # Ziel-URL
            url = "https://insides.goslar-app.de/bevoelkerungsschutz"

            # Seite laden
            response = requests.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            savemepath = os.getcwd() + "/output"
            os.makedirs(savemepath, exist_ok=True)

            # Suche
            hauptbereich = soup.find("div", id="bevoelkerungsschutz")

            eintraege = []
            if hauptbereich:
                # Suche nach allen direkten Einträgen (divs mit class="block_textimage" z.B.)
                # Hier solltest du den genauen Container der einzelnen Einträge anpassen.
                # Beispiel: alle divs mit wrap_image_right, die die Bilder enthalten
                container_div = hauptbereich.find_all("div", class_="block_textimage")
                result = random.choice(container_div)
                # Beschreibung und Link aus wrap_text_left
                text_div = result.find("div", class_="wrap_text_left")
                p_tags = text_div.find_all("p") if text_div else []
                beschreibung = p_tags[0].get_text(strip=True) if len(p_tags) >= 1 else ""
                a_tag = p_tags[1].find("a") if len(p_tags) >= 2 else None
                link = a_tag["href"] if a_tag and a_tag.has_attr("href") else None

                description = "aktuell keine Warnung: \n" + beschreibung

                # Bild wird aktuell nicht gebraucht aus, sonst aus wrap_image_right
                # img_div = container_div.find("div", class_="wrap_image_right")
                # img_tag = img_div.find("img") if img_div else None
                # image_url = urljoin(url, img_tag["src"]) if img_tag and img_tag.has_attr("src") else None
            target_url = link

    # JSON-Datensatz erstellen
    data = {
        "title": "Goslar, " + description,
        "description": description,
        "call_to_action_url": target_url,
        # "call_to_action_url": driver.current_url,
        # "image_url": "https://machmit.goslar.de/fileadmin/media-machmit/goslar-app/bevoelkerungsschutz.jpg",
        "image_url": "",
        "published_at": ""
        # "published_at": time.strftime("%Y-%m-%dT%H:%M")
    }

    # Speichern
    os.makedirs("output", exist_ok=True)
    with open("output/045_naturgefahren_de.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ Ergebnis gespeichert in 'output/045_naturgefahren_de.json'")
    print(json.dumps(data, ensure_ascii=False, indent=2))

finally:
    driver.quit()
