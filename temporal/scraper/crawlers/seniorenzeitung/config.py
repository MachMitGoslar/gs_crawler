from crawlers.base import CrawlerConfig

CONFIG: CrawlerConfig = {
    "name": "seniorenzeitung",
    "task_queue": "crawler-seniorenzeitung",
    "cron_expressions": ["0 2 * * *"],
}