from __future__ import annotations

from dataclasses import asdict
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


with workflow.unsafe.imports_passed_through():
    from crawlers.generic.activities import (
        fetch_html,
        scrape_entries,
        select_and_post_process,
        save_output
    )
    from crawlers.generic.models import (
        GenericCrawlerConfig,
        ScrapedEntry,
        SingleCard,
        ScrapeResult,
    )


@workflow.defn
class GenericCrawlerWorkflow:
    RETRY = RetryPolicy(
        initial_interval=timedelta(seconds=2),
        backoff_coefficient=2.0,
        maximum_attempts=5,
        non_retryable_error_types=["ValueError"],
    )

    @workflow.run
    async def run(self, cfg: GenericCrawlerConfig) -> dict:
        workflow.logger.info("Starting scraper %s (%s)", cfg.id, cfg.name)

        html: str = await workflow.execute_activity(
            fetch_html,
            cfg.url,
            start_to_close_timeout=timedelta(seconds=45),
            retry_policy=self.RETRY,
        )

        entry_dicts: list[dict] = await workflow.execute_activity(
            scrape_entries,
            args=[cfg, html],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=self.RETRY,
        )

        if not entry_dicts:
            workflow.logger.warning("No entries for %s", cfg.id)
            return asdict(ScrapeResult(
                crawler_id=cfg.id,
                scraped_at=workflow.now(),
                all_entries=[],
                single_entry=None,
            ))

        single_dict: dict | None = await workflow.execute_activity(
            select_and_post_process,
            args=[cfg, entry_dicts],
            start_to_close_timeout=timedelta(seconds=15),
            retry_policy=self.RETRY,
        )

        await workflow.execute_activity(
            save_output,
            args=[cfg, entry_dicts, single_dict],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=self.RETRY,
        )

        result = ScrapeResult(
            crawler_id=cfg.id,
            scraped_at=workflow.now(),
            all_entries=[ScrapedEntry(**e) for e in entry_dicts],
            single_entry=SingleCard(**single_dict) if single_dict else None,
        )
        workflow.logger.info(
            "Finished %s: %d entries", cfg.id, result.entry_count
        )
        return asdict(result)