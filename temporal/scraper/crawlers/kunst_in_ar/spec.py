# crawlers/kunst_in_ar/spec.py
from crawlers.base import SHARED_TASK_QUEUE, BasicCrawlerConfig, CrawlerSpec
from crawlers.kunst_in_ar.workflow import KunstInArrawlerWorkflow
from crawlers.kunst_in_ar.activities import (
    crawl_artists,
    crawl_artist,
    save_artist,
)

SPEC = CrawlerSpec(
    name="017_kunst_in_ar",
    task_queue=SHARED_TASK_QUEUE,
    workflow_class=KunstInArrawlerWorkflow,
    activities=(crawl_artists, crawl_artist, save_artist),
    configs=[BasicCrawlerConfig(id="017_kunst_in_ar", schedule= "0 8 * * *")],
)