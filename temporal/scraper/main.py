# main.py
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import os
from temporalio.client import Client
from temporalio.worker import Worker

from crawlers import CRAWLERS
from runtime.scheduler import ensure_schedules


async def main() -> None:
    host = os.getenv("TEMPORAL_HOST", "localhost:7233")
    namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
    logging.basicConfig(level=logging.DEBUG)

    logging.debug(f"Connecting to temporal instance at {host}")
    client = await Client.connect(host, namespace=namespace)

    # Ensure schedules exist (safe on every restart)
    await ensure_schedules(client, CRAWLERS)

    # Start one Worker per task queue, all inside a single process
    workers = []
    for crawler in CRAWLERS:
        workers.append(
            Worker(
                client,
                task_queue=crawler["config"]["task_queue"],
                workflows=[crawler["workflow_class"]],
                activities=crawler["activities"],
            )
        )

    print(f"🚀 Starting {len(workers)} worker(s) for {len(CRAWLERS)} crawler(s)")
    # Run all workers concurrently in this single container
    await asyncio.gather(*(w.run() for w in workers))


if __name__ == "__main__":
    asyncio.run(main())