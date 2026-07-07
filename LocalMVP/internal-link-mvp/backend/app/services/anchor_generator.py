import re
from collections import defaultdict

from app.services.rule_engine import CandidateDraft, validate_anchor_candidate

COMMERCIAL_WORDS = {"buy", "choose", "best", "review", "product", "products", "collection", "shop", "price", "type", "option"}


def suggest_link_type(anchor_text: str, context_text: str) -> str:
    haystack = f"{anchor_text} {context_text}".lower()
    if any(word in haystack.split() for word in COMMERCIAL_WORDS):
        return "collection"
    if re.search(r"\b(model|series|sku|[a-z]+[- ]?\d{2,})\b", haystack):
        return "product"
    return "blog"


def build_phrases(page) -> list[str]:
    phrases: list[str] = []
    for value in [page.keyword, page.title, page.h1]:
        if not value:
            continue
        cleaned = " ".join(str(value).split())
        words = cleaned.split()
        if 2 <= len(words) <= 6:
            phrases.append(cleaned)
        if len(words) > 6:
            for size in range(2, 7):
                for index in range(0, len(words) - size + 1):
                    phrase = " ".join(words[index : index + size])
                    phrases.append(phrase)
    seen: set[str] = set()
    ordered: list[str] = []
    for phrase in sorted(phrases, key=len, reverse=True):
        key = phrase.lower()
        if key not in seen:
            seen.add(key)
            ordered.append(phrase)
    return ordered


def generate_candidate_drafts(blocks, target_pages) -> list[CandidateDraft]:
    drafts: list[CandidateDraft] = []
    existing_texts: set[str] = set()
    block_counts = defaultdict(int)

    phrase_pool: list[str] = []
    for page in target_pages:
        phrase_pool.extend(build_phrases(page))

    phrase_pool = sorted(set(phrase_pool), key=len, reverse=True)

    for block in blocks:
        if block.block_type == "heading" or block.is_first_paragraph or block.has_existing_link:
            continue

        content = block.content or ""
        for phrase in phrase_pool:
            match = re.search(re.escape(phrase), content, re.I)
            if not match:
                continue
            anchor_text = content[match.start() : match.end()]
            draft = CandidateDraft(
                article_block_id=block.id,
                anchor_text=anchor_text,
                context_text=content,
                link_type_suggestion=suggest_link_type(anchor_text, content),
                start_offset=match.start(),
                end_offset=match.end(),
                reason="命中目标页面 keyword、title 或 h1 中的 2-6 词短语，并通过硬性规则过滤。",
                confidence_score=82,
            )
            result = validate_anchor_candidate(draft, block, existing_texts, block_counts[block.id])
            if result.passed:
                drafts.append(draft)
                existing_texts.add(anchor_text.lower())
                block_counts[block.id] += 1
            if block_counts[block.id] >= 2:
                break

    return drafts
