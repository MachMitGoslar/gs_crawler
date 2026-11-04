"""Imports every crawler spec and exposes flat, validated views for the
worker bootstrap and the scheduler.

Importing this module performs all config loading. Do it in the worker
bootstrap (before ``Worker(...)`` is constructed) and in the starter — never
inside a workflow.
"""
from __future__ import annotations

from collections import defaultdict
import logging
from typing import Iterable, Mapping

from crawlers.base import CrawlerSpec
from crawlers.generic.spec import SPEC as GENERIC_SPEC
from crawlers.seniorenzeitung.spec import SPEC as SENIOREN_SPEC
from crawlers.kunst_in_ar.spec import SPEC as KUNST_IN_AR_SPEC


SPECS: tuple[CrawlerSpec, ...] = (
    GENERIC_SPEC,
    SENIOREN_SPEC,
    KUNST_IN_AR_SPEC,
)


def _validate_specs(specs: Iterable[CrawlerSpec]) -> None:
    seen_task_queues: dict[str, set[str]] = defaultdict(set)
    for spec in specs:
        for act in spec.activities:
            name = getattr(act, "__name__", None) or getattr(act, "__temporal_activity_definition", None).name # type: ignore
            existing = seen_task_queues[spec.task_queue]
            # Temporal allows duplicate activity names only for identical impls.
            if act.__name__ in {a.__name__ for a in spec.activities if a is not act}:
                raise ValueError(
                    f"Duplicate activity name {name!r} within {spec.name}"
                )
            existing.add(name)
_validate_specs(SPECS)


# ---------------------------------------------------------------------------
# Views consumed by the worker / starter
# ---------------------------------------------------------------------------
def workflows_by_task_queue() -> Mapping[str, list[type]]:
    """Distinct workflow classes per task queue (dedupe by identity)."""
    buckets: dict[str, dict[int, type]] = defaultdict(dict)
    for spec in SPECS:
        buckets[spec.task_queue][id(spec.workflow_class)] = spec.workflow_class
    return {q: list(classes.values()) for q, classes in buckets.items()}


def activities_by_task_queue() -> Mapping[str, list]:
    """All activities per task queue, deduped by identity."""
    buckets: dict[str, dict[int, object]] = defaultdict(dict)
    for spec in SPECS:
        for act in spec.activities:
            buckets[spec.task_queue][id(act)] = act
    return {q: list(acts.values()) for q, acts in buckets.items()}


def schedules() -> Iterable[tuple[str, str, object]]:
    """Yield ``(schedule_id, cron, workflow_input)`` for every configured run.

    Skips configs without a schedule. The workflow_input is the validated
    pydantic config object — safe to pass as the workflow argument.
    """
    for spec in SPECS:
        for cfg in spec.configs:
            cron = getattr(cfg, "schedule", None)
            if not cron:
                logging.warning(f"Warning: {spec.name}/{cfg.id} has no schedule")
                continue
            if spec.name == cfg.id:
                schedule_id = f"gs-crawler-{cfg.id}"
            else:
                schedule_id = f"gs-crawler-{spec.name}-{cfg.id}"

            yield schedule_id, cron, cfg