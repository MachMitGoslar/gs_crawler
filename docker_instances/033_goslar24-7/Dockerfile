FROM ghcr.io/machmitgoslar/gs_crawler_python_basic_crawler:latest

# Systempakete für Pillow & SQLite
RUN apt-get update && apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y fonts-dejavu-core

# copy Code
ADD .. .

# SQLite-Datenbank liegt auf einem Volume (/data), weil das Dateisystem sonst schreibgeschützt
# ist. Die Tabelle legt init_db.py beim ersten Import zur Laufzeit an.
ENV DB_PATH=/data/webcam_images.db
RUN mkdir -p /data && chmod 1777 /data
