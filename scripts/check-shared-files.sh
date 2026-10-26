#!/bin/sh
# Prüft, dass Dateien, die in mehreren Base-Images identisch vorliegen müssen, nicht auseinanderlaufen.
cd "$(dirname "$0")/.." || exit 1
status=0
for f in scheduler.py; do
    if ! cmp -s "base_images/python_basic_crawler/$f" "base_images/generic_scraper/$f"; then
        echo "❌ $f weicht zwischen python_basic_crawler und generic_scraper ab"
        status=1
    fi
done
[ $status -eq 0 ] && echo "✅ Gemeinsame Dateien identisch"
exit $status
