#!/usr/bin/env python3
"""Minimaler Scheduler als Ersatz für den cron-Daemon im Container.

Läuft als PID 1 ohne Root-Rechte, startet Jobs nacheinander als Unterprozess
und schreibt direkt nach stdout/stderr (docker logs).

Konfiguration über Umgebungsvariablen:
  SCHEDULE         Cron-Ausdruck (5 Felder), mehrere mit ';' getrennt, z. B. "0 * * * *"
  SCRIPT           auszuführendes Python-Skript (Standard: script.py)
  RUN_ON_START     "true" (Standard): einmal direkt beim Start ausführen
  SCRIPT_TIMEOUT   Sekunden bis ein hängender Lauf beendet wird (Standard: 1800)

Achtung: Diese Datei existiert identisch in base_images/python_basic_crawler und
base_images/generic_scraper (scripts/check-shared-files.sh prüft das).

Zeiten gelten in der Zeitzone des Containers (UTC), wie bisher bei cron.
Ein Lauf blockiert den nächsten: dauert er länger als das Intervall, wird der
verpasste Termin einmal nachgeholt, nicht mehrfach parallel.
"""
import os
import signal
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from croniter import croniter

DEFAULT_TIMEOUT = 1800

stop = threading.Event()
_current: Optional[subprocess.Popen] = None


def log(message: str) -> None:
    print(f"[scheduler {datetime.now():%Y-%m-%d %H:%M:%S}] {message}", flush=True)


@dataclass
class Job:
    name: str
    schedules: List[str]
    argv: List[str]
    cwd: str = "/app"
    timeout: int = DEFAULT_TIMEOUT
    next_run: Optional[datetime] = field(default=None, init=False)

    def __post_init__(self):
        for expr in self.schedules:
            if len(expr.split()) != 5 or not croniter.is_valid(expr):
                raise ValueError(f"{self.name}: ungültiger Cron-Ausdruck '{expr}'")

    def schedule_next(self, after: datetime) -> None:
        self.next_run = min(croniter(expr, after).get_next(datetime) for expr in self.schedules)


def parse_schedules(value: str) -> List[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def run_job(job: Job) -> None:
    global _current
    log(f"{job.name}: Start")
    started = datetime.now()
    try:
        _current = subprocess.Popen(job.argv, cwd=job.cwd)
        code = _current.wait(timeout=job.timeout)
        log(f"{job.name}: beendet mit Code {code} nach {(datetime.now() - started).seconds}s")
    except subprocess.TimeoutExpired:
        _current.kill()
        _current.wait()
        log(f"{job.name}: nach {job.timeout}s abgebrochen (Timeout)")
    except OSError as e:
        log(f"{job.name}: konnte nicht gestartet werden: {e}")
    finally:
        _current = None


def _shutdown(signum, _frame) -> None:
    log(f"Signal {signum} empfangen, beende")
    stop.set()
    if _current is not None:
        _current.terminate()


def run_forever(jobs: List[Job], run_on_start: bool = True) -> None:
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    if run_on_start:
        for job in jobs:
            if stop.is_set():
                return
            run_job(job)

    now = datetime.now()
    for job in jobs:
        job.schedule_next(now)
        log(f"{job.name}: nächster Lauf {job.next_run:%Y-%m-%d %H:%M} ({'; '.join(job.schedules)})")

    while not stop.is_set():
        job = min(jobs, key=lambda j: j.next_run)
        wait = (job.next_run - datetime.now()).total_seconds()
        if wait > 0:
            # in kurzen Schritten warten, damit Signale und Uhrsprünge zeitnah wirken
            stop.wait(min(wait, 30))
            continue
        run_job(job)
        job.schedule_next(datetime.now())


def main() -> int:
    schedule = os.environ.get("SCHEDULE", "")
    script = os.environ.get("SCRIPT", "script.py")
    try:
        job = Job(
            name=script,
            schedules=parse_schedules(schedule),
            argv=[sys.executable, script],
            timeout=int(os.environ.get("SCRIPT_TIMEOUT", DEFAULT_TIMEOUT)),
        )
        if not job.schedules:
            raise ValueError("SCHEDULE ist nicht gesetzt")
    except ValueError as e:
        log(f"Konfigurationsfehler: {e}")
        return 2

    run_forever([job], run_on_start=os.environ.get("RUN_ON_START", "true").lower() == "true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
