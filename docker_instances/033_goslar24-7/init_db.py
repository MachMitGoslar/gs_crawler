import sqlite3

conn = sqlite3.connect("webcam_images.db")
cur = conn.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS webcam_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        image BLOB NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
""")
conn.commit()
conn.close()
