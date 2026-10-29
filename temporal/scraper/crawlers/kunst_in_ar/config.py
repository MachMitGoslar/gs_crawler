from crawlers.base import CrawlerConfig

CONFIG: CrawlerConfig = {
    "name": "kunst_in_ar",
    "task_queue": "crawler-kunst-in-ar",
    "cron_expressions": ["0 8 * * *"],
}