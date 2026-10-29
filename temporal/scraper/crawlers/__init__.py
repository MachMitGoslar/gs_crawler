from crawlers.seniorenzeitung import (
    CONFIG as SENIOREN_CONFIG,
    SeniorenCrawlerWorkflow,
    save_senioren as senioren_save_senioren,
    crawl_senioren as senioren_crawl_senioren,
)
from crawlers.kunst_in_ar import (
    CONFIG as KUNST_IN_AR_CONFIG,
    KunstInArrawlerWorkflow,
    crawl_artists as kunst_in_ar_crawl_artists, 
    crawl_artist as kunst_in_ar_crawl_artist, 
    save_artist as kunst_in_ar_save_artist,
)
from crawlers.base import CrawlerEntry

CRAWLERS: list[CrawlerEntry] = [
    {
        "config": SENIOREN_CONFIG,
        "workflow_class": SeniorenCrawlerWorkflow,
        "activities": [senioren_save_senioren, senioren_crawl_senioren],
    },
    {
        "config": KUNST_IN_AR_CONFIG,
        "workflow_class": KunstInArrawlerWorkflow,
        "activities": [kunst_in_ar_crawl_artists, kunst_in_ar_crawl_artist, kunst_in_ar_save_artist],
    },
]
