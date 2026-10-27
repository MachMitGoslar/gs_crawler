#!/bin/sh
# Legt für jeden Crawler aus crawlers.yaml den Ausgabeordner httpdocs/crawler/<id> an.
#
# Muss als Hosting-User laufen (nicht als root) und VOR `docker compose up`, weil Docker
# fehlende Bind-Mount-Ordner sonst als root anlegt und die Container dort nicht schreiben können.
#
# Usage:  ./scripts/init-output-dirs.sh [Zielordner]   (Standard: httpdocs/crawler)
cd "$(dirname "$0")/.." || exit 1
ROOT="${1:-httpdocs/crawler}"

if [ "$(id -u)" = "0" ]; then
    echo "❌ Bitte nicht als root ausführen, sonst gehören die Ordner root." >&2
    exit 1
fi

ids=$(sed -n 's/^  - id: "\([^"]*\)".*/\1/p' crawlers.yaml)
if [ -z "$ids" ]; then
    echo "❌ Keine Crawler in crawlers.yaml gefunden" >&2
    exit 1
fi

for id in $ids; do
    mkdir -p "$ROOT/$id"
done
echo "✅ $(echo "$ids" | wc -l | tr -d ' ') Ordner in $ROOT bereit (Besitzer: $(id -un))"
