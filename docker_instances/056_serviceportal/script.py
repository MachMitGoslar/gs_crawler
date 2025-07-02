import requests
from bs4 import BeautifulSoup
import random
import json
import os
from datetime import datetime

# Ziel-URL
url = "https://service.goslar.de/home?search="
imageurl = "https://crawler.goslar.app/senioren/jsonapp/023-serviceportal.png"

# Ausgabeordner
save_dir = "output/"
export_jsonfile = "056-serviceportal.json"
export_jsonfile_alle = "056-serviceportal-alle.json"
os.makedirs(save_dir, exist_ok=True)

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    services_div = soup.find("div", class_="services")
    eintraege = []

    zufallszahl = random.randint(1, 8)
    if zufallszahl == 1:
        contitle = "Stadt Goslar - einfach online:"
    elif zufallszahl == 2:
        contitle = "Stadt Goslar - online einfach:"
    elif zufallszahl == 3:
        contitle = "Keiner hat daran geglaubt!\nWir schon - jetzt online:"
    elif zufallszahl == 4:
        contitle = "Hör auf, Du kannst doch gar nicht online..."
    elif zufallszahl == 5:
        contitle = "Nach 15 Jahren Testphase - wir sind drin!"
    elif zufallszahl == 6:
        contitle = "Wir wollen online, wenn Du bereit bist:"
    elif zufallszahl == 7:
        contitle = "Wenn Du mutig bist, versuchs doch online:"
    elif zufallszahl == 8:
        contitle = "Sag einfach: 'Ja, ich will online'"
    else:
        contitle = "Trau Dich - lern uns kennen:" 


    if services_div:
        a_tags = services_div.find_all("a")
        for a in a_tags:
            href = a.get("href")
            title = a.get("title")
            if href and title:
                eintrag = {
                    "title": contitle + "\n\"" + title.strip() + "\"",
                    "description": contitle + "\n\"" + title.strip() + "\"",
                    "image_url": imageurl,
                    "call_to_action_url": href.strip(),
                    "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
                }
                eintraege.append(eintrag)
        
        # Standardsuche auch mit implementieren
        eintrag = {
            "title": "Such doch mal im Serviceportal nach einer Leistung!",
            "description": "Such doch mal im Serviceportal nach einer Leistung!\nServiceportal jetzt testen!",
            "image_url": imageurl,
            "call_to_action_url": "https://service.goslar.de/?search=",
            "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
        }
        eintraege.append(eintrag)
        
        eintrag = {
            "title": "Echt jetzt, die Stadtverwaltung kann online?",
            "description": "Echt jetzt, die Stadtverwaltung kann online?\nServiceportal jetzt testen!",
            "image_url": imageurl,
            "call_to_action_url": "https://service.goslar.de/?search=",
            "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
        }
        eintraege.append(eintrag)

        # Speichere alle
        with open(os.path.join(save_dir, export_jsonfile_alle), "w", encoding="utf-8") as f_all:
            json.dump(eintraege, f_all, ensure_ascii=False, indent=2)

        # Wähle einen zufällig aus
        if eintraege:
            zufall = random.choice(eintraege)
            with open(os.path.join(save_dir, export_jsonfile), "w", encoding="utf-8") as f_one:
                json.dump(zufall, f_one, ensure_ascii=False, indent=2)
            print("✅ Erfolgreich gespeichert:", zufall["title"])
        else:
            print("⚠️ Keine Einträge gefunden.")
    else:
        print("⚠️ Kein 'services'-Container gefunden.")

except requests.RequestException as e:
    print("❌ Fehler beim Laden der Seite:", e)
