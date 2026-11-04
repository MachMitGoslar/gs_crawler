import asyncio
import logging
import os

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleUpdate,
    ScheduleUpdateInput,
)
from temporalio.contrib.pydantic import pydantic_data_converter

from crawlers.registry import SPECS, schedules, workflows_by_task_queue

logger = logging.getLogger(__name__)


async def reconcile_schedules(client: Client) -> None:
    """Create, update, and delete Temporal schedules to match SPECS."""
    # Build desired schedules keyed by ID
    desired: dict[str, dict] = {}
    for schedule_id, cron, cfg in schedules():
        # Find the spec that owns this config to get workflow class + task queue
        owning_spec = next(s for s in SPECS if cfg in s.configs)
        workflow_class = owning_spec.workflow_class

        desired[schedule_id] = {
            "cron": cron,
            "workflow_class": workflow_class,
            "task_queue": owning_spec.task_queue,
            "cfg": cfg,
        }

    existing_ids: set[str] = set()
    async for sched in await client.list_schedules():
        existing_ids.add(sched.id)

    # Create or update each desired schedule
    for schedule_id, spec in desired.items():
        schedule = Schedule(
            action=ScheduleActionStartWorkflow(
                spec["workflow_class"].run,
                spec["cfg"],
                id=f"gs-crawler-{schedule_id}",
                task_queue=spec["task_queue"],
            ),
            spec=ScheduleSpec(cron_expressions=[spec["cron"]]),
        )

        if schedule_id not in existing_ids:
            logger.info("Creating schedule %s", schedule_id)
            await client.create_schedule(id=schedule_id, schedule=schedule)
        else:
            logger.info("Updating schedule %s", schedule_id)

            async def updater(input: ScheduleUpdateInput) -> ScheduleUpdate:
                # Replace action + spec with our desired versions, preserve state
                return ScheduleUpdate(
                    schedule=Schedule(
                        action=schedule.action,
                        spec=schedule.spec,
                        policy=input.description.schedule.policy,
                        state=input.description.schedule.state,
                    )
                )

            handle = client.get_schedule_handle(schedule_id)
            await handle.update(updater)

    # Delete schedules that exist but aren't in our desired set
    # Only touch schedules matching our naming convention to avoid
    # clobbering schedules created by other systems.
    for existing_id in existing_ids - set(desired.keys()):
        # Adjust the prefix to match your naming scheme
        if not existing_id.startswith(("gs-crawler")):
            continue
        logger.warning("Deleting stale schedule %s", existing_id)
        handle = client.get_schedule_handle(existing_id)
        await handle.delete()


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    client = await Client.connect(
        os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"),
        data_converter=pydantic_data_converter,
    )
    await reconcile_schedules(client)


if __name__ == "__main__":
    asyncio.run(main())