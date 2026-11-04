import asyncio
import os
import logging

from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from crawlers.registry import activities_by_task_queue, workflows_by_task_queue


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    client = await Client.connect(
        os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
        data_converter=pydantic_data_converter,
    )

    workflows_by_queue = workflows_by_task_queue()
    activities_by_queue = activities_by_task_queue()

    workers = [
        Worker(
            client,
            task_queue=queue,
            workflows=workflows_by_queue.get(queue, []),
            activities=activities_by_queue.get(queue, []),
        )
        for queue in set(workflows_by_queue) | set(activities_by_queue)
    ]
        

    logger.info(f"🚀 Starting {len(workers)} worker(s)")
    await asyncio.gather(*(w.run() for w in workers))


if __name__ == "__main__":
    asyncio.run(main())