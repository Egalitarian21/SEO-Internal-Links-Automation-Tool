from __future__ import annotations

from datetime import datetime
from threading import Thread
from typing import Any, Callable

from app.models.tables import TaskRecord, now_iso, short_id, store


Runner = Callable[[str, dict[str, Any]], dict[str, Any] | None]


class TaskBus:
    def submit(self, project_id: str, task_type: str, title: str, payload: dict[str, Any], runner: Runner) -> TaskRecord:
        task = TaskRecord(
            id=short_id("task"),
            project_id=project_id,
            task_type=task_type,
            status="queued",
            title=title,
            created_at=now_iso(),
            updated_at=now_iso(),
            progress=0,
            detail="Queued for execution.",
        )
        with store.lock:
            store.tasks[task.id] = task
        thread = Thread(target=self._execute, args=(task.id, payload, runner), daemon=True)
        thread.start()
        return task

    def update(self, task_id: str, *, status: str | None = None, progress: int | None = None, detail: str | None = None, result: dict[str, Any] | None = None) -> None:
        with store.lock:
            task = store.tasks[task_id]
            if status is not None:
                task.status = status
            if progress is not None:
                task.progress = progress
            if detail is not None:
                task.detail = detail
            if result is not None:
                task.result = result
            task.updated_at = datetime.utcnow().isoformat() + "Z"

    def _execute(self, task_id: str, payload: dict[str, Any], runner: Runner) -> None:
        self.update(task_id, status="running", progress=10, detail="Worker started.")
        try:
            result = runner(task_id, payload) or {}
            self.update(task_id, status="success", progress=100, detail="Task completed.", result=result)
        except Exception as exc:  # pragma: no cover - demo safety
            self.update(task_id, status="failed", progress=100, detail=str(exc), result={"error": str(exc)})


task_bus = TaskBus()

