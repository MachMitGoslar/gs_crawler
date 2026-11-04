# crawlers/seniorenzeitung/spec.py
from crawlers.base import SHARED_TASK_QUEUE, BasicCrawlerConfig, CrawlerSpec
from crawlers.seniorenzeitung.workflow import SeniorenCrawlerWorkflow
from crawlers.seniorenzeitung.activities import (
    save_senioren,
    crawl_senioren,
)

SPEC = CrawlerSpec(
    name="001_seniorenzeitung",
    task_queue=SHARED_TASK_QUEUE,
    workflow_class=SeniorenCrawlerWorkflow,
    activities=(crawl_senioren, save_senioren),
    configs=[BasicCrawlerConfig(id="001_seniorenzeitung", schedule= "0 2 * * *")],
)