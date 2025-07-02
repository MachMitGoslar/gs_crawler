import requests
from PIL import Image
from io import BytesIO
import os
import json
from datetime import datetime

# Liste der Webcam-Bilder
urls = [
    'https://webcams.goslar.de/schuhhof.jpg',
    'https://webcams.goslar.de/marktplatz-gmg.jpg',
]
json_filename = "032_webcams_goslar.json"

# Zielgröße (Breite x Höhe)
target_size = (600, 400)

images = []

# Bilder laden, skalieren, vereinheitlichen
for url in urls:
    response = requests.get(url)
    img = Image.open(BytesIO(response.content)).convert("RGB")
    img = img.resize(target_size, Image.LANCZOS)
    images.append(img)

# GIF-Pfad festlegen
gif_filename = "webcam.gif"
savemepath = "output/"
output_path = os.path.join(savemepath, gif_filename)


# GIF erzeugen
images[0].save(
    output_path,
    save_all=True,
    append_images=images[1:],
    duration=5000,
    loop=0,
    optimize=True
)

print(f"✅ GIF wurde erstellt: {savemepath}")

# JSON-Daten vorbereiten
json_data = {
    "title": "Webcams Goslar",
    "description": "Webcam Views aus Goslar",
    "image_url": f"https://machmit.goslar.de/fileadmin/media-machmit/goslar-app/{gif_filename}",  # URL zum veröffentlichten GIF
    "call_to_action_url": "https://www.meingoslar.de/erleben-und-geniessen/webcams#h5189",
    "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
}

# JSON speichern
# json_output_path = os.path.join(savemepath, "webcams_goslar.json")
with open(os.path.join(savemepath, json_filename), "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print(f"✅ JSON-Schnittstelle gespeichert: {savemepath}")
