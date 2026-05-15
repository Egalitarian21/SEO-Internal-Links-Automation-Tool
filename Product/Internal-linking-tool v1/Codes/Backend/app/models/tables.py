from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from threading import RLock
from typing import Any
from uuid import uuid4

from app.infra.file_store import LocalFileStore


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def short_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:8]}"


@dataclass
class Project:
    id: str
    name: str
    domain: str
    owner: str
    status: str
    created_at: str
    last_activity_at: str
    health_score: int
    imported_urls: int
    wiki_cards: int
    approved_suggestions: int
    publish_success_rate: int
    description: str


@dataclass
class Article:
    id: str
    project_id: str
    title: str
    url: str
    category: str
    status: str
    imported_at: str
    last_recommendation_at: str | None
    excerpt: str
    paragraphs: list[str]
    existing_links: int


@dataclass
class Card:
    id: str
    project_id: str
    title: str
    page_type: str
    target_url: str
    source_article_id: str | None
    summary: str
    keywords: list[str]
    last_updated_at: str
    status: str


@dataclass
class Violation:
    severity: str
    rule_id: str
    message: str


@dataclass
class RelevanceDetails:
    anchor_target: int
    paragraph_target: int
    continuity: int

    @property
    def total(self) -> float:
        return round((self.anchor_target + self.paragraph_target + self.continuity) / 3, 1)


@dataclass
class Suggestion:
    id: str
    project_id: str
    article_id: str
    anchor_text: str
    context_before: str
    context_after: str
    target_title: str
    target_url: str
    page_type: str
    status: str
    edited_anchor_text: str | None
    relevance: RelevanceDetails
    rule_violations: list[Violation]
    created_at: str


@dataclass
class TaskRecord:
    id: str
    project_id: str
    task_type: str
    status: str
    title: str
    created_at: str
    updated_at: str
    progress: int
    detail: str
    result: dict[str, Any] = field(default_factory=dict)


@dataclass
class PublishJob:
    id: str
    project_id: str
    article_ids: list[str]
    status: str
    blockers: int
    warnings: int
    created_at: str
    updated_at: str
    before_html_snapshot: str
    after_html_snapshot: str
    shopify_response: dict[str, Any] = field(default_factory=dict)


class DemoStore:
    def __init__(self) -> None:
        self.lock = RLock()
        self.file_store = LocalFileStore()
        self.projects: dict[str, Project] = {}
        self.project_clients: dict[str, str] = {}
        self.articles: dict[str, Article] = {}
        self.cards: dict[str, Card] = {}
        self.suggestions: dict[str, Suggestion] = {}
        self.tasks: dict[str, TaskRecord] = {}
        self.publish_jobs: dict[str, PublishJob] = {}
        self.imported_urls: dict[str, list[dict[str, Any]]] = {}
        self.review_logs: dict[str, list[dict[str, Any]]] = {}
        self.load_or_seed()

    def load_or_seed(self) -> None:
        if self.file_store.has_projects():
            self._load_from_payload(self.file_store.load_all())
            return
        self.seed()
        self.persist()

    def seed(self) -> None:
        self.projects.clear()
        self.project_clients.clear()
        self.articles.clear()
        self.cards.clear()
        self.suggestions.clear()
        self.tasks.clear()
        self.publish_jobs.clear()
        self.imported_urls.clear()
        self.review_logs.clear()
        project = Project(
            id="proj_hydra",
            name="Hydra Home Fitness",
            domain="hydrafitness.com",
            owner="SEO Ops",
            status="active",
            created_at=(datetime.utcnow() - timedelta(days=18)).isoformat() + "Z",
            last_activity_at=now_iso(),
            health_score=82,
            imported_urls=6,
            wiki_cards=5,
            approved_suggestions=4,
            publish_success_rate=96,
            description="An ecommerce content program focused on home gym equipment and training guides.",
        )
        self.projects[project.id] = project
        self.project_clients[project.id] = "hydra-home-fitness"

        articles = [
            Article(
                id="art_strength",
                project_id=project.id,
                title="How to Build a Beginner Strength Routine at Home",
                url="https://hydrafitness.com/blogs/training/beginner-strength-routine",
                category="training",
                status="ready",
                imported_at=(datetime.utcnow() - timedelta(days=12)).isoformat() + "Z",
                last_recommendation_at=(datetime.utcnow() - timedelta(hours=8)).isoformat() + "Z",
                excerpt="A beginner-friendly guide to building a strength routine with limited home equipment.",
                paragraphs=[
                    "A beginner strength routine works best when the training plan matches the equipment you already own.",
                    "Most new lifters see the fastest progress when they pair compound lifts with adjustable dumbbells and a stable bench.",
                    "Recovery gets easier when you track volume, keep sessions short, and progress in small steps.",
                ],
                existing_links=2,
            ),
            Article(
                id="art_recovery",
                project_id=project.id,
                title="Recovery Tips for Busy Professionals Who Still Want to Train",
                url="https://hydrafitness.com/blogs/training/recovery-tips-busy-professionals",
                category="recovery",
                status="ready",
                imported_at=(datetime.utcnow() - timedelta(days=10)).isoformat() + "Z",
                last_recommendation_at=None,
                excerpt="Practical recovery advice for lifters training around demanding work schedules.",
                paragraphs=[
                    "Busy professionals need recovery habits that are repeatable, not perfect.",
                    "A short mobility block and lighter accessory work often matter more than adding more intensity.",
                    "If your sleep is inconsistent, reduce training complexity before you reduce consistency.",
                ],
                existing_links=1,
            ),
            Article(
                id="art_setup",
                project_id=project.id,
                title="The Smartest Garage Gym Setup for Small Spaces",
                url="https://hydrafitness.com/blogs/equipment/garage-gym-small-space",
                category="equipment",
                status="needs_review",
                imported_at=(datetime.utcnow() - timedelta(days=6)).isoformat() + "Z",
                last_recommendation_at=(datetime.utcnow() - timedelta(days=1)).isoformat() + "Z",
                excerpt="How to assemble a compact garage gym without wasting budget or floor space.",
                paragraphs=[
                    "A small garage gym should prioritize storage, adjustable equipment, and clear traffic lanes.",
                    "Foldable racks, modular plates, and a bench with vertical storage keep the space usable.",
                    "When the room is tight, every purchase should serve multiple training patterns.",
                ],
                existing_links=3,
            ),
        ]
        for article in articles:
            self.articles[article.id] = article
        self.imported_urls[project.id] = [
            {"url": article.url, "status": "imported", "imported_at": article.imported_at}
            for article in articles
        ]

        cards = [
            Card(
                id="card_adjustable_dumbbells",
                project_id=project.id,
                title="Hydra Adjustable Dumbbells",
                page_type="product",
                target_url="https://hydrafitness.com/products/adjustable-dumbbells",
                source_article_id=None,
                summary="Adjustable dumbbells for home strength progression without taking over the room.",
                keywords=["adjustable dumbbells", "home strength", "compact equipment"],
                last_updated_at=now_iso(),
                status="published",
            ),
            Card(
                id="card_training_bench",
                project_id=project.id,
                title="Hydra Foldable Training Bench",
                page_type="product",
                target_url="https://hydrafitness.com/products/foldable-training-bench",
                source_article_id=None,
                summary="A stable bench that folds away for small-space setups.",
                keywords=["training bench", "foldable bench", "garage gym"],
                last_updated_at=now_iso(),
                status="published",
            ),
            Card(
                id="card_small_space",
                project_id=project.id,
                title="Small Space Strength Training Guide",
                page_type="blog",
                target_url="https://hydrafitness.com/blogs/training/small-space-strength-guide",
                source_article_id="art_setup",
                summary="Planning principles for compact home gym layouts and equipment choices.",
                keywords=["small space gym", "compact gym", "space planning"],
                last_updated_at=now_iso(),
                status="draft",
            ),
            Card(
                id="card_recovery_collection",
                project_id=project.id,
                title="Recovery Collection",
                page_type="collection",
                target_url="https://hydrafitness.com/collections/recovery-tools",
                source_article_id=None,
                summary="Massage tools and mobility accessories for easier recovery.",
                keywords=["recovery", "mobility", "massage tools"],
                last_updated_at=now_iso(),
                status="published",
            ),
            Card(
                id="card_progressive_overload",
                project_id=project.id,
                title="Progressive Overload for Beginners",
                page_type="blog",
                target_url="https://hydrafitness.com/blogs/training/progressive-overload-beginners",
                source_article_id=None,
                summary="A simple framework for progressing volume and intensity without stalling.",
                keywords=["progressive overload", "beginners", "strength routine"],
                last_updated_at=now_iso(),
                status="published",
            ),
        ]
        for card in cards:
            self.cards[card.id] = card

        seeded_suggestions = [
            Suggestion(
                id="sug_001",
                project_id=project.id,
                article_id="art_strength",
                anchor_text="adjustable dumbbells",
                context_before="Most new lifters see the fastest progress when they pair compound lifts with",
                context_after="and a stable bench.",
                target_title="Hydra Adjustable Dumbbells",
                target_url="https://hydrafitness.com/products/adjustable-dumbbells",
                page_type="product",
                status="approved",
                edited_anchor_text=None,
                relevance=RelevanceDetails(anchor_target=95, paragraph_target=91, continuity=89),
                rule_violations=[],
                created_at=(datetime.utcnow() - timedelta(hours=6)).isoformat() + "Z",
            ),
            Suggestion(
                id="sug_002",
                project_id=project.id,
                article_id="art_strength",
                anchor_text="stable bench",
                context_before="Most new lifters see the fastest progress when they pair compound lifts with adjustable dumbbells and a",
                context_after=".",
                target_title="Hydra Foldable Training Bench",
                target_url="https://hydrafitness.com/products/foldable-training-bench",
                page_type="product",
                status="pending",
                edited_anchor_text=None,
                relevance=RelevanceDetails(anchor_target=86, paragraph_target=88, continuity=84),
                rule_violations=[Violation(severity="warning", rule_id="Q-02", message="Article already has 2 commercial links.")],
                created_at=(datetime.utcnow() - timedelta(hours=5)).isoformat() + "Z",
            ),
            Suggestion(
                id="sug_003",
                project_id=project.id,
                article_id="art_setup",
                anchor_text="small garage gym",
                context_before="A",
                context_after="should prioritize storage, adjustable equipment, and clear traffic lanes.",
                target_title="Small Space Strength Training Guide",
                target_url="https://hydrafitness.com/blogs/training/small-space-strength-guide",
                page_type="blog",
                status="pending",
                edited_anchor_text=None,
                relevance=RelevanceDetails(anchor_target=89, paragraph_target=93, continuity=90),
                rule_violations=[Violation(severity="blocker", rule_id="P-01", message="Anchor appears in the opening sentence.")],
                created_at=(datetime.utcnow() - timedelta(hours=4)).isoformat() + "Z",
            ),
            Suggestion(
                id="sug_004",
                project_id=project.id,
                article_id="art_recovery",
                anchor_text="mobility block",
                context_before="A short",
                context_after="and lighter accessory work often matter more than adding more intensity.",
                target_title="Recovery Collection",
                target_url="https://hydrafitness.com/collections/recovery-tools",
                page_type="collection",
                status="approved",
                edited_anchor_text="mobility recovery tools",
                relevance=RelevanceDetails(anchor_target=82, paragraph_target=85, continuity=79),
                rule_violations=[Violation(severity="warning", rule_id="A-05", message="Original anchor text was too generic.")],
                created_at=(datetime.utcnow() - timedelta(hours=3)).isoformat() + "Z",
            ),
        ]
        for suggestion in seeded_suggestions:
            self.suggestions[suggestion.id] = suggestion

        task = TaskRecord(
            id="task_seed_import",
            project_id=project.id,
            task_type="import",
            status="success",
            title="Initial content import",
            created_at=(datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
            updated_at=(datetime.utcnow() - timedelta(days=7)).isoformat() + "Z",
            progress=100,
            detail="6 URLs imported successfully.",
            result={"imported": 6, "failed": 0},
        )
        self.tasks[task.id] = task

        publish_job = PublishJob(
            id="pub_seed_strength",
            project_id=project.id,
            article_ids=["art_strength"],
            status="success",
            blockers=0,
            warnings=1,
            created_at=(datetime.utcnow() - timedelta(days=1)).isoformat() + "Z",
            updated_at=(datetime.utcnow() - timedelta(days=1)).isoformat() + "Z",
            before_html_snapshot="<article><p>Beginner strength routine draft.</p></article>",
            after_html_snapshot="<article><p>Beginner strength routine draft with approved internal links.</p></article>",
        )
        self.publish_jobs[publish_job.id] = publish_job
        self.review_logs[project.id] = []

    def project_list(self) -> list[Project]:
        return list(self.projects.values())

    def persist(self) -> None:
        self.project_clients = self.file_store.save_all(
            projects={key: asdict(value) for key, value in self.projects.items()},
            project_clients=self.project_clients,
            articles={key: asdict(value) for key, value in self.articles.items()},
            cards={key: asdict(value) for key, value in self.cards.items()},
            suggestions={key: asdict(value) for key, value in self.suggestions.items()},
            tasks={key: asdict(value) for key, value in self.tasks.items()},
            publish_jobs={key: asdict(value) for key, value in self.publish_jobs.items()},
            imported_urls=self.imported_urls,
            review_logs=self.review_logs,
        )

    def client_slug(self, project_id: str) -> str:
        if project_id not in self.project_clients:
            project = self.projects[project_id]
            self.project_clients[project_id] = self.file_store.slugify(project.domain or project.name)
        return self.project_clients[project_id]

    def append_review_log(self, project_id: str, entry: dict[str, Any]) -> None:
        self.review_logs.setdefault(project_id, []).append(entry)

    def to_jsonable(self, obj: Any) -> Any:
        if isinstance(obj, list):
            return [self.to_jsonable(item) for item in obj]
        if hasattr(obj, "__dataclass_fields__"):
            data = asdict(obj)
            if isinstance(obj, Suggestion):
                data["relevance"]["total"] = obj.relevance.total
            return data
        return obj

    def _load_from_payload(self, payload: dict[str, Any]) -> None:
        self.project_clients = dict(payload.get("project_clients", {}))
        self.projects = {
            project_id: Project(**self._pick(Project, data))
            for project_id, data in payload.get("projects", {}).items()
        }
        self.articles = {
            article_id: Article(**self._pick(Article, data))
            for article_id, data in payload.get("articles", {}).items()
        }
        self.cards = {
            card_id: Card(**self._pick(Card, data))
            for card_id, data in payload.get("cards", {}).items()
        }
        self.suggestions = {
            suggestion_id: self._suggestion_from_dict(data)
            for suggestion_id, data in payload.get("suggestions", {}).items()
        }
        self.tasks = {
            task_id: TaskRecord(**self._pick(TaskRecord, {**data, "result": data.get("result", {})}))
            for task_id, data in payload.get("tasks", {}).items()
        }
        self.publish_jobs = {
            job_id: PublishJob(**self._pick(PublishJob, data))
            for job_id, data in payload.get("publish_jobs", {}).items()
        }
        self.imported_urls = dict(payload.get("imported_urls", {}))
        self.review_logs = dict(payload.get("review_logs", {}))

    def _suggestion_from_dict(self, data: dict[str, Any]) -> Suggestion:
        relevance = data.get("relevance") or {}
        relevance.pop("total", None)
        violations = data.get("rule_violations") or []
        return Suggestion(
            **self._pick(
                Suggestion,
                {
                    **data,
                    "relevance": RelevanceDetails(**self._pick(RelevanceDetails, relevance)),
                    "rule_violations": [Violation(**self._pick(Violation, violation)) for violation in violations],
                },
            )
        )

    def _pick(self, model: type, data: dict[str, Any]) -> dict[str, Any]:
        return {key: data[key] for key in model.__dataclass_fields__ if key in data}


store = DemoStore()
