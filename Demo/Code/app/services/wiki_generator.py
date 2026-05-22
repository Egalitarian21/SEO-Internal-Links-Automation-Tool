import asyncio
import time
from typing import Any

from app.config import get_settings
from app.errors import AppError
from app.llm.client import LLMClient
from app.schemas import FailedItem, GenerateRequest, GenerateResult, WikiCard
from app.services.crawler import CrawlerService
from app.services.storage import StorageService
from app.utils.slug import sanitize_customer_name


class WikiGeneratorService:
    def __init__(
        self,
        storage: StorageService | None = None,
        crawler: CrawlerService | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        self.settings = get_settings()
        self.storage = storage or StorageService()
        self.crawler = crawler or CrawlerService()
        self.llm = llm or LLMClient()

    def _existing_urls(self, customer: str) -> set[str]:
        urls: set[str] = set()
        for path in self.storage.list_wiki_cards(customer):
            try:
                payload = self.storage.load_wiki_card(path)
                url = str(payload.get("url", "")).strip()
                if url:
                    urls.add(url)
            except Exception:
                continue
        return urls

    async def _process_one(self, customer: str, url: str, overwrite: bool) -> str:
        attempts = 3
        for idx in range(attempts):
            try:
                crawl = await self.crawler.crawl(url)
                abstract = await self.llm.generate_wiki_abstract(
                    title=crawl["title"],
                    description=crawl["description"],
                    h_hierarchy=crawl["h_hierarchy"],
                    body_text=crawl["body_text"],
                )
                card = WikiCard(
                    customer=customer,
                    url=url,
                    Title=crawl["title"],
                    Description=crawl["description"],
                    H_Hierarchy=crawl["h_hierarchy"],
                    Web_Abstract_AI_Generated=abstract,
                )
                path = self.storage.save_wiki_card(customer, card.Title, card, overwrite=overwrite)
                return path.name
            except Exception:
                if idx + 1 < attempts:
                    await asyncio.sleep(2)
                    continue
                raise

        raise AppError("URL_FETCH_FAILED", f"Failed processing URL: {url}")

    async def generate(self, request: GenerateRequest) -> GenerateResult:
        begin = time.perf_counter()
        customer = sanitize_customer_name(request.customer)
        self.storage.ensure_customer_dirs(customer)

        all_urls = self.storage.read_internal_urls(customer)
        existing_urls = self._existing_urls(customer)
        todo_urls = [u for u in all_urls if not request.only_missing or u not in existing_urls]

        semaphore = asyncio.Semaphore(max(1, self.settings.llm_max_concurrency))
        failed: list[FailedItem] = []
        cards_generated: list[str] = []

        async def worker(url: str) -> None:
            try:
                async with semaphore:
                    file_name = await asyncio.wait_for(
                        self._process_one(customer, url, overwrite=not request.only_missing),
                        timeout=self.settings.crawler_timeout,
                    )
                    cards_generated.append(file_name)
            except asyncio.TimeoutError:
                failed.append(FailedItem(url=url, error_code="URL_FETCH_FAILED", message="Timeout"))
            except AppError as exc:
                failed.append(FailedItem(url=url, error_code=exc.code, message=exc.message))
            except Exception as exc:
                failed.append(FailedItem(url=url, error_code="URL_FETCH_FAILED", message=str(exc)))

        for start in range(0, len(todo_urls), max(1, request.batch_size)):
            chunk = todo_urls[start : start + max(1, request.batch_size)]
            await asyncio.gather(*(worker(url) for url in chunk))

        return GenerateResult(
            customer=customer,
            total_todo=len(todo_urls),
            success=len(cards_generated),
            failed=failed,
            cards_generated=cards_generated,
            elapsed_seconds=round(time.perf_counter() - begin, 3),
        )

