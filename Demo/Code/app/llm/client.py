import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.errors import AppError
from app.schemas import Recommendation

try:
    from openai import AsyncOpenAI
except Exception:  # pragma: no cover - fallback when package unavailable
    AsyncOpenAI = None


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.prompt_dir = Path(__file__).resolve().parent / "prompts"
        self.log_root = self.settings.log_root_path
        self.log_root.mkdir(parents=True, exist_ok=True)
        self.calls_log_dir = self.log_root / "llm_calls"
        self.calls_log_dir.mkdir(parents=True, exist_ok=True)
        self.use_mock = self.settings.llm_use_mock or AsyncOpenAI is None
        self.client = None
        if not self.use_mock:
            self.client = AsyncOpenAI(
                api_key=self.settings.llm_api_key,
                base_url=self.settings.llm_base_url,
                timeout=self.settings.llm_timeout,
            )

    def _prompt(self, file_name: str) -> str:
        return (self.prompt_dir / file_name).read_text(encoding="utf-8")

    def _extract_json(self, text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            lines = text.splitlines()
            if lines and lines[0].lower().startswith("json"):
                lines = lines[1:]
            text = "\n".join(lines)
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end >= 0:
            text = text[start : end + 1]
        return json.loads(text)

    def _write_call_log(self, payload: dict[str, Any]) -> None:
        date_key = datetime.now().strftime("%Y-%m-%d")
        log_path = self.calls_log_dir / f"{date_key}.jsonl"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    async def _call(self, node: str, prompt: str, retries: int = 1) -> dict[str, Any]:
        for attempt in range(1, retries + 2):
            begin = time.perf_counter()
            status = "ok"
            response_text = ""
            try:
                if self.use_mock:
                    raise AppError("MOCK_MODE", "Mock mode")
                assert self.client is not None
                response = await self.client.chat.completions.create(
                    model=self.settings.llm_model,
                    temperature=0.2,
                    max_tokens=self.settings.llm_max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                )
                response_text = response.choices[0].message.content or "{}"
                payload = self._extract_json(response_text)
                self._write_call_log(
                    {
                        "node": node,
                        "status": "ok",
                        "attempt": attempt,
                        "elapsed_ms": round((time.perf_counter() - begin) * 1000, 2),
                        "prompt": prompt,
                        "response": payload,
                    }
                )
                return payload
            except AppError:
                status = "mock"
                response_text = "{}"
                payload = {}
                self._write_call_log(
                    {
                        "node": node,
                        "status": status,
                        "attempt": attempt,
                        "elapsed_ms": round((time.perf_counter() - begin) * 1000, 2),
                        "prompt": prompt,
                        "response": response_text,
                    }
                )
                return payload
            except json.JSONDecodeError as exc:
                status = "invalid_json"
                if attempt > retries:
                    self._write_call_log(
                        {
                            "node": node,
                            "status": status,
                            "attempt": attempt,
                            "elapsed_ms": round((time.perf_counter() - begin) * 1000, 2),
                            "prompt": prompt,
                            "response": response_text,
                            "error": str(exc),
                        }
                    )
                    raise AppError("LLM_INVALID_JSON", f"Invalid JSON response: {exc}") from exc
            except Exception as exc:
                status = "error"
                if attempt > retries:
                    self._write_call_log(
                        {
                            "node": node,
                            "status": status,
                            "attempt": attempt,
                            "elapsed_ms": round((time.perf_counter() - begin) * 1000, 2),
                            "prompt": prompt,
                            "response": response_text,
                            "error": str(exc),
                        }
                    )
                    raise AppError("LLM_TIMEOUT", str(exc)) from exc
            self._write_call_log(
                {
                    "node": node,
                    "status": status,
                    "attempt": attempt,
                    "elapsed_ms": round((time.perf_counter() - begin) * 1000, 2),
                    "prompt": prompt,
                    "response": response_text,
                }
            )

        raise AppError("LLM_TIMEOUT", "Unknown LLM error")

    def _mock_generate_abstract(
        self,
        title: str,
        description: str,
        h_hierarchy: list[dict[str, Any]],
        body_text: str,
    ) -> str:
        sections = ", ".join(node.get("text", "") for node in h_hierarchy[:4] if node.get("text"))
        short_body = body_text[:220].replace("\n", " ").strip()
        return (
            f"This page focuses on '{title}'. {description[:120]} "
            f"Key sections include: {sections}. Content sample: {short_body}"
        )[:500]

    async def generate_wiki_abstract(
        self,
        title: str,
        description: str,
        h_hierarchy: list[dict[str, Any]],
        body_text: str,
    ) -> str:
        if self.use_mock:
            abstract = self._mock_generate_abstract(title, description, h_hierarchy, body_text)
            self._write_call_log(
                {
                    "node": "wiki_generation",
                    "status": "mock",
                    "prompt": {"title": title},
                    "response": {"Web_Abstract_AI_Generated": abstract},
                }
            )
            return abstract

        prompt = self._prompt("wiki_generation.md").format(
            title=title,
            description=description,
            h_hierarchy_formatted=json.dumps(h_hierarchy, ensure_ascii=False),
            body_text_excerpt=body_text[:4000],
        )
        payload = await self._call("wiki_generation", prompt, retries=1)
        text = str(payload.get("Web_Abstract_AI_Generated", "")).strip()
        if not text:
            raise AppError("LLM_INVALID_JSON", "Empty Web_Abstract_AI_Generated.")
        return text

    async def filter_card_titles(self, blog_title: str, blog_markdown: str, card_titles: list[str]) -> list[str]:
        if self.use_mock:
            blog_text = f"{blog_title} {blog_markdown}".lower()
            ranked = sorted(
                card_titles,
                key=lambda t: sum(1 for token in t.lower().split() if token in blog_text),
                reverse=True,
            )
            return [title for title in ranked if title][:30]

        numbered = "\n".join(f"{idx + 1}. {title}" for idx, title in enumerate(card_titles))
        prompt = self._prompt("card_filter.md").format(
            blog_title=blog_title or "",
            blog_excerpt=(blog_markdown or "")[:1500],
            card_titles_numbered=numbered,
        )
        payload = await self._call("card_filter", prompt, retries=1)
        matched = payload.get("matched_titles", [])
        if not isinstance(matched, list):
            raise AppError("LLM_INVALID_JSON", "matched_titles is not a list.")
        matched_set = {str(item).strip() for item in matched if str(item).strip()}
        return [title for title in card_titles if title in matched_set][:30]

    def _mock_find_anchor(self, paragraph: str) -> str:
        words = [w.strip(".,:;!?()[]{}\"'") for w in paragraph.split()]
        words = [w for w in words if len(w) > 3]
        if len(words) >= 2:
            return f"{words[0]} {words[1]}"
        if words:
            return words[0]
        return ""

    async def match_content(
        self,
        blog_markdown: str,
        candidate_cards: list[dict[str, Any]],
        threshold: float,
        max_recommendations: int,
    ) -> list[Recommendation]:
        if self.use_mock:
            paragraphs = [line.strip() for line in blog_markdown.splitlines() if line.strip() and not line.lstrip().startswith("#")]
            if len(paragraphs) <= 1:
                return []
            candidates = paragraphs[1:]
            recommendations: list[Recommendation] = []
            for card in candidate_cards:
                if len(recommendations) >= max_recommendations:
                    break
                paragraph = candidates[len(recommendations) % len(candidates)]
                anchor = self._mock_find_anchor(paragraph)
                if not anchor:
                    continue
                recommendations.append(
                    Recommendation(
                        target_url=str(card.get("url", "")),
                        target_title=str(card.get("Title", "")),
                        anchor_text=anchor,
                        insert_paragraph=paragraph,
                        relevance_score=max(0.6, threshold),
                        reason="Mock semantic match based on paragraph keywords.",
                    )
                )
            return recommendations

        prompt = self._prompt("content_match.md").format(
            blog_markdown=blog_markdown,
            candidate_cards_formatted=json.dumps(candidate_cards, ensure_ascii=False),
            threshold=threshold,
            max_recommendations=max_recommendations,
        )
        payload = await self._call("content_match", prompt, retries=1)
        recs = payload.get("recommendations", [])
        if not isinstance(recs, list):
            raise AppError("LLM_INVALID_JSON", "recommendations is not a list.")
        parsed: list[Recommendation] = []
        for item in recs:
            parsed.append(Recommendation.model_validate(item))
        return parsed

