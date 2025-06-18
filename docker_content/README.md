# How-To Docker-to-JSON-Crawler

## Konfiguration

1. Bestehenden Ordner kopieren 
```
cp -r ./001_senioren ./002_test
```

2. Script mit passendem Code füllen
```
cp -f my_script.py ./002_test/script.py
```

3. (optional) requirements.txt anfügen
```
cp -f my_requirements.txt ./002_test/requirements.txt
```

4. Ablaufzeiten in  **./002_test/crontab** aufnehmen
```
# ┌───────────── Minute (0 - 59)
# │ ┌───────────── Hour (0 - 23)
# │ │ ┌───────────── Day of month (1 - 31)
# │ │ │ ┌───────────── Month (1 - 12)
# │ │ │ │ ┌───────────── Day of week (0 - 6) (Sunday to Saturday)
# │ │ │ │ │
# │ │ │ │ │
  0 2 * * * python3 /app/script.py
```

5. Eintrag in **./docker-compose.yml** ergänzen
```
  gs_python_compiler_002_test:
    build: ./002_senioren
    volumes:
      - ./output:/app/output
    container_name: gs_python_compiler_002_test
```

5. Container neu bauen und starten
```
docker-compose up --build -d
```



