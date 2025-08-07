import logging
from io import BytesIO
import sqlite3
import os
import json
from datetime import datetime
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont
import textwrap
import pytz



DB_PATH = "webcam_images.db"

def slugify_url(url):
    """Hilfsfunktion: Dateinamen aus URL generieren"""
    return url.split("/")[-1].replace(".jpg", "").replace("-", "_")

def create_gif_from_db_images():
    output_dir = "output"
    img_url_path = "https://crawler.goslar.app/crawler/"
    os.makedirs(output_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
           SELECT url, image, created_at FROM webcam_images
           WHERE datetime(created_at) >= datetime('now', '-6 days')
           ORDER BY url, created_at
       """)
    rows = cur.fetchall()
    conn.close()

    images_by_url = defaultdict(list)

    for url, image_data, created_at in rows:
        img = Image.open(BytesIO(image_data)).convert("RGB")
        img = add_timestamp_overlay(img, datetime.fromisoformat(created_at))
        images_by_url[url].append((created_at, img))

    if not images_by_url:
        logging.info("⚠️ Keine Bilder gefunden.")
        return

    for url, img_list in images_by_url.items():
        img_list.sort()  # sortiere nach Zeit
        images = [img for _, img in img_list]

        if not images:
            continue

        # Datei- & URL-Namen erstellen
        slug = slugify_url(url)
        gif_filename = f"033_gif_{slug}.gif"
        json_filename = f"033_gif_{slug}.json"
        gif_path = os.path.join(output_dir, gif_filename)
        json_path = os.path.join(output_dir, json_filename)

        # GIF speichern
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=500,
            loop=0,
            optimize=True
        )
        logging.info(f"✅ GIF gespeichert: {gif_path}")

        # JSON-Daten schreiben
        json_data = {
            "title": f"Webcam {slug.replace('_', ' ').capitalize()}",
            "description": f"Webcam-Ansicht für {slug}",
            "image_url": f"{img_url_path}{gif_filename}",
            "call_to_action_url": "https://www.meingoslar.de/erleben-und-geniessen/webcams#h5189",
            "published_at": datetime.now().strftime("%Y-%m-%dT%H:%M")
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        logging.info(f"✅ JSON gespeichert: {json_path}")



def add_timestamp_overlay(img, timestamp):
    """Fügt transparenten Datumsstempel (nur Text) in westeuropäischer Zeit hinzu."""
    draw = ImageDraw.Draw(img, "RGBA")

    # Westeuropäische Zeit (z.B. Berlin)
    tz_berlin = pytz.timezone("Europe/Berlin")
    timestamp_local = timestamp.astimezone(tz_berlin)
    text = timestamp_local.strftime("%d.%m.%Y")

    # Schriftart und -größe
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_size = 28
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    # Textgröße berechnen
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Position unten mittig
    x = (img.width - text_width) // 2
    y = img.height - text_height - 20

    # Nur transparente, weiße Schrift zeichnen (ohne Hintergrund)
    draw.text((x, y), text, fill=(255, 255, 255, 10), font=font)

    return img
