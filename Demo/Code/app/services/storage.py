import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import get_settings
from app.schemas import WikiCard
from app.utils.slug import sanitize_customer_name, slugify_text, slugify_url


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.data_root = self.settings.data_root_path

    def get_customer_raw_dir(self, customer: str) -> Path:
        return self.data_root / "Raw" / sanitize_customer_name(customer)

    def get_customer_wiki_dir(self, customer: str) -> Path:
        return self.data_root / "Wiki card" / sanitize_customer_name(customer)

    def get_customer_reference_dir(self, customer: str) -> Path:
        return self.data_root / "Reference" / sanitize_customer_name(customer)

    def get_internal_url_md_path(self, customer: str) -> Path:
        return self.get_customer_raw_dir(customer) / "Internal-URL.md"

    def get_blog_dir(self, customer: str) -> Path:
        return self.get_customer_raw_dir(customer) / "blogs"

    def get_blog_md_path(self, customer: str, blog_url: str) -> Path:
        return self.get_blog_dir(customer) / f"{slugify_url(blog_url)}.md"

    def get_wiki_card_path(self, customer: str, title: str) -> Path:
        file_slug = slugify_text(title, max_len=80)
        return self.get_customer_wiki_dir(customer) / f"Wiki-{file_slug}.json"

    def get_excel_report_path(self, customer: str, blog_slug: str, timestamp: str) -> Path:
        return self.get_customer_reference_dir(customer) / f"Recommendations-{blog_slug}-{timestamp}.xlsx"

    def ensure_customer_dirs(self, customer: str) -> list[Path]:
        dirs = [
            self.get_customer_raw_dir(customer),
            self.get_customer_wiki_dir(customer),
            self.get_customer_reference_dir(customer),
            self.get_blog_dir(customer),
        ]
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
        return dirs[:3]

    def _render_internal_urls(self, customer: str, urls: list[str]) -> str:
        last_updated = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        lines = [
            f"# {sanitize_customer_name(customer)} — Internal URLs",
            "",
            f"> Last updated: {last_updated}",
            "",
        ]
        lines.extend(f"- {url}" for url in urls)
        lines.append("")
        return "\n".join(lines)

    def read_internal_urls(self, customer: str) -> list[str]:
        path = self.get_internal_url_md_path(customer)
        if not path.exists():
            return []
        urls: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value.startswith("- "):
                urls.append(value[2:].strip())
        return urls

    def append_internal_urls(self, customer: str, new_urls: list[str]) -> tuple[int, int, int]:
        path = self.get_internal_url_md_path(customer)
        existing = self.read_internal_urls(customer)
        existing_set = set(existing)

        unique_new = [url for url in new_urls if url and url not in existing_set]
        all_urls = existing + unique_new
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self._render_internal_urls(customer, all_urls), encoding="utf-8")
        return len(unique_new), len(new_urls) - len(unique_new), len(all_urls)

    def save_blog_markdown(self, customer: str, blog_url: str, blog_markdown: str) -> Path:
        path = self.get_blog_md_path(customer, blog_url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(blog_markdown, encoding="utf-8")
        return path

    def list_wiki_cards(self, customer: str) -> list[Path]:
        directory = self.get_customer_wiki_dir(customer)
        if not directory.exists():
            return []
        return sorted(directory.glob("Wiki-*.json"))

    def list_wiki_card_titles(self, customer: str) -> list[str]:
        titles: list[str] = []
        for path in self.list_wiki_cards(customer):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                title = (payload.get("Title") or "").strip()
                if title:
                    titles.append(title)
            except Exception:
                continue
        return titles

    def _resolve_card_path_collision(self, path: Path) -> Path:
        if not path.exists():
            return path
        stem = path.stem
        suffix = path.suffix
        index = 2
        while True:
            candidate = path.with_name(f"{stem}-{index}{suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def save_wiki_card(self, customer: str, title: str, card: WikiCard | dict, overwrite: bool = False) -> Path:
        base_path = self.get_wiki_card_path(customer, title)
        base_path.parent.mkdir(parents=True, exist_ok=True)
        if overwrite:
            final_path = base_path
        else:
            final_path = self._resolve_card_path_collision(base_path)

        payload = card.model_dump() if isinstance(card, WikiCard) else card
        final_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return final_path

    def load_wiki_card(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def list_reports(self, customer: str) -> list[Path]:
        directory = self.get_customer_reference_dir(customer)
        if not directory.exists():
            return []
        return sorted(directory.glob("Recommendations-*.xlsx"))

