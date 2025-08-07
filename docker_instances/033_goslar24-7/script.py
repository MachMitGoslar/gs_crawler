import logging
import schedule
import time
from get_and_store_images import fetch_and_store_images, delete_old_images
from create_gif import create_gif_from_db_images

# define logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def job():
    fetch_and_store_images()
    create_gif_from_db_images()
    delete_old_images()

logging.info("🕒 Initiale Ausführung")
job()
schedule.every().hour.at(":00").do(job)
logging.info("⏳ Warte auf nächste Ausführung ...")
while True:
    schedule.run_pending()
    time.sleep(60)
