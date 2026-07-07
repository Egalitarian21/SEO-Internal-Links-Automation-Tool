import re
from dataclasses import dataclass

GENERIC_ANCHORS = {"click here", "read more", "learn more", "this", "here", "more", "link", "了解更多", "点击这里"}


@dataclass
class CandidateDraft:
    article_block_id: object
    anchor_text: str
    context_text: str
    link_type_suggestion: str
    start_offset: int
    end_offset: int
    reason: str
    confidence_score: float


@dataclass
class RuleResult:
    passed: bool
    errors: list[str]
    warnings: list[str]


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+", text))


def validate_anchor_candidate(candidate: CandidateDraft, block, existing_anchor_texts: set[str], block_candidate_count: int) -> RuleResult:
    errors: list[str] = []
    warnings: list[str] = []
    anchor = " ".join(candidate.anchor_text.split())
    content = block.content or ""

    if not anchor:
        errors.append("锚文本不能为空。")
    if block.block_type == "heading":
        errors.append("标题块中不能添加锚文本。")
    if block.is_first_paragraph:
        errors.append("首段不能添加锚文本。")
    if block.has_existing_link:
        errors.append("已有链接的段落不再添加候选锚文本。")
    if anchor.lower() in GENERIC_ANCHORS:
        errors.append("锚文本不能是泛用点击词。")
    if word_count(anchor) < 2:
        errors.append("英文锚文本至少需要 2 个词。")
    if word_count(anchor) > 12:
        errors.append("英文锚文本不能超过 12 个词。")
    if block_candidate_count >= 2:
        errors.append("同一正文块最多保留 2 个候选。")
    if anchor.lower() in existing_anchor_texts:
        errors.append("同一文章中同一锚文本最多保留 1 个候选。")
    if candidate.end_offset <= candidate.start_offset:
        errors.append("end_offset 必须大于 start_offset。")
    elif content[candidate.start_offset : candidate.end_offset] != candidate.anchor_text:
        errors.append("offset 无法精确截取锚文本。")

    return RuleResult(passed=not errors, errors=errors, warnings=warnings)


def check_preview(errors: list[str], warnings: list[str]) -> dict:
    return {"passed": not errors, "errors": errors, "warnings": warnings}
