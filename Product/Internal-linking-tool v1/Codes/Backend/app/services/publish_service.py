from __future__ import annotations

import time

from app.infra.shopify_client import shopify_client
from app.infra.task_bus import task_bus
from app.models.tables import PublishJob, now_iso, short_id, store
from app.services.rules_service import build_publish_checklist


class PublishService:
    def checklist(self, project_id: str, article_ids: list[str] | None = None) -> dict:
        approved = [
            suggestion
            for suggestion in store.suggestions.values()
            if suggestion.project_id == project_id and suggestion.status == "approved"
        ]
        if article_ids:
            approved = [suggestion for suggestion in approved if suggestion.article_id in article_ids]
        items = build_publish_checklist(approved)
        blockers = sum(1 for item in items if item["severity"] == "blocker" and not item["passed"])
        warnings = sum(1 for item in items if item["severity"] == "warning" and not item["passed"])
        return {"items": items, "blockers": blockers, "warnings": warnings}

    def start_publish(self, project_id: str, article_ids: list[str]) -> str:
        task = task_bus.submit(
            project_id=project_id,
            task_type="publish",
            title="Run pre-publish checks and publish",
            payload={"article_ids": article_ids, "project_id": project_id},
            runner=self._run_publish,
        )
        return task.id

    def _run_publish(self, task_id: str, payload: dict[str, list[str] | str]) -> dict[str, str]:
        project_id = str(payload["project_id"])
        article_ids = payload["article_ids"]
        checklist = self.checklist(project_id, article_ids)  # type: ignore[arg-type]
        task_bus.update(task_id, progress=35, detail="Checklist evaluated.")
        if checklist["blockers"] > 0:
            raise RuntimeError("Publish blocked by checklist violations.")
        time.sleep(0.6)
        job = PublishJob(
            id=short_id("pub"),
            project_id=project_id,
            article_ids=article_ids,
            status="success",
            blockers=checklist["blockers"],
            warnings=checklist["warnings"],
            created_at=now_iso(),
            updated_at=now_iso(),
            before_html_snapshot="<article>before_html snapshot</article>",
            after_html_snapshot="<article>after_html snapshot with internal links</article>",
        )
        with store.lock:
            store.publish_jobs[job.id] = job
            project = store.projects[project_id]
            project.last_activity_at = now_iso()
            store.persist()
        task_bus.update(task_id, progress=80, detail="Publishing to Shopify demo client.")
        result = shopify_client.publish(article_ids)
        with store.lock:
            store.publish_jobs[job.id].shopify_response = result
            store.publish_jobs[job.id].updated_at = now_iso()
            store.projects[project_id].last_activity_at = now_iso()
            store.persist()
        return {"publish_job_id": job.id, **result}

    def rollback(self, job_id: str) -> dict:
        with store.lock:
            job = store.publish_jobs[job_id]
            job.status = "rolled_back"
            job.updated_at = now_iso()
            store.projects[job.project_id].last_activity_at = now_iso()
            store.persist()
        return shopify_client.rollback(job_id)


publish_service = PublishService()
