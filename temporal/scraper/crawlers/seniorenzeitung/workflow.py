from datetime import timedelta

from temporalio import workflow

from .activities import crawl_senioren, save_senioren

@workflow.defn
class SeniorenCrawlerWorkflow:
    @workflow.run
    async def run(self):
        result = await workflow.execute_activity(
            crawl_senioren,
            start_to_close_timeout=timedelta(seconds=10),
        )

        return await workflow.execute_activity(
            save_senioren,
            result,
            start_to_close_timeout=timedelta(seconds=10),
        )