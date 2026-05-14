from __future__ import annotations

from app.models.tables import Article, Suggestion, Violation


def evaluate_anchor_rules(article: Article, anchor_text: str, paragraph_index: int) -> list[Violation]:
    violations: list[Violation] = []
    lowered = anchor_text.lower()
    if paragraph_index == 0:
        violations.append(Violation(severity="blocker", rule_id="P-01", message="Anchor appears in the opening paragraph."))
    if any(generic in lowered for generic in ["click here", "learn more", "read more"]):
        violations.append(Violation(severity="blocker", rule_id="A-01", message="Generic anchor text is not allowed."))
    if len(anchor_text.split()) < 2:
        violations.append(Violation(severity="warning", rule_id="A-03", message="Anchor should contain at least 2 words."))
    if article.existing_links >= 2:
        violations.append(Violation(severity="warning", rule_id="Q-02", message="Article already contains multiple links."))
    return violations


def build_publish_checklist(suggestions: list[Suggestion]) -> list[dict[str, str | bool]]:
    blockers = sum(1 for suggestion in suggestions for violation in suggestion.rule_violations if violation.severity == "blocker")
    warnings = sum(1 for suggestion in suggestions for violation in suggestion.rule_violations if violation.severity == "warning")
    return [
        {
            "id": "CL-01",
            "label": "At least one approved suggestion exists",
            "severity": "blocker",
            "passed": bool(suggestions),
            "detail": "Publishing requires approved suggestions for at least one article.",
        },
        {
            "id": "CL-02",
            "label": "No blocker rule violations remain",
            "severity": "blocker",
            "passed": blockers == 0,
            "detail": f"{blockers} blocker issues detected.",
        },
        {
            "id": "CL-03",
            "label": "Warnings reviewed by an editor",
            "severity": "warning",
            "passed": True,
            "detail": f"{warnings} warning issues will ship with audit visibility.",
        },
    ]

