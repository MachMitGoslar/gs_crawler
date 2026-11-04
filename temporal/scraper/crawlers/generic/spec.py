from __future__ import annotations

import os
from pathlib import Path

from crawlers.base import CrawlerSpec
from crawlers.generic.config_loader import load_all_configs
from crawlers.generic.workflow import GenericCrawlerWorkflow
from crawlers.generic.activities import (
    fetch_html,
    save_output,
    scrape_entries,
    select_and_post_process,
)
from crawlers.generic.models import GenericCrawlerConfig

def _default_config_dir() -> Path:
    here = Path(__file__).resolve().parent
    return Path(os.environ.get("CONFIG_DIR", here / "configs"))


def _load_configs() -> list[GenericCrawlerConfig]:
    return list(load_all_configs(_default_config_dir()).values())


SPEC = CrawlerSpec(
    name="generic",
    task_queue="crawler-generic",
    workflow_class=GenericCrawlerWorkflow,
    activities=(fetch_html, scrape_entries, select_and_post_process, save_output),
    configs=_load_configs(),
)