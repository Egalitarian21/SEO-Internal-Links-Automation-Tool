from app.schemas import IntakeRequest, IntakeResult
from app.services.storage import StorageService
from app.utils.slug import sanitize_customer_name
from app.utils.url_utils import is_probably_url, normalize_url


class URLIntakeService:
    def __init__(self, storage: StorageService | None = None) -> None:
        self.storage = storage or StorageService()

    def intake(self, request: IntakeRequest) -> IntakeResult:
        customer = sanitize_customer_name(request.customer)
        dirs_ready = [str(path) for path in self.storage.ensure_customer_dirs(customer)]

        candidates: list[str] = []
        for raw_url in request.urls or []:
            url = normalize_url(raw_url)
            if url and is_probably_url(url):
                candidates.append(url)

        if request.blog_url:
            blog_url = normalize_url(request.blog_url)
            if blog_url and is_probably_url(blog_url):
                candidates.append(blog_url)

        deduped_candidates = list(dict.fromkeys(candidates))
        new_added, duplicates, total = self.storage.append_internal_urls(customer, deduped_candidates)

        blog_md_saved = False
        if request.blog_url and request.blog_markdown:
            self.storage.save_blog_markdown(customer, request.blog_url, request.blog_markdown)
            blog_md_saved = True

        return IntakeResult(
            customer=customer,
            new_urls_added=new_added,
            duplicate_urls_skipped=duplicates,
            total_urls_in_db=total,
            blog_md_saved=blog_md_saved,
            dirs_ready=dirs_ready,
        )

