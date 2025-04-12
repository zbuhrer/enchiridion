#!/usr/bin/env python3
from typing import Dict, Optional, List
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from agents import Agent

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Status values for tasks in the queue."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    status: TaskStatus
    result: Optional[Dict] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class TaskQueue:
    """Manages task execution for agents."""

    def __init__(self):
        """Initialize the task queue."""
        self.queue: List[Dict] = []
        self.results: Dict[str, TaskResult] = {}
        self.running: bool = False

    def enqueue(self, agent: Agent, task: str, data: Dict) -> TaskResult:
        """Add a task to the queue."""
        task_id = f"task_{len(self.queue)}"
        task_item = {
            'id': task_id,
            'agent': agent,
            'task': task,
            'data': data,
            'status': TaskStatus.PENDING
        }
        self.queue.append(task_item)

        self.results[task_id] = TaskResult(
            task_id=task_id,
            status=TaskStatus.PENDING
        )

        logger.debug(f"Enqueued task {task_id}")
        return self.results[task_id]

    async def run_all(self) -> None:
        """Execute all tasks in the queue."""
        self.running = True
        try:
            while self.queue and self.running:
                task = self.queue.pop(0)
                await self._execute_task(task)
        except Exception as e:
            logger.error(f"Error in task queue: {str(e)}", exc_info=True)
        finally:
            self.running = False

    async def _execute_task(self, task: Dict) -> None:
        """Execute a single task."""
        task_id = task['id']
        result = self.results[task_id]
        result.start_time = datetime.now()
        result.status = TaskStatus.RUNNING

        try:
            agent_result = task['agent'].call(
                task['task'],
                **task['data']
            )

            result.result = agent_result
            result.status = TaskStatus.COMPLETED

        except Exception as e:
            result.error = str(e)
            result.status = TaskStatus.FAILED
            logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)

        finally:
            result.end_time = datetime.now()

    def cancel(self, task_id: str) -> None:
        """Cancel a pending task."""
        # Remove from queue if pending
        self.queue = [t for t in self.queue if t['id'] != task_id]

        # Update result status
        if task_id in self.results:
            self.results[task_id].status = TaskStatus.CANCELLED
            logger.info(f"Cancelled task {task_id}")

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get the result of a specific task."""
        return self.results.get(task_id)

    def clear(self) -> None:
        """Clear all pending tasks."""
        self.queue = []
        logger.info("Task queue cleared")

    def stop(self) -> None:
        """Stop task execution."""
        self.running = False
        logger.info("Task queue stopped")

    def get_queue_status(self) -> Dict:
        """Get current queue status."""
        return {
            'running': self.running,
            'pending': len(self.queue),
            'completed': len([r for r in self.results.values()
                            if r.status == TaskStatus.COMPLETED]),
            'failed': len([r for r in self.results.values()
                          if r.status == TaskStatus.FAILED])
        }
