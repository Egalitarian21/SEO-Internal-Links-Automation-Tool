from __future__ import annotations

import time

from app.infra.embedding_client import embedding_client
from app.infra.task_bus import task_bus
from app.infra.vector_repo import vector_repo
from app.models.tables import RelevanceDetails, Suggestion, now_iso, short_id, store
from app.services.rules_service import evaluate_anchor_rules


class RecommendService:
    def start_generation(self, project_id: str, article_id: str) -> str:
        task = task_bus.submit(
            project_id=project_id,
            task_type="recommend",
            title="Generate internal link suggestions",
            payload={"article_id": article_id},
            runner=self._run_generation,
        )
        return task.id

    def _run_generation(self, task_id: str, payload: dict[str, str]) -> dict[str, int]:
        article_id = payload["article_id"]
        article = store.articles[article_id]
        created = 0
        for index, paragraph in enumerate(article.paragraphs):
            time.sleep(0.4)
            candidates = vector_repo.find_candidates(article.project_id, paragraph)
            if not candidates:
                continue
            card = candidates[0]
            words = paragraph.split()
            anchor_text = " ".join(words[2:5]) if len(words) >= 5 else " ".join(words[:2])
            violations = evaluate_anchor_rules(article, anchor_text, index)
            relevance = RelevanceDetails(
                anchor_target=embedding_client.score_similarity(anchor_text, card.title),
                paragraph_target=embedding_client.score_similarity(paragraph, card.summary),
                continuity=max(70, 94 - index * 5),
            )
            suggestion = Suggestion(
                id=short_id("sug"),
                project_id=article.project_id,
                article_id=article_id,
                anchor_text=anchor_text,
                context_before=" ".join(words[:2]),
                context_after=" ".join(words[5:10]),
                target_title=card.title,
                target_url=card.target_url,
                page_type=card.page_type,
                status="pending",
                edited_anchor_text=None,
                relevance=relevance,
                rule_violations=violations,
                created_at=now_iso(),
            )
            with store.lock:
                store.suggestions[suggestion.id] = suggestion
                store.articles[article_id].last_recommendation_at = now_iso()
                store.projects[article.project_id].last_activity_at = now_iso()
                store.persist()
            created += 1
            task_bus.update(task_id, progress=min(95, int(((index + 1) / len(article.paragraphs)) * 100)), detail=f"Scored paragraph {index + 1}")
        return {"created": created}

    def list_suggestions(self, project_id: str, article_id: str | None = None, review_only: bool = False) -> list[dict]:
        suggestions = [item for item in store.suggestions.values() if item.project_id == project_id]
        if article_id:
            suggestions = [item for item in suggestions if item.article_id == article_id]
        if review_only:
            suggestions = [item for item in suggestions if item.status in {"pending", "approved", "rejected"}]
        suggestions.sort(
            key=lambda item: (
                any(v.severity == "blocker" for v in item.rule_violations),
                item.relevance.total,
            ),
            reverse=True,
        )
        return [store.to_jsonable(item) for item in suggestions]

    def reverse_links(self, project_id: str) -> list[dict[str, str | int]]:
        summary: dict[str, int] = {}
        titles: dict[str, str] = {}
        for suggestion in store.suggestions.values():
            if suggestion.project_id != project_id or suggestion.status != "approved":
                continue
            summary[suggestion.target_url] = summary.get(suggestion.target_url, 0) + 1
            titles[suggestion.target_url] = suggestion.target_title
        ranked = sorted(summary.items(), key=lambda item: item[1], reverse=True)
        return [{"target_url": url, "target_title": titles[url], "approved_links": count} for url, count in ranked]


recommend_service = RecommendService()
