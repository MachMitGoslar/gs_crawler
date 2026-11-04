from __future__ import annotations

from dataclasses import dataclass
from .generic.models import GenericCrawlerConfig
from typing import Any,  Callable, Sequence, Type, Union

SHARED_TASK_QUEUE = "crawler-shared"

# Every crawler config type in the app. Add new entry classes here.
@dataclass(frozen=True)
class BasicCrawlerConfig:
    id: str
    schedule: str


CrawlerConfigT = Union[GenericCrawlerConfig, BasicCrawlerConfig]   # extend with Union[...] later

@dataclass(frozen=True, slots=True)
class CrawlerSpec:
    """Declarative description of one crawler.

    - ``configs`` is the list of configurations this crawler should be
      scheduled for (one entry per schedule, not per task queue).
    - ``workflow_class`` must be a ``@workflow.defn``.
    - ``activities`` are the *function* objects decorated with
      ``@activity.defn``. Their names must be unique per task queue.
    - ``task_queue`` is where both the workflow and the activities run.
    """
    name: str
    task_queue: str
    workflow_class: Type
    activities: Sequence[Callable]
    configs: Sequence[CrawlerConfigT]