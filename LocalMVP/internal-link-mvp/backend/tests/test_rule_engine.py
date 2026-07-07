from dataclasses import dataclass
from uuid import uuid4

from app.services.rule_engine import CandidateDraft, validate_anchor_candidate


@dataclass
class Block:
    id: object
    content: str
    block_type: str = "paragraph"
    is_first_paragraph: bool = False
    has_existing_link: bool = False


def make_candidate(anchor_text="glider recliner", start=10, end=25):
    return CandidateDraft(
        article_block_id=uuid4(),
        anchor_text=anchor_text,
        context_text=f"The right {anchor_text} helps parents.",
        link_type_suggestion="collection",
        start_offset=start,
        end_offset=end,
        reason="测试",
        confidence_score=80,
    )


def test_first_paragraph_candidate_filtered():
    block = Block(id=uuid4(), content="The right glider recliner helps parents.", is_first_paragraph=True)
    result = validate_anchor_candidate(make_candidate(), block, set(), 0)

    assert result.passed is False


def test_heading_candidate_filtered():
    block = Block(id=uuid4(), content="The right glider recliner helps parents.", block_type="heading")
    result = validate_anchor_candidate(make_candidate(), block, set(), 0)

    assert result.passed is False


def test_click_here_filtered():
    block = Block(id=uuid4(), content="Please click here for details.")
    result = validate_anchor_candidate(make_candidate("click here", 7, 17), block, set(), 0)

    assert result.passed is False


def test_single_word_filtered():
    block = Block(id=uuid4(), content="The chair is soft.")
    result = validate_anchor_candidate(make_candidate("chair", 4, 9), block, set(), 0)

    assert result.passed is False


def test_offset_mismatch_filtered():
    block = Block(id=uuid4(), content="The right glider recliner helps parents.")
    result = validate_anchor_candidate(make_candidate("glider recliner", 0, 15), block, set(), 0)

    assert result.passed is False
