import logging
import requests
from PIL import Image
from io import BytesIO
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "webcam_images.db"

# Webcam-URLs
URLS = [
    'https://webcams.goslar.de/schuhhof.jpg',
    'https://webcams.goslar.de/marktplatz-gmg.jpg',
]

# Zielgröße für das Bild
TARGET_SIZE = (600, 400)

def save_image_to_db(url, image_bytes):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO webcam_images (url, image, created_at) VALUES (?, ?, ?)",
        (url, image_bytes, datetime.now())
    )
    conn.commit()
    cur.close()
    conn.close()

def fetch_and_store_images(max_retries=3):
    for url in URLS:
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

                img = Image.open(BytesIO(response.content)).convert("RGB")
                img = img.resize(TARGET_SIZE, Image.LANCZOS)

                buffer = BytesIO()
                img.save(buffer, format="JPEG")
                save_image_to_db(url, buffer.getvalue())
                logging.info(f"✅ Bild von {url} gespeichert.")
                break  # Erfolgreich -> Schleife abbrechen
            except Exception as e:
                logging.warning(f"⚠️ Versuch {attempt} fehlgeschlagen für {url}: {e}")
                if attempt == max_retries:
                    logging.error(f"❌ Alle {max_retries} Versuche für {url} fehlgeschlagen.")


def delete_old_images():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    seven_days_ago = datetime.now() - timedelta(days=7)
    cur.execute("""
        DELETE FROM webcam_images
        WHERE datetime(created_at) < ?
    """, (seven_days_ago,))
    deleted = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    logging.info(f"🧹 {deleted} alte Bilder gelöscht.")