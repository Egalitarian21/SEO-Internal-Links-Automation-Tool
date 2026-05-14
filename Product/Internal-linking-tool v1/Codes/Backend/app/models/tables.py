from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any
from uuid import uuid4


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


class DemoStore:
    def __init__(self) -> None:
        self.lock = Lock()
        self.projects: dict[str, Project] = {}
        self.articles: dict[str, Article] = {}
        self.cards: dict[str, Card] = {}
        self.suggestions: dict[str, Suggestion] = {}
        self.tasks: dict[str, TaskRecord] = {}
        self.publish_jobs: dict[str, PublishJob] = {}
        self.seed()

    def seed(self) -> None:
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

    def project_list(self) -> list[Project]:
        return list(self.projects.values())

    def to_jsonable(self, obj: Any) -> Any:
        if isinstance(obj, list):
            return [self.to_jsonable(item) for item in obj]
        if hasattr(obj, "__dataclass_fields__"):
            data = asdict(obj)
            if isinstance(obj, Suggestion):
                data["relevance"]["total"] = obj.relevance.total
            return data
        return obj


store = DemoStore()

