"""Periodischer Export der Jobdaten nach /app/output."""

import json
import os
from pathlib import Path

from jobs_logic import build_jobs_payload


OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/app/output"))
OUTPUT_FILE = OUTPUT_DIR / "072_karriere_jobs.json"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_jobs_payload({})
    with OUTPUT_FILE.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, ensure_ascii=False, indent=2)
    print(
        f"Wrote {OUTPUT_FILE} with {payload.get('total_results', 0)} jobs "
        f"and {len(payload.get('errors', []))} source errors"
    )


if __name__ == "__main__":
    main()
