#!/usr/bin/env python3
"""Startet den Scheduler für alle Crawler-Configs in CONFIG_DIR (ersetzt cron)."""
import os
import sys

from config_loader import load_all_configs
from scheduler import Job, log, parse_schedules, run_forever


def main() -> int:
    configs = load_all_configs()
    if not configs:
        log("Keine Configs gefunden, nichts zu tun")
        return 1

    try:
        jobs = [
            Job(
                name=crawler_id,
                schedules=parse_schedules(config["schedule"]),
                argv=[sys.executable, "scraper.py", config["_path"]],
            )
            for crawler_id, config in configs.items()
        ]
    except ValueError as e:
        log(f"Konfigurationsfehler: {e}")
        return 2

    run_forever(jobs, run_on_start=os.environ.get("RUN_ON_START", "true").lower() == "true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
