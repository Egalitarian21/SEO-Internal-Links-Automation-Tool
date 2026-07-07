from dataclasses import dataclass
from uuid import uuid4

from app.services.insertion import generate_preview_html


@dataclass
class Block:
    id: object
    content: str
    raw_html: str


@dataclass
class Candidate:
    id: object
    anchor_text: str
    start_offset: int
    end_offset: int


def test_approve_decision_inserts_anchor():
    html = "<p>The right glider recliner helps parents.</p>"
    block = Block(uuid4(), "The right glider recliner helps parents.", html)
    candidate = Candidate(uuid4(), "glider recliner", 10, 25)

    preview, rule_check = generate_preview_html(html, [{"block": block, "candidate": candidate, "target_url": "https://example.com/target"}])

    assert rule_check["passed"] is True
    assert '<a href="https://example.com/target">glider recliner</a>' in preview


def test_reject_anchor_has_no_insertion_when_no_insertions_passed():
    html = "<p>The right glider recliner helps parents.</p>"

    preview, rule_check = generate_preview_html(html, [])

    assert rule_check["passed"] is True
    assert preview == html


def test_offset_invalid_reports_error():
    html = "<p>The right glider recliner helps parents.</p>"
    block = Block(uuid4(), "The right glider recliner helps parents.", html)
    candidate = Candidate(uuid4(), "glider recliner", 0, 15)

    _, rule_check = generate_preview_html(html, [{"block": block, "candidate": candidate, "target_url": "https://example.com/target"}])

    assert rule_check["passed"] is False
    assert rule_check["errors"]


def test_existing_target_url_skips_duplicate():
    html = '<p>Already links <a href="https://example.com/target">target</a>. The right glider recliner helps.</p>'
    block = Block(uuid4(), "Already links target. The right glider recliner helps.", html)
    candidate = Candidate(uuid4(), "glider recliner", 32, 47)

    preview, rule_check = generate_preview_html(html, [{"block": block, "candidate": candidate, "target_url": "https://example.com/target"}])

    assert rule_check["passed"] is True
    assert rule_check["warnings"]
    assert preview == html
