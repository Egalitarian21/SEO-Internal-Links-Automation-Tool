from __future__ import annotations

import json
import os
import re
import struct
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4


class FileStoreError(RuntimeError):
    pass


class LocalFileStore:
    """JSON/NPY backed storage for the demo runtime cache."""

    def __init__(self) -> None:
        product_dir = Path(__file__).resolve().parents[5]
        self.root = product_dir / "Data Base" / "data"
        self.projects_path = self.root / "projects.json"
        self.lock = Lock()

    def ensure_base(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.projects_path.exists():
            self._atomic_write_json(self.projects_path, {"projects": []})

    def has_projects(self) -> bool:
        self.ensure_base()
        data = self._read_json(self.projects_path, default={"projects": []})
        return bool(self._project_items(data))

    def load_all(self) -> dict[str, Any]:
        self.ensure_base()
        project_items = self._project_items(self._read_json(self.projects_path, default={"projects": []}))
        payload: dict[str, Any] = {
            "projects": {},
            "project_clients": {},
            "articles": {},
            "cards": {},
            "suggestions": {},
            "tasks": {},
            "publish_jobs": {},
            "imported_urls": {},
            "review_logs": {},
        }
        for item in project_items:
            project = dict(item)
            project_id = str(project["id"])
            client_slug = str(project.pop("client_slug", "") or self.slugify(project.get("domain") or project.get("name") or project_id))
            payload["project_clients"][project_id] = client_slug
            payload["projects"][project_id] = self._project_from_summary(project)
            client_dir = self._ensure_client_structure(client_slug)
            meta = self._read_json(client_dir / "_meta.json", default={})
            payload["tasks"].update({task["id"]: task for task in meta.get("tasks", []) if "id" in task})
            payload["imported_urls"][project_id] = self._read_json(client_dir / "urls" / "imported_urls.json", default=[])
            payload["review_logs"][project_id] = self._read_json(client_dir / "reviews" / "review_log.json", default=[])

            article_index = self._read_json(client_dir / "articles" / "_index.json", default={"articles": {}})
            for article_id, entry in self._index_entries(article_index, "articles").items():
                file_name = entry.get("file") or f"{article_id}.json"
                article = self._read_json(client_dir / "articles" / file_name, default=None)
                if article:
                    payload["articles"][article_id] = self._article_from_file(article, project_id)

            card_index = self._read_json(client_dir / "wiki_cards" / "_index.json", default={"cards": {}})
            for card_id, entry in self._index_entries(card_index, "cards").items():
                file_name = entry.get("file") or f"{card_id}.json"
                card = self._read_json(client_dir / "wiki_cards" / file_name, default=None)
                if card:
                    payload["cards"][card_id] = self._card_from_file(card, project_id, "blog")

            targets = self._read_json(client_dir / "link_targets" / "targets.json", default=[])
            for target in targets:
                card_id = target.get("id") or target.get("target_id")
                if card_id:
                    payload["cards"][card_id] = self._card_from_file(target, project_id, target.get("page_type", "product"))

            suggestion_files = self._suggestion_files(client_dir)
            for file_path in suggestion_files:
                suggestions = self._read_json(file_path, default=[])
                if isinstance(suggestions, dict):
                    suggestions = suggestions.get("suggestions", [])
                for suggestion in suggestions:
                    if "id" in suggestion:
                        payload["suggestions"][suggestion["id"]] = self._suggestion_from_file(suggestion, project_id)

            publish_index = self._read_json(client_dir / "publish" / "_index.json", default={"jobs": {}})
            jobs = publish_index.get("jobs", {})
            if isinstance(jobs, list):
                jobs = {job["id"]: job for job in jobs if "id" in job}
            for job_id, job in jobs.items():
                payload["publish_jobs"][job_id] = self._publish_job_from_file(job, project_id)
        return payload

    def save_all(
        self,
        *,
        projects: dict[str, dict[str, Any]],
        project_clients: dict[str, str],
        articles: dict[str, dict[str, Any]],
        cards: dict[str, dict[str, Any]],
        suggestions: dict[str, dict[str, Any]],
        tasks: dict[str, dict[str, Any]],
        publish_jobs: dict[str, dict[str, Any]],
        imported_urls: dict[str, list[dict[str, Any]]],
        review_logs: dict[str, list[dict[str, Any]]],
    ) -> dict[str, str]:
        with self.lock:
            self.ensure_base()
            used_slugs: set[str] = set()
            resolved_clients: dict[str, str] = {}
            project_summaries = []
            for project_id, project in projects.items():
                mapped_slug = project_clients.get(project_id)
                client_slug = mapped_slug or self.slugify(project.get("domain") or project.get("name") or project_id)
                if client_slug in used_slugs or not mapped_slug:
                    client_slug = self._unique_slug(client_slug, used_slugs)
                resolved_clients[project_id] = client_slug
                used_slugs.add(client_slug)
                client_dir = self._ensure_client_structure(client_slug)
                project_summaries.append(self._project_summary(project, client_slug))
                self._write_client(
                    client_dir=client_dir,
                    project=project,
                    project_id=project_id,
                    articles={k: v for k, v in articles.items() if v.get("project_id") == project_id},
                    cards={k: v for k, v in cards.items() if v.get("project_id") == project_id},
                    suggestions={k: v for k, v in suggestions.items() if v.get("project_id") == project_id},
                    tasks={k: v for k, v in tasks.items() if v.get("project_id") == project_id},
                    publish_jobs={k: v for k, v in publish_jobs.items() if v.get("project_id") == project_id},
                    imported_urls=imported_urls.get(project_id, []),
                    review_logs=review_logs.get(project_id, []),
                )
            project_summaries.sort(key=lambda item: item.get("last_activity_at", ""), reverse=True)
            self._atomic_write_json(self.projects_path, {"projects": project_summaries})
            return resolved_clients

    def append_review_log(self, client_slug: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
        with self.lock:
            client_dir = self._ensure_client_structure(client_slug)
            log_path = client_dir / "reviews" / "review_log.json"
            log = self._read_json(log_path, default=[])
            log.append(entry)
            self._atomic_write_json(log_path, log)
            return log

    @staticmethod
    def slugify(value: Any) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", str(value).lower()).strip("-")
        return slug or "client"

    def _write_client(
        self,
        *,
        client_dir: Path,
        project: dict[str, Any],
        project_id: str,
        articles: dict[str, dict[str, Any]],
        cards: dict[str, dict[str, Any]],
        suggestions: dict[str, dict[str, Any]],
        tasks: dict[str, dict[str, Any]],
        publish_jobs: dict[str, dict[str, Any]],
        imported_urls: list[dict[str, Any]],
        review_logs: list[dict[str, Any]],
    ) -> None:
        meta = {
            "project_id": project_id,
            "name": project.get("name"),
            "shopify_domain": project.get("domain"),
            "owner": project.get("owner"),
            "status": project.get("status"),
            "created_at": project.get("created_at"),
            "updated_at": project.get("last_activity_at"),
            "config": {
                "shopify_domain": project.get("domain"),
                "shopify_token_ref": None,
                "token_storage_note": "Reserved for env vars or a secret manager; do not hard-code tokens in code.",
            },
            "tasks": list(tasks.values()),
        }
        self._atomic_write_json(client_dir / "_meta.json", meta)
        self._atomic_write_json(client_dir / "urls" / "imported_urls.json", imported_urls)
        self._write_articles(client_dir, articles)
        self._write_cards(client_dir, cards)
        self._write_suggestions(client_dir, suggestions)
        self._write_publish_jobs(client_dir, publish_jobs)
        self._atomic_write_json(client_dir / "reviews" / "review_log.json", review_logs)

    def _write_articles(self, client_dir: Path, articles: dict[str, dict[str, Any]]) -> None:
        index: dict[str, Any] = {"articles": {}}
        for article_id, article in articles.items():
            file_name = f"{self._safe_filename(article_id)}.json"
            article_doc = {
                **article,
                "body_html": article.get("body_html") or "".join(f"<p>{paragraph}</p>" for paragraph in article.get("paragraphs", [])),
                "body_text": article.get("body_text") or "\n\n".join(article.get("paragraphs", [])),
                "meta": article.get("meta") or {"category": article.get("category")},
                "headings": article.get("headings") or [],
                "paragraphs": article.get("paragraphs") or [],
                "existing_links": article.get("existing_links", 0),
            }
            self._atomic_write_json(client_dir / "articles" / file_name, article_doc)
            index["articles"][article_id] = {
                "file": file_name,
                "title": article.get("title"),
                "url": article.get("url"),
                "status": article.get("status"),
                "imported_at": article.get("imported_at"),
                "last_recommendation_at": article.get("last_recommendation_at"),
            }
        self._atomic_write_json(client_dir / "articles" / "_index.json", index)

    def _write_cards(self, client_dir: Path, cards: dict[str, dict[str, Any]]) -> None:
        wiki_index: dict[str, Any] = {"cards": {}}
        targets = []
        wiki_ids = []
        target_ids = []
        for card_id, card in cards.items():
            page_type = card.get("page_type")
            if page_type == "blog":
                file_name = f"{self._safe_filename(card_id)}.json"
                card_doc = {
                    **card,
                    "topics": card.get("topics") or card.get("keywords", []),
                    "entities": card.get("entities") or [],
                    "semantic_tags": card.get("semantic_tags") or card.get("keywords", []),
                    "linkable_phrases": card.get("linkable_phrases") or card.get("keywords", []),
                }
                self._atomic_write_json(client_dir / "wiki_cards" / file_name, card_doc)
                wiki_index["cards"][card_id] = {
                    "file": file_name,
                    "article_id": card.get("source_article_id"),
                    "title": card.get("title"),
                    "status": card.get("status"),
                    "updated_at": card.get("last_updated_at"),
                }
                wiki_ids.append(card_id)
            else:
                targets.append(
                    {
                        "id": card_id,
                        "target_id": card_id,
                        "project_id": card.get("project_id"),
                        "url": card.get("target_url"),
                        "target_url": card.get("target_url"),
                        "meta_title": card.get("title"),
                        "title": card.get("title"),
                        "page_type": page_type,
                        "summary": card.get("summary"),
                        "keywords": card.get("keywords", []),
                        "status": card.get("status"),
                        "last_updated_at": card.get("last_updated_at"),
                        "source_article_id": card.get("source_article_id"),
                    }
                )
                target_ids.append(card_id)
        self._atomic_write_json(client_dir / "wiki_cards" / "_index.json", wiki_index)
        self._atomic_write_json(client_dir / "link_targets" / "targets.json", targets)
        self._write_embeddings(client_dir, wiki_ids, target_ids)

    def _write_suggestions(self, client_dir: Path, suggestions: dict[str, dict[str, Any]]) -> None:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for suggestion in suggestions.values():
            grouped.setdefault(str(suggestion.get("article_id")), []).append(suggestion)
        index: dict[str, Any] = {"sources": {}}
        for article_id, items in grouped.items():
            file_name = f"{self._safe_filename(article_id)}.json"
            self._atomic_write_json(client_dir / "suggestions" / file_name, items)
            index["sources"][article_id] = {
                "file": file_name,
                "total": len(items),
                "pending": sum(1 for item in items if item.get("status") == "pending"),
                "approved": sum(1 for item in items if item.get("status") == "approved"),
                "rejected": sum(1 for item in items if item.get("status") == "rejected"),
                "updated_at": max((item.get("created_at", "") for item in items), default=""),
            }
        self._atomic_write_json(client_dir / "suggestions" / "_index.json", index)

    def _write_publish_jobs(self, client_dir: Path, publish_jobs: dict[str, dict[str, Any]]) -> None:
        index: dict[str, Any] = {"jobs": {}, "articles": {}}
        by_article: dict[str, list[dict[str, Any]]] = {}
        for job_id, job in publish_jobs.items():
            index["jobs"][job_id] = job
            for article_id in job.get("article_ids", []):
                by_article.setdefault(article_id, []).append(job)
                index["articles"][article_id] = {
                    "file": f"{self._safe_filename(article_id)}.json",
                    "latest_job_id": job_id,
                    "status": job.get("status"),
                    "updated_at": job.get("updated_at"),
                }
        for article_id, jobs in by_article.items():
            latest = sorted(jobs, key=lambda item: item.get("updated_at", ""))[-1]
            doc = {
                "article_id": article_id,
                "publish_job_id": latest.get("id"),
                "before_html": latest.get("before_html_snapshot"),
                "after_html": latest.get("after_html_snapshot"),
                "checklist": {
                    "blockers": latest.get("blockers", 0),
                    "warnings": latest.get("warnings", 0),
                },
                "shopify_response": latest.get("shopify_response", {}),
                "rollback": {"available": True, "job_id": latest.get("id")},
                "time": latest.get("updated_at"),
                "history": jobs,
            }
            self._atomic_write_json(client_dir / "publish" / f"{self._safe_filename(article_id)}.json", doc)
        self._atomic_write_json(client_dir / "publish" / "_index.json", index)

    def _write_embeddings(self, client_dir: Path, wiki_ids: list[str], target_ids: list[str]) -> None:
        embeddings_dir = client_dir / "embeddings"
        self._atomic_write_json_if_changed(embeddings_dir / "wiki_cards_ids.json", wiki_ids)
        self._atomic_write_json_if_changed(embeddings_dir / "link_targets_ids.json", target_ids)
        self._atomic_write_bytes_if_changed(embeddings_dir / "wiki_cards.npy", self._empty_npy(rows=len(wiki_ids)))
        self._atomic_write_bytes_if_changed(embeddings_dir / "link_targets.npy", self._empty_npy(rows=len(target_ids)))

    def _ensure_client_structure(self, client_slug: str) -> Path:
        client_dir = self.root / client_slug
        for relative in [
            "",
            "urls",
            "articles",
            "wiki_cards",
            "link_targets",
            "embeddings",
            "suggestions",
            "reviews",
            "publish",
        ]:
            (client_dir / relative).mkdir(parents=True, exist_ok=True)
        defaults = {
            "_meta.json": {},
            "urls/imported_urls.json": [],
            "articles/_index.json": {"articles": {}},
            "wiki_cards/_index.json": {"cards": {}},
            "link_targets/targets.json": [],
            "suggestions/_index.json": {"sources": {}},
            "reviews/review_log.json": [],
            "publish/_index.json": {"jobs": {}, "articles": {}},
            "embeddings/wiki_cards_ids.json": [],
            "embeddings/link_targets_ids.json": [],
        }
        for relative, default in defaults.items():
            path = client_dir / relative
            if not path.exists():
                self._atomic_write_json(path, default)
        for relative in ["embeddings/wiki_cards.npy", "embeddings/link_targets.npy"]:
            path = client_dir / relative
            if not path.exists():
                self._atomic_write_bytes(path, self._empty_npy())
        return client_dir

    def _suggestion_files(self, client_dir: Path) -> list[Path]:
        index = self._read_json(client_dir / "suggestions" / "_index.json", default={"sources": {}})
        files = []
        sources = index.get("sources", {})
        if isinstance(sources, dict):
            for source_id, entry in sources.items():
                files.append(client_dir / "suggestions" / (entry.get("file") or f"{source_id}.json"))
        if not files:
            files = [path for path in (client_dir / "suggestions").glob("*.json") if path.name != "_index.json"]
        return files

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as exc:
            raise FileStoreError(f"Invalid JSON in {path}: {exc}") from exc

    def _atomic_write_json(self, path: Path, data: Any) -> None:
        encoded = json.dumps(data, ensure_ascii=False, indent=2)
        self._atomic_write_bytes(path, encoded.encode("utf-8"))

    def _atomic_write_json_if_changed(self, path: Path, data: Any) -> None:
        encoded = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self._atomic_write_bytes_if_changed(path, encoded)

    def _atomic_write_bytes(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_name(f"{path.name}.tmp.{uuid4().hex}")
        with temp_path.open("wb") as handle:
            handle.write(data)
        try:
            os.replace(temp_path, path)
        except OSError:
            temp_path.unlink(missing_ok=True)
            raise

    def _atomic_write_bytes_if_changed(self, path: Path, data: bytes) -> None:
        if path.exists() and path.read_bytes() == data:
            return
        self._atomic_write_bytes(path, data)

    def _empty_npy(self, rows: int = 0) -> bytes:
        header = str({"descr": "<f4", "fortran_order": False, "shape": (rows, 0)})
        header = header.replace('"', "'")
        header_bytes = (header + " ").encode("latin1")
        padding = 16 - ((10 + len(header_bytes) + 1) % 16)
        header_bytes += b" " * padding + b"\n"
        return b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header_bytes)) + header_bytes

    def _project_items(self, data: Any) -> list[dict[str, Any]]:
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            projects = data.get("projects", [])
            if isinstance(projects, dict):
                return list(projects.values())
            return projects
        return []

    def _index_entries(self, data: Any, key: str) -> dict[str, Any]:
        if not isinstance(data, dict):
            return {}
        items = data.get(key, data)
        if isinstance(items, list):
            return {item["id"]: item for item in items if "id" in item}
        return items if isinstance(items, dict) else {}

    def _project_summary(self, project: dict[str, Any], client_slug: str) -> dict[str, Any]:
        return {
            **project,
            "client_slug": client_slug,
            "last_updated_at": project.get("last_activity_at"),
        }

    def _project_from_summary(self, project: dict[str, Any]) -> dict[str, Any]:
        project.pop("last_updated_at", None)
        return project

    def _article_from_file(self, article: dict[str, Any], project_id: str) -> dict[str, Any]:
        article = dict(article)
        article.setdefault("project_id", project_id)
        article.setdefault("category", article.get("meta", {}).get("category", "imported"))
        article.setdefault("status", "ready")
        article.setdefault("last_recommendation_at", None)
        article.setdefault("excerpt", (article.get("body_text") or "")[:180])
        article.setdefault("paragraphs", [])
        article.setdefault("existing_links", 0)
        return {key: article.get(key) for key in ["id", "project_id", "title", "url", "category", "status", "imported_at", "last_recommendation_at", "excerpt", "paragraphs", "existing_links"]}

    def _card_from_file(self, card: dict[str, Any], project_id: str, default_page_type: str) -> dict[str, Any]:
        card = dict(card)
        return {
            "id": card.get("id") or card.get("target_id"),
            "project_id": card.get("project_id") or project_id,
            "title": card.get("title") or card.get("meta_title"),
            "page_type": card.get("page_type") or default_page_type,
            "target_url": card.get("target_url") or card.get("url"),
            "source_article_id": card.get("source_article_id"),
            "summary": card.get("summary") or "",
            "keywords": card.get("keywords") or card.get("topics") or card.get("semantic_tags") or [],
            "last_updated_at": card.get("last_updated_at") or card.get("updated_at"),
            "status": card.get("status") or "draft",
        }

    def _suggestion_from_file(self, suggestion: dict[str, Any], project_id: str) -> dict[str, Any]:
        suggestion = dict(suggestion)
        suggestion.setdefault("project_id", project_id)
        relevance = suggestion.get("relevance") or {}
        relevance.pop("total", None)
        suggestion["relevance"] = relevance
        suggestion.setdefault("rule_violations", [])
        return suggestion

    def _publish_job_from_file(self, job: dict[str, Any], project_id: str) -> dict[str, Any]:
        job = dict(job)
        job.setdefault("project_id", project_id)
        job.setdefault("shopify_response", {})
        return job

    def _unique_slug(self, base: str, used: set[str]) -> str:
        slug = base
        counter = 2
        while slug in used or (self.root / slug).exists():
            slug = f"{base}-{counter}"
            counter += 1
        return slug

    def _safe_filename(self, value: str) -> str:
        return self.slugify(value).replace("-", "_")
