import requests
import os
import json
import time
from PIL import Image, ImageDraw
import io
import imageio


# URLs und Zielverzeichnis
gif_url = "https://files.ufz.de/~drought/nFK_0_25_daily_n14.gif"
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

# Dateipfade
gif_path = os.path.join(output_dir, "047_bodenwasser.gif")
focus_gif_path = os.path.join(output_dir, "047_bodenwasser_focus.gif")
json_path = os.path.join(output_dir, "047_bodenwasser.json")

# Herunterladen und Öffnen des GIF
gif_url = "https://files.ufz.de/~drought/PAW_0_25cm_daily_n14.gif"
response = requests.get(gif_url)
gif_bytes = io.BytesIO(response.content)
gif = Image.open(gif_bytes)

# Erster Frame auswählen
frame = gif.convert("RGB")
width, height = frame.size

# Geografische Koordinaten für Goslar
goslar_lat = 51.9
goslar_lon = 10.4

# Kartenbereich des GIF (Deutschland grob)
lat_min, lat_max = 47.0, 55.0
lon_min, lon_max = 5.0, 15.0

# Mapping der Koordinaten auf Pixelposition
x = int((goslar_lon - lon_min) / (lon_max - lon_min) * width)
y = int((lat_max - goslar_lat) / (lat_max - lat_min) * height)

# Kopiere alle Frames und markiere Goslar
frames = []
gif.seek(0)
try:
    while True:
        frame = gif.convert("RGB")
        draw = ImageDraw.Draw(frame)
        # Kreis um Goslar (Radius 10 Pixel), Rand schwarz
        radius = 50
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), outline="black", width=15)
        frames.append(frame)
        gif.seek(gif.tell() + 1)
except EOFError:
    pass

# Neues GIF speichern
os.makedirs(output_dir, exist_ok=True)
marked_gif_path = os.path.join(output_dir, "047_bodenwasser.gif")
frames[0].save(marked_gif_path, save_all=True, append_images=frames[1:], loop=0, duration=gif.info['duration'])

# JSON-Metadaten erstellen
data = {
    "title": "Tagesaktueller Bodenwasserstand",
    "description": "Tagesaktueller Stand zum pflanzenverfügbaren Wasser im Boden.",
    "call_to_action_url": "https://www.ufz.de/index.php?de=37937",
    "image_url": "https://machmit.goslar.de/fileadmin/media-machmit/goslar-app/011-bodenwasser.gif",
    "published_at": time.strftime("%Y-%m-%dT%H:%M")
}

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"✅ Metadaten gespeichert unter: {json_path}")
