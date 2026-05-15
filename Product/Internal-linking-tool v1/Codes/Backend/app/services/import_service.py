from __future__ import annotations

import time
from urllib.parse import urlparse

from app.infra.task_bus import task_bus
from app.models.tables import Article, Card, now_iso, short_id, store


class ImportService:
    def start_import(self, project_id: str, urls: list[str]) -> str:
        task = task_bus.submit(
            project_id=project_id,
            task_type="import",
            title=f"Import {len(urls)} URLs",
            payload={"urls": urls, "project_id": project_id},
            runner=self._run_import,
        )
        return task.id

    def _run_import(self, task_id: str, payload: dict[str, list[str] | str]) -> dict[str, int]:
        urls = payload["urls"]
        project_id = str(payload["project_id"])
        imported = 0
        failed = 0
        for index, url in enumerate(urls, start=1):  # type: ignore[arg-type]
            time.sleep(0.35)
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                failed += 1
                with store.lock:
                    store.imported_urls.setdefault(project_id, []).append(
                        {"url": url, "status": "failed", "imported_at": now_iso(), "error": "Invalid URL"}
                    )
                    store.persist()
                task_bus.update(task_id, progress=int(index / len(urls) * 100), detail=f"Skipped invalid URL: {url}")
                continue

            article_id = short_id("art")
            title_stub = parsed.path.strip("/").replace("-", " ").title() or "Imported Article"
            article = Article(
                id=article_id,
                project_id=project_id,
                title=title_stub,
                url=url,
                category="imported",
                status="ready",
                imported_at=now_iso(),
                last_recommendation_at=None,
                excerpt=f"Imported draft generated from {parsed.netloc}.",
                paragraphs=[
                    f"{title_stub} is now part of the internal linking workspace.",
                    "This demo article was generated from a batch import and is ready for recommendation review.",
                    "Editors can now attach wiki cards, generate suggestions, and push approved links to publish.",
                ],
                existing_links=0,
            )
            card = Card(
                id=short_id("card"),
                project_id=project_id,
                title=f"{title_stub} Wiki Card",
                page_type="blog",
                target_url=url,
                source_article_id=article_id,
                summary=f"Auto-generated knowledge card for {title_stub}.",
                keywords=title_stub.lower().split()[:3] or ["imported", "content"],
                last_updated_at=now_iso(),
                status="draft",
            )
            with store.lock:
                store.articles[article.id] = article
                store.cards[card.id] = card
                store.imported_urls.setdefault(project_id, []).append(
                    {"url": url, "status": "imported", "imported_at": article.imported_at}
                )
                project = store.projects[project_id]
                project.imported_urls += 1
                project.wiki_cards += 1
                project.last_activity_at = now_iso()
                store.persist()
            imported += 1
            task_bus.update(task_id, progress=int(index / len(urls) * 100), detail=f"Imported {title_stub}")
        return {"imported": imported, "failed": failed}


import_service = ImportService()
