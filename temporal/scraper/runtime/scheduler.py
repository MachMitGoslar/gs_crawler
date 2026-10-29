# runtime/scheduler.py
import asyncio
from datetime import timedelta
from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleSpec,
    ScheduleState,
    ScheduleAlreadyRunningError,
)

from crawlers.base import CrawlerEntry

async def ensure_schedules(client: Client, crawler_configs: list[CrawlerEntry]):
    """
    Iterate through all crawler configurations to ensure their scheduled tasks exist.
    Using create_schedule and catching AlreadyRunningError for simple idempotency logic.
    """
    for config in crawler_configs:
        schedule_id = f"schedule-{config['config']['name']}"
        
        # Specify the Workflow to be started by the schedule
        action = ScheduleActionStartWorkflow(
            config["workflow_class"].run,  # Reference the run method of the Workflow class
            id=f"{config['config']['name']}-scheduled-run",
            task_queue=config['config']["task_queue"],
            # Can pass an initial input like {"url": "..."}
        )
        
        # Define the timing rules
        spec = ScheduleSpec(
            cron_expressions=config['config']["cron_expressions"],
            jitter=timedelta(seconds=30)  # Recommended to add jitter to avoid thundering herd
        )
        
        # Create the schedule
        try:
            await client.create_schedule(
                schedule_id,
                Schedule(
                    action=action,
                    spec=spec,
                    state=ScheduleState(note=f"Scheduled crawler: {config['config']['name']}"),
                )
            )
            print(f"Schedule created: {schedule_id}")
        except ScheduleAlreadyRunningError:
            # If the schedule already exists, it means this is a restart. Subsequent Worker restarts will not interrupt running schedules.
            # If you need to update the schedule time, you can call client.get_schedule_handle(schedule_id).update(...)
            print(f"Schedule already exists, skipping creation: {schedule_id}")