from datetime import timedelta
import random

from temporalio import workflow

from .activities import crawl_artists, crawl_artist, save_artist

@workflow.defn
class KunstInArrawlerWorkflow:
    @workflow.run
    async def run(self):
        artists = await workflow.execute_activity(
            crawl_artists,
            start_to_close_timeout=timedelta(seconds=10),
        )

        if not artists:
            workflow.logger.info("❌ Keine Künstler gefunden")
            return

        artist = workflow.random().choice(artists)
        artist_details = await workflow.execute_activity(
            crawl_artist,
            artist,
            start_to_close_timeout=timedelta(seconds=10),

        )

        await workflow.execute_activity(
            save_artist,
            artist_details,
            start_to_close_timeout=timedelta(seconds=10),
        )