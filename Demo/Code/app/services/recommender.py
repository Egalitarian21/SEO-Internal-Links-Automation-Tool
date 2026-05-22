import re
import time
from pathlib import Path
from typing import Any

from app.llm.client import LLMClient
from app.schemas import DiscardedItem, RecommendRequest, RecommendResult, Recommendation
from app.services.storage import StorageService
from app.utils.slug import sanitize_customer_name
from app.utils.url_utils import normalize_url


class RecommenderService:
    def __init__(self, storage: StorageService | None = None, llm: LLMClient | None = None) -> None:
        self.storage = storage or StorageService()
        self.llm = llm or LLMClient()

    def _is_in_first_paragraph(self, blog_markdown: str, text: str) -> bool:
        paragraphs = [line.strip() for line in blog_markdown.splitlines() if line.strip()]
        if not paragraphs:
            return False
        first = paragraphs[0]
        return text in first

    def _is_heading_line(self, blog_markdown: str, text: str) -> bool:
        for line in blog_markdown.splitlines():
            cleaned = line.strip()
            if cleaned.startswith("#") and text in cleaned:
                return True
        return False

    def _extract_titles_map(self, customer: str) -> tuple[list[dict[str, Any]], dict[str, Path]]:
        cards: list[dict[str, Any]] = []
        title_to_path: dict[str, Path] = {}
        for path in self.storage.list_wiki_cards(customer):
            try:
                payload = self.storage.load_wiki_card(path)
                title = str(payload.get("Title", "")).strip()
                if title:
                    cards.append(payload)
                    title_to_path[title] = path
            except Exception:
                continue
        return cards, title_to_path

    def _select_source_title(self, request: RecommendRequest) -> str:
        if request.blog_title:
            return request.blog_title
        headings = [line.strip("# ").strip() for line in request.blog_markdown.splitlines() if line.lstrip().startswith("#")]
        if headings:
            return headings[0]
        return "Untitled Blog"

    def _validate_recommendations(
        self,
        blog_markdown: str,
        recommendations: list[Recommendation],
        max_recommendations: int,
    ) -> tuple[list[Recommendation], list[DiscardedItem]]:
        kept: list[Recommendation] = []
        discarded: list[DiscardedItem] = []
        target_seen: set[str] = set()
        for item in recommendations:
            anchor = item.anchor_text.strip()
            if not anchor or anchor not in blog_markdown:
                discarded.append(
                    DiscardedItem(
                        target_url=item.target_url,
                        reason="ANCHOR_NOT_IN_BLOG",
                        details=f"anchor_text={anchor}",
                    )
                )
                continue
            if self._is_in_first_paragraph(blog_markdown, anchor):
                discarded.append(
                    DiscardedItem(
                        target_url=item.target_url,
                        reason="ANCHOR_IN_FIRST_PARAGRAPH",
                        details=anchor,
                    )
                )
                continue
            if self._is_heading_line(blog_markdown, anchor):
                discarded.append(
                    DiscardedItem(
                        target_url=item.target_url,
                        reason="ANCHOR_IN_HEADING",
                        details=anchor,
                    )
                )
                continue
            if item.target_url in target_seen:
                discarded.append(
                    DiscardedItem(
                        target_url=item.target_url,
                        reason="DUPLICATE_TARGET_URL",
                        details=item.target_url,
                    )
                )
                continue
            target_seen.add(item.target_url)
            kept.append(item)
            if len(kept) >= max_recommendations:
                break
        return kept, discarded

    async def recommend(self, request: RecommendRequest) -> RecommendResult:
        begin = time.perf_counter()
        customer = sanitize_customer_name(request.customer)
        source_title = self._select_source_title(request)
        blog_url = normalize_url(request.blog_url)

        cards, _ = self._extract_titles_map(customer)
        library_size = len(cards)
        source_pattern = re.escape(blog_url.rstrip("/"))
        cards = [c for c in cards if not re.match(source_pattern, str(c.get("url", "")).rstrip("/"))]
        card_titles = [str(c.get("Title", "")) for c in cards if str(c.get("Title", "")).strip()]

        matched_titles = await self.llm.filter_card_titles(source_title, request.blog_markdown, card_titles)
        selected_cards = [card for card in cards if str(card.get("Title", "")) in set(matched_titles)]

        llm_recommendations = await self.llm.match_content(
            blog_markdown=request.blog_markdown,
            candidate_cards=selected_cards,
            threshold=request.score_threshold,
            max_recommendations=request.max_recommendations,
        )
        validated, discarded = self._validate_recommendations(
            blog_markdown=request.blog_markdown,
            recommendations=llm_recommendations,
            max_recommendations=request.max_recommendations,
        )
        validated.sort(key=lambda x: x.relevance_score, reverse=True)

        return RecommendResult(
            customer=customer,
            blog_url=blog_url,
            blog_title=request.blog_title,
            candidates_filtered=len(selected_cards),
            recommendations=validated,
            discarded=discarded,
            library_size=library_size,
            elapsed_seconds=round(time.perf_counter() - begin, 3),
        )

