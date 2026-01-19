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

# SQLite-Datenbank bei Build erstellen
RUN python init_db.py
