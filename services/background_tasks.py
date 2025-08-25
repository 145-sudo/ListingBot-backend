import asyncio
import logging
from typing import Callable, Coroutine, Any
from functools import partial

class BackgroundTaskManager:
    def __init__(self):
        self._tasks = set()

    async def start_task(self, func: Callable[..., Coroutine[Any, Any, None]], interval: int, *args, **kwargs):
        """Start a background task that runs periodically"""
        async def wrapped_task():
            while True:
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(*args, **kwargs)
                    else:
                        await asyncio.to_thread(func, *args, **kwargs)
                    await asyncio.sleep(interval)
                except Exception as e:
                    logging.error(f"Error in background task {func.__name__}: {e}")
                    await asyncio.sleep(10)  # Wait before retrying

        task = asyncio.create_task(wrapped_task())
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def get_running_tasks(self):
        """Get all currently running background tasks"""
        return list(self._tasks)

    async def stop_all_tasks(self):
        """Stop all running background tasks"""
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

task_manager = BackgroundTaskManager()
