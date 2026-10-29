# crawlers/registry_types.py
from typing import Any, Callable, TypedDict

class CrawlerConfig(TypedDict):
    name: str
    task_queue: str
    cron_expressions: list[str]


class CrawlerEntry(TypedDict):
    config: CrawlerConfig
    workflow_class: type             # any @workflow.defn decorated class
    activities: list[Callable[..., Any]]