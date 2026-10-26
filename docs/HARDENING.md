# Härtung der Container und neue Routen

Dieses Dokument beschreibt die Sicherheitsmaßnahmen rund um die Crawler-Container (Auslöser: CVE-2026-111497
im Brotli-Decoder), das Deployment auf dem Server und die **geänderten öffentlichen URLs**.

## Was sich geändert hat

| Maßnahme | Wirkung |
|---|---|
| Kein Browser mehr (`035_talsperren` nutzt `requests`, Selenium-/Firefox-Image entfernt) | Kein Rendering fremder Inhalte im Container, kein Brotli-Decoder auf dem Netzwerkpfad |
| Scheduler statt cron (`scheduler.py`) | Kein Root mehr nötig, Logs direkt in `docker logs`, kein `cron`/`rsyslog` im Image |
| Container laufen als Hosting-User (`user: CRAWLER_UID:CRAWLER_GID`) | Dateien gehören dem Hosting-User, kein root-eigener Müll im Docroot |
| `read_only: true`, `cap_drop: ALL`, `no-new-privileges`, `tmpfs` für `/tmp` | Ein kompromittierter Prozess kann nichts dauerhaft ablegen und keine Rechte erweitern |
| Jeder Crawler sieht nur seinen eigenen Ordner `httpdocs/crawler/<id>` | Ein Crawler kann Ausgaben anderer Crawler nicht überschreiben |
| Bind-Mounts mit `create_host_path: false` | Fehlende Ordner brechen `compose up` ab, statt als root angelegt zu werden |
| Health Monitor liest `httpdocs/crawler` nur lesend | Schreibt nur nach `httpdocs/crawler/000_health_monitor` |

## Deployment auf dem Server

Einmalig, als **Hosting-User** (nicht als root):

```bash
id -u && id -g                          # UID/GID des Hosting-Users
# CRAWLER_UID und CRAWLER_GID in die vorhandene .env eintragen (Vorlage: .env.example)
./scripts/init-output-dirs.sh           # legt httpdocs/crawler/<id> an
```

Danach wie gewohnt:

```bash
docker compose pull && docker compose up -d
```

Hinweise:
- `httpdocs/crawler` muss dem Hosting-User gehören. Alte Dateien im Wurzelverzeichnis (flache Pfade) werden nicht mehr
  geschrieben und können nach der Umstellung entfernt werden.
- Die SQLite-Datenbank von `033_goslar24-7` liegt im Volume `gs_033_data`. Der bisherige Verlauf im alten Container
  wird nicht übernommen, die GIFs füllen sich innerhalb weniger Stunden wieder.
- Zeiten im Scheduler gelten in UTC (wie vorher bei cron). Der Takt steht pro Crawler als `ENV SCHEDULE` im Dockerfile.
- Läuft Docker rootless oder mit Podman, entfällt das Mapping der UID, `CRAWLER_UID` muss dann zum Container-User passen.

## nginx in Plesk (zweite Schicht)

Unter *Apache & nginx-Einstellungen → Zusätzliche nginx-Anweisungen* eintragen. Annahme: nginx liefert die
statischen Dateien direkt aus (in Plesk: "Statische Dateien direkt von nginx bereitstellen"). Nach dem Eintragen testen.

```nginx
# Aus /crawler/ nur Daten und statische Assets ausliefern, nichts Ausführbares (.php, .htaccess, ...)
location ^~ /crawler/ {
    location ~* ^/crawler/.+\.(json|xml|png|jpe?g|gif|svg|webp|ico|css|js|html|woff2?)$ {
        add_header X-Content-Type-Options "nosniff" always;
    }
    location ~* ^/crawler/ {
        # alle anderen Dateitypen sperren
        if ($uri !~* \.(json|xml|png|jpe?g|gif|svg|webp|ico|css|js|html|woff2?)$) { return 403; }
    }
}

# Reine Daten brauchen keinerlei Aktivinhalt: JSON/XML mit restriktiver CSP ausliefern
location ~* ^/crawler/.+\.(json|xml)$ {
    add_header X-Content-Type-Options "nosniff" always;
    add_header Content-Security-Policy "default-src 'none'" always;
}
```

Offen: Eine CSP für die HTML-Seiten (`*_index.html` usw.) ist noch nicht festgelegt, weil sie Skripte und Bilder von
mehreren Hosts laden können. Empfehlung: zuerst im Report-Only-Modus testen.

## Neue Routen

Jeder Crawler liegt jetzt unter `/crawler/<id>/`. Dateinamen bleiben gleich, nur der Ordner kommt dazu. Die
Alt-Pfade werden nicht mehr beschrieben; Konsumenten (Apps, Verlinkungen) müssen auf die neuen Pfade umgestellt werden.
Die URLs **innerhalb** der erzeugten JSON-Dateien (`image_url`, `call_to_action_url`) zeigen bereits auf die neuen Pfade.

Zusätzlich neu: `/crawler/000_health_monitor/000-health-status.json` (vorher `/crawler/000-health-status.json`).

Der Crawler `060_defi_kataster` liegt jetzt unter `/crawler/060_defi_kataster/` (vorher `/crawler/defi-kataster/` und
als Kopie unter `/crawler/060_defi_kataster/`), `070_wochenmarkt` unter `/crawler/070_wochenmarkt/` (vorher `wochenmaerkte/`),
`073_busflotte` unter `/crawler/073_busflotte/` (vorher `busflotte/`).

| Crawler | Alt | Neu |
|---|---|---|
| `001_senioren` | `/crawler/001_senioren_feed.xml` | `/crawler/001_senioren/001_senioren_feed.xml` |
| `002_gz` | `/crawler/002_goslarsche.json` | `/crawler/002_gz/002_goslarsche.json` |
| `002_gz` | `/crawler/002_goslarsche-alle.json` | `/crawler/002_gz/002_goslarsche-alle.json` |
| `040_hp` | `/crawler/040_hp.json` | `/crawler/040_hp/040_hp.json` |
| `004_zufaellig-nix-vor` | `/crawler/ui-kit/goslar-ui.css` | `/crawler/004_zufaellig-nix-vor/ui-kit/goslar-ui.css` |
| `004_zufaellig-nix-vor` | `/crawler/ui-kit/goslar-ui.js` | `/crawler/004_zufaellig-nix-vor/ui-kit/goslar-ui.js` |
| `004_zufaellig-nix-vor` | `/crawler/004_zufaellig-nix-vor.json` | `/crawler/004_zufaellig-nix-vor/004_zufaellig-nix-vor.json` |
| `004_zufaellig-nix-vor` | `/crawler/004_zufaellig-nix-vor-alle.json` | `/crawler/004_zufaellig-nix-vor/004_zufaellig-nix-vor-alle.json` |
| `004_zufaellig-nix-vor` | `/crawler/004_zufaellig-nix-vor.html` | `/crawler/004_zufaellig-nix-vor/004_zufaellig-nix-vor.html` |
| `004_zufaellig-nix-vor` | `/crawler/004_zufaellig-nix-vor-alle.html` | `/crawler/004_zufaellig-nix-vor/004_zufaellig-nix-vor-alle.html` |
| `014_kunst_in_ar` | `/crawler/017-kunst-in-ar-single.json` | `/crawler/014_kunst_in_ar/017-kunst-in-ar-single.json` |
| `019_was_app` | `/crawler/019_was_app.json` | `/crawler/019_was_app/019_was_app.json` |
| `027_erster_freitag` | `/crawler/027-erster-freitag.json` | `/crawler/027_erster_freitag/027-erster-freitag.json` |
| `041_immenrode` | `/crawler/041_immenrode.json` | `/crawler/041_immenrode/041_immenrode.json` |
| `044_wiedelah` | `/crawler/044-wiedelah.json` | `/crawler/044_wiedelah/044-wiedelah.json` |
| `044_wiedelah` | `/crawler/044-wiedelah_alle.json` | `/crawler/044_wiedelah/044-wiedelah_alle.json` |
| `048_jerstedt` | `/crawler/048_jerstedt.json` | `/crawler/048_jerstedt/048_jerstedt.json` |
| `031_goslarer_geschichten` | `/crawler/031-goslarer_geschichten.json` | `/crawler/031_goslarer_geschichten/031-goslarer_geschichten.json` |
| `042_freiwilligen` | `/crawler/ui-kit/goslar-ui.css` | `/crawler/042_freiwilligen/ui-kit/goslar-ui.css` |
| `042_freiwilligen` | `/crawler/ui-kit/goslar-ui.js` | `/crawler/042_freiwilligen/ui-kit/goslar-ui.js` |
| `042_freiwilligen` | `/crawler/042-freiwilligenagentur.json` | `/crawler/042_freiwilligen/042-freiwilligenagentur.json` |
| `042_freiwilligen` | `/crawler/042-freiwilligenagentur-alle.json` | `/crawler/042_freiwilligen/042-freiwilligenagentur-alle.json` |
| `042_freiwilligen` | `/crawler/042_freiwilligenagentur_index.html` | `/crawler/042_freiwilligen/042_freiwilligenagentur_index.html` |
| `042_freiwilligen` | `/crawler/042_freiwilligenagentur_detail.html` | `/crawler/042_freiwilligen/042_freiwilligenagentur_detail.html` |
| `035_talsperren` | `/crawler/035-talsperren_alle.json` | `/crawler/035_talsperren/035-talsperren_alle.json` |
| `035_talsperren` | `/crawler/035-talsperren_index.json` | `/crawler/035_talsperren/035-talsperren_index.json` |
| `045_naturgefahren` | `/crawler/045_naturgefahren/045_naturgefahren_de.json` | `/crawler/045_naturgefahren/045_naturgefahren_de.json` |
| `046_bio_stadt_goslar` | `/crawler/046_bio_stadt_goslar/ui-kit/goslar-ui.css` | `/crawler/046_bio_stadt_goslar/ui-kit/goslar-ui.css` |
| `046_bio_stadt_goslar` | `/crawler/046_bio_stadt_goslar/ui-kit/goslar-ui.js` | `/crawler/046_bio_stadt_goslar/ui-kit/goslar-ui.js` |
| `046_bio_stadt_goslar` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_card.json` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_card.json` |
| `046_bio_stadt_goslar` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_alle.json` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_alle.json` |
| `046_bio_stadt_goslar` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_standorte.json` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_standorte.json` |
| `046_bio_stadt_goslar` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_index.html` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_index.html` |
| `046_bio_stadt_goslar` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_detail.html` | `/crawler/046_bio_stadt_goslar/046_bio_stadt_goslar_detail.html` |
| `047_bodenwasser` | `/crawler/047_bodenwasser.json` | `/crawler/047_bodenwasser/047_bodenwasser.json` |
| `047_bodenwasser` | `/crawler/047_bodenwasser.gif` | `/crawler/047_bodenwasser/047_bodenwasser.gif` |
| `050_tschuessschule_studium` | `/crawler/050-tschuessschule-studium.json` | `/crawler/050_tschuessschule_studium/050-tschuessschule-studium.json` |
| `050_tschuessschule_studium` | `/crawler/050-tschuessschule-studium-alle.json` | `/crawler/050_tschuessschule_studium/050-tschuessschule-studium-alle.json` |
| `051_vhs` | `/crawler/051_vhs.json` | `/crawler/051_vhs/051_vhs.json` |
| `051_vhs` | `/crawler/051_vhs-alle.json` | `/crawler/051_vhs/051_vhs-alle.json` |
| `052_vhs_kinderuni` | `/crawler/052_vhs_kinderuni.json` | `/crawler/052_vhs_kinderuni/052_vhs_kinderuni.json` |
| `052_vhs_kinderuni` | `/crawler/052_vhs_kinderuni_alle.json` | `/crawler/052_vhs_kinderuni/052_vhs_kinderuni_alle.json` |
| `053_tschuessschule_praktikum` | `/crawler/053-tschuessschule-praktikum.json` | `/crawler/053_tschuessschule_praktikum/053-tschuessschule-praktikum.json` |
| `053_tschuessschule_praktikum` | `/crawler/053-tschuessschule-praktikum-alle.json` | `/crawler/053_tschuessschule_praktikum/053-tschuessschule-praktikum-alle.json` |
| `054_tschuessschule_ausbildung` | `/crawler/054-tschuessschule-ausbildung.json` | `/crawler/054_tschuessschule_ausbildung/054-tschuessschule-ausbildung.json` |
| `054_tschuessschule_ausbildung` | `/crawler/054-tschuessschule-ausbildung-alle.json` | `/crawler/054_tschuessschule_ausbildung/054-tschuessschule-ausbildung-alle.json` |
| `032_webcams_goslar` | `/crawler/032_webcams_goslar.json` | `/crawler/032_webcams_goslar/032_webcams_goslar.json` |
| `032_webcams_goslar` | `/crawler/032_webcams.gif` | `/crawler/032_webcams_goslar/032_webcams.gif` |
| `033_goslar24-7` | `/crawler/033_gif_schuhhof.json` | `/crawler/033_goslar24-7/033_gif_schuhhof.json` |
| `033_goslar24-7` | `/crawler/033_gif_schuhhof.gif` | `/crawler/033_goslar24-7/033_gif_schuhhof.gif` |
| `033_goslar24-7` | `/crawler/033_gif_marktplatz_gmg.gif` | `/crawler/033_goslar24-7/033_gif_marktplatz_gmg.gif` |
| `033_goslar24-7` | `/crawler/033_gif_marktplatz_gmg.json` | `/crawler/033_goslar24-7/033_gif_marktplatz_gmg.json` |
| `056_serviceportal` | `/crawler/ui-kit/goslar-ui.css` | `/crawler/056_serviceportal/ui-kit/goslar-ui.css` |
| `056_serviceportal` | `/crawler/ui-kit/goslar-ui.js` | `/crawler/056_serviceportal/ui-kit/goslar-ui.js` |
| `056_serviceportal` | `/crawler/056-serviceportal.json` | `/crawler/056_serviceportal/056-serviceportal.json` |
| `056_serviceportal` | `/crawler/056_serviceportal_index.html` | `/crawler/056_serviceportal/056_serviceportal_index.html` |
| `056_serviceportal` | `/crawler/056_serviceportal_termin.html` | `/crawler/056_serviceportal/056_serviceportal_termin.html` |
| `056_serviceportal` | `/crawler/056_serviceportal_image.png` | `/crawler/056_serviceportal/056_serviceportal_image.png` |
| `060_defi_kataster` | `/crawler/defi-kataster/ui-kit/goslar-ui.css` | `/crawler/060_defi_kataster/ui-kit/goslar-ui.css` |
| `060_defi_kataster` | `/crawler/defi-kataster/ui-kit/goslar-ui.js` | `/crawler/060_defi_kataster/ui-kit/goslar-ui.js` |
| `060_defi_kataster` | `/crawler/defi-kataster/060-defi-kataster.json` | `/crawler/060_defi_kataster/060-defi-kataster.json` |
| `060_defi_kataster` | `/crawler/defi-kataster/index.html` | `/crawler/060_defi_kataster/index.html` |
| `060_defi_kataster` | `/crawler/defi-kataster/script.js` | `/crawler/060_defi_kataster/script.js` |
| `060_defi_kataster` | `/crawler/defi-kataster/style.css` | `/crawler/060_defi_kataster/style.css` |
| `080_bereitschaftsdienste` | `/crawler/ui-kit/goslar-ui.css` | `/crawler/080_bereitschaftsdienste/ui-kit/goslar-ui.css` |
| `080_bereitschaftsdienste` | `/crawler/ui-kit/goslar-ui.js` | `/crawler/080_bereitschaftsdienste/ui-kit/goslar-ui.js` |
| `080_bereitschaftsdienste` | `/crawler/080_bereitschaftsdienste_card.json` | `/crawler/080_bereitschaftsdienste/080_bereitschaftsdienste_card.json` |
| `080_bereitschaftsdienste` | `/crawler/080_bereitschaftsdienste_card.png` | `/crawler/080_bereitschaftsdienste/080_bereitschaftsdienste_card.png` |
| `080_bereitschaftsdienste` | `/crawler/080_bereitschaftsdienste_index.html` | `/crawler/080_bereitschaftsdienste/080_bereitschaftsdienste_index.html` |
| `080_bereitschaftsdienste` | `/crawler/080_bereitschaftsdienste_medizinisch.html` | `/crawler/080_bereitschaftsdienste/080_bereitschaftsdienste_medizinisch.html` |
| `080_bereitschaftsdienste` | `/crawler/080_bereitschaftsdienste_staedtisch.html` | `/crawler/080_bereitschaftsdienste/080_bereitschaftsdienste_staedtisch.html` |
| `080_bereitschaftsdienste` | `/crawler/080_bereitschaftsdienste_sicherheit.html` | `/crawler/080_bereitschaftsdienste/080_bereitschaftsdienste_sicherheit.html` |
| `070_wochenmarkt` | `/crawler/wochenmaerkte/070_wochenmarkt_card.json` | `/crawler/070_wochenmarkt/070_wochenmarkt_card.json` |
| `070_wochenmarkt` | `/crawler/wochenmaerkte/070_wochenmarkt_alle.json` | `/crawler/070_wochenmarkt/070_wochenmarkt_alle.json` |
| `072_karriere` | `/crawler/ui-kit/goslar-ui.css` | `/crawler/072_karriere/ui-kit/goslar-ui.css` |
| `072_karriere` | `/crawler/ui-kit/goslar-ui.js` | `/crawler/072_karriere/ui-kit/goslar-ui.js` |
| `072_karriere` | `/crawler/072_karriere_card.json` | `/crawler/072_karriere/072_karriere_card.json` |
| `072_karriere` | `/crawler/072_jobs.json` | `/crawler/072_karriere/072_jobs.json` |
| `072_karriere` | `/crawler/072_karriere_index.html` | `/crawler/072_karriere/072_karriere_index.html` |
| `072_karriere` | `/crawler/jobs.css` | `/crawler/072_karriere/jobs.css` |
| `072_karriere` | `/crawler/jobs.js` | `/crawler/072_karriere/jobs.js` |
| `073_busflotte` | `/crawler/busflotte/073_busflotte_card.json` | `/crawler/073_busflotte/073_busflotte_card.json` |
| `073_busflotte` | `/crawler/busflotte/073_busflotte_alle.json` | `/crawler/073_busflotte/073_busflotte_alle.json` |
