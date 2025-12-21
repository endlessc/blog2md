import asyncio
from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskInfo(BaseModel):
    id: str
    url: str
    status: TaskStatus
    logs: list[str] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class TaskManager:
    def __init__(self, concurrency: int = 2):
        self.queue = asyncio.Queue()
        self.tasks: Dict[str, TaskInfo] = {}
        self.concurrency = concurrency
        self.workers = []
        self.running = False

    def add_task(self, url: str) -> str:
        task_id = str(uuid.uuid4())
        task = TaskInfo(
            id=task_id,
            url=url,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        self.tasks[task_id] = task
        self.queue.put_nowait(task_id)
        return task_id

    async def start_workers(self, process_func, loop, broadcast_func):
        if self.running:
            return
        self.running = True
        for _ in range(self.concurrency):
            worker = asyncio.create_task(self._worker(process_func, loop, broadcast_func))
            self.workers.append(worker)

    async def _worker(self, process_func, loop, broadcast_func):
        while self.running:
            try:
                task_id = await self.queue.get()
                task = self.tasks.get(task_id)
                if not task:
                    self.queue.task_done()
                    continue

                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                await broadcast_func(f"UPDATE:{task_id}:{task.status}")

                def log_callback(msg):
                    task.logs.append(msg)
                    # Optional: Broadcast real-time logs if needed, but might be too noisy for all clients
                    # For now, we rely on polling or specific subscription, or just broadcast everything
                    # Let's broadcast logs for the specific task
                    future = asyncio.run_coroutine_threadsafe(
                        broadcast_func(f"LOG:{task_id}:{msg}"), loop
                    )
                    try:
                        future.result(timeout=5)
                    except Exception:
                        pass

                try:
                    # Run the synchronous process_url in a thread pool
                    from fastapi.concurrency import run_in_threadpool
                    await run_in_threadpool(process_func, task.url, "output", log_callback)
                    
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    await broadcast_func(f"UPDATE:{task_id}:{task.status}")
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.completed_at = datetime.now()
                    await broadcast_func(f"UPDATE:{task_id}:{task.status}")
                finally:
                    self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker error: {e}")

    def update_concurrency(self, new_concurrency: int):
        # Dynamic resizing is complex, for now simplest is to restart workers or just accept new value for future starts
        # But for this MVP, we might just set it and let user restart server if needed, 
        # or implement a basic version where we add/remove workers.
        # Let's keep it simple: restart workers.
        pass

