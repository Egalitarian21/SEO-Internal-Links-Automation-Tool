from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import (
    AnchorCandidate,
    AppSetting,
    ArticleBlock,
    AuditLog,
    InsertionPreview,
    LinkDecision,
    LinkRecommendation,
    Page,
    Snapshot,
)
from app.db.session import get_db
from app.schemas.anchor import AnchorGenerateResponse, AnchorListResponse
from app.schemas.decision import DecisionsRequest, DecisionsResponse
from app.schemas.preview import LocalWriteRequest, LocalWriteResponse, PreviewResponse
from app.schemas.recommendation import AnchorRecommendationGroup, RecommendationGenerateResponse, RecommendationListResponse, RecommendationOut
from app.schemas.settings import LlmSettings
from app.services.anchor_generator import generate_candidate_drafts
from app.services.canonical import content_hash
from app.services.insertion import generate_preview_html
from app.services.recommender import rank_recommendations
from app.services.snapshot import apply_local_write

router = APIRouter(prefix="/internal-linking", tags=["内链流程"])


@router.post("/{source_page_id}/anchor-candidates/generate", response_model=AnchorGenerateResponse)
def generate_anchors(source_page_id: UUID, db: Session = Depends(get_db)):
    source_page = get_source_blog(db, source_page_id)
    blocks = db.scalars(select(ArticleBlock).where(ArticleBlock.page_id == source_page.id).order_by(ArticleBlock.block_index)).all()
    if not blocks:
        raise HTTPException(status_code=400, detail="请先解析正文。")
    target_pages = db.scalars(select(Page).where(Page.status == "published")).all()

    existing_candidates = db.scalars(select(AnchorCandidate).where(AnchorCandidate.source_page_id == source_page.id)).all()
    existing_keys = {
        (candidate.article_block_id, candidate.anchor_text.lower(), candidate.start_offset)
        for candidate in existing_candidates
    }
    existing_texts = {candidate.anchor_text.lower() for candidate in existing_candidates}
    drafts = generate_candidate_drafts(blocks, target_pages)
    candidates = [
        AnchorCandidate(
            tenant_id=get_settings().default_tenant_id,
            source_page_id=source_page.id,
            article_block_id=draft.article_block_id,
            anchor_text=draft.anchor_text,
            context_text=draft.context_text,
            link_type_suggestion=draft.link_type_suggestion,
            start_offset=draft.start_offset,
            end_offset=draft.end_offset,
            reason=draft.reason,
            confidence_score=draft.confidence_score,
            status="pending",
        )
        for draft in drafts
        if (draft.article_block_id, draft.anchor_text.lower(), draft.start_offset) not in existing_keys
        and draft.anchor_text.lower() not in existing_texts
    ]
    db.add_all(candidates)
    db.commit()
    for candidate in candidates:
        db.refresh(candidate)
    all_candidates = db.scalars(select(AnchorCandidate).where(AnchorCandidate.source_page_id == source_page.id).order_by(AnchorCandidate.created_at)).all()
    return AnchorGenerateResponse(source_page_id=source_page.id, created=len(candidates), items=list(all_candidates))


@router.get("/{source_page_id}/anchor-candidates", response_model=AnchorListResponse)
def list_anchors(source_page_id: UUID, db: Session = Depends(get_db)):
    items = db.scalars(select(AnchorCandidate).where(AnchorCandidate.source_page_id == source_page_id).order_by(AnchorCandidate.created_at)).all()
    return AnchorListResponse(items=list(items))


@router.post("/{source_page_id}/recommendations/generate", response_model=RecommendationGenerateResponse)
def generate_recommendations(source_page_id: UUID, db: Session = Depends(get_db)):
    source_page = get_source_blog(db, source_page_id)
    anchors = db.scalars(select(AnchorCandidate).where(AnchorCandidate.source_page_id == source_page.id, AnchorCandidate.status == "pending")).all()
    target_pages = db.scalars(select(Page).where(Page.status == "published")).all()
    created = 0

    for anchor in anchors:
        db.execute(delete(LinkRecommendation).where(LinkRecommendation.anchor_candidate_id == anchor.id))
        ranked = rank_recommendations(source_page, anchor, target_pages)
        for index, score in enumerate(ranked, start=1):
            db.add(
                LinkRecommendation(
                    tenant_id=get_settings().default_tenant_id,
                    anchor_candidate_id=anchor.id,
                    target_page_id=score.target_page_id,
                    rank=index,
                    score_total=score.score_total,
                    score_cluster=score.score_cluster,
                    score_keyword=score.score_keyword,
                    score_page_type=score.score_page_type,
                    score_semantic=score.score_semantic,
                    score_title=score.score_title,
                    score_history=score.score_history,
                    score_quality=score.score_quality,
                    penalty_duplicate=score.penalty_duplicate,
                    penalty_competition=score.penalty_competition,
                    penalty_over_optimization=score.penalty_over_optimization,
                    penalty_distance=score.penalty_distance,
                    reason_json=score.reason_json,
                    status="pending",
                )
            )
            created += 1

    db.commit()
    return RecommendationGenerateResponse(source_page_id=source_page.id, created=created)


@router.get("/{source_page_id}/recommendations", response_model=RecommendationListResponse)
def list_recommendations(source_page_id: UUID, db: Session = Depends(get_db)):
    anchors = db.scalars(select(AnchorCandidate).where(AnchorCandidate.source_page_id == source_page_id).order_by(AnchorCandidate.created_at)).all()
    groups: list[AnchorRecommendationGroup] = []
    for anchor in anchors:
        recs = db.scalars(select(LinkRecommendation).where(LinkRecommendation.anchor_candidate_id == anchor.id).order_by(LinkRecommendation.rank)).all()
        rec_out: list[RecommendationOut] = []
        for rec in recs:
            target = db.get(Page, rec.target_page_id)
            if not target:
                continue
            rec_out.append(
                RecommendationOut(
                    id=rec.id,
                    target_page_id=target.id,
                    rank=rec.rank,
                    url=target.canonical_url,
                    title=target.title,
                    page_type=target.page_type,
                    meta_description=target.meta_description,
                    score_total=float(rec.score_total),
                    score_cluster=float(rec.score_cluster),
                    score_keyword=float(rec.score_keyword),
                    score_page_type=float(rec.score_page_type),
                    score_semantic=float(rec.score_semantic),
                    score_title=float(rec.score_title),
                    score_history=float(rec.score_history),
                    score_quality=float(rec.score_quality),
                    penalty_duplicate=float(rec.penalty_duplicate),
                    penalty_competition=float(rec.penalty_competition),
                    penalty_over_optimization=float(rec.penalty_over_optimization),
                    penalty_distance=float(rec.penalty_distance),
                    reason_json=rec.reason_json,
                )
            )
        groups.append(
            AnchorRecommendationGroup(
                anchor_candidate_id=anchor.id,
                anchor_text=anchor.anchor_text,
                context_text=anchor.context_text,
                link_type_suggestion=anchor.link_type_suggestion,
                reason=anchor.reason,
                status=anchor.status,
                recommendations=rec_out,
            )
        )
    return RecommendationListResponse(items=groups)


@router.post("/{source_page_id}/decisions", response_model=DecisionsResponse)
def save_decisions(source_page_id: UUID, payload: DecisionsRequest, db: Session = Depends(get_db)):
    get_source_blog(db, source_page_id)
    created = 0
    for item in payload.decisions:
        candidate = db.get(AnchorCandidate, item.anchor_candidate_id)
        if not candidate or candidate.source_page_id != source_page_id:
            raise HTTPException(status_code=400, detail="候选锚文本不存在或不属于当前 source page。")
        if item.decision == "approve" and not item.selected_target_page_id:
            raise HTTPException(status_code=400, detail="approve 必须提供 selected_target_page_id。")
        if item.decision == "replace_target" and not item.manual_target_url:
            raise HTTPException(status_code=400, detail="replace_target 必须提供 manual_target_url。")
        if item.decision not in {"approve", "reject_anchor", "reject_target", "replace_target", "skip"}:
            raise HTTPException(status_code=400, detail="未知审核决策。")

        db.add(
            LinkDecision(
                tenant_id=get_settings().default_tenant_id,
                source_page_id=source_page_id,
                anchor_candidate_id=item.anchor_candidate_id,
                selected_target_page_id=item.selected_target_page_id,
                manual_target_url=item.manual_target_url,
                decision=item.decision,
                reviewer_note=item.reviewer_note,
            )
        )
        if item.decision in {"approve", "replace_target"}:
            candidate.status = "accepted"
            if item.selected_target_page_id:
                recommendation = db.scalar(
                    select(LinkRecommendation).where(
                        LinkRecommendation.anchor_candidate_id == candidate.id,
                        LinkRecommendation.target_page_id == item.selected_target_page_id,
                    )
                )
                if recommendation:
                    recommendation.status = "selected"
        elif item.decision == "reject_anchor":
            candidate.status = "rejected"
        elif item.decision == "skip":
            candidate.status = "skipped"
        created += 1

    db.commit()
    return DecisionsResponse(created=created)


@router.post("/{source_page_id}/preview", response_model=PreviewResponse)
def create_preview(source_page_id: UUID, db: Session = Depends(get_db)):
    source_page = get_source_blog(db, source_page_id)
    decisions = latest_decisions(db, source_page_id)
    insertions = []
    for decision in decisions:
        if decision.decision not in {"approve", "replace_target"}:
            continue
        candidate = db.get(AnchorCandidate, decision.anchor_candidate_id)
        if not candidate:
            continue
        block = db.get(ArticleBlock, candidate.article_block_id)
        if not block:
            continue
        if decision.decision == "approve":
            target = db.get(Page, decision.selected_target_page_id)
            if not target:
                continue
            target_url = target.canonical_url
        else:
            target_url = decision.manual_target_url or ""
        insertions.append({"candidate": candidate, "block": block, "target_url": target_url})

    preview_html, rule_check = generate_preview_html(source_page.raw_html or "", insertions)
    preview = InsertionPreview(
        tenant_id=get_settings().default_tenant_id,
        source_page_id=source_page.id,
        before_html=source_page.raw_html or "",
        preview_html=preview_html,
        rule_check_json=rule_check,
    )
    db.add(preview)
    db.commit()
    db.refresh(preview)
    return PreviewResponse(preview_id=preview.id, preview_html=preview.preview_html, rule_check=rule_check)


@router.post("/{source_page_id}/local-write", response_model=LocalWriteResponse)
def local_write(source_page_id: UUID, payload: LocalWriteRequest, db: Session = Depends(get_db)):
    page = get_source_blog(db, source_page_id)
    preview = db.get(InsertionPreview, payload.preview_id)
    if not preview or preview.source_page_id != source_page_id:
        raise HTTPException(status_code=404, detail="预览不存在。")
    if not preview.rule_check_json.get("passed"):
        raise HTTPException(status_code=400, detail="预览未通过规则检查，不能保存本地写回。")

    snapshot, audit = apply_local_write(page, preview, Snapshot, AuditLog, get_settings().default_tenant_id)
    db.add_all([snapshot, audit])
    db.commit()
    db.refresh(snapshot)
    return LocalWriteResponse(snapshot_id=snapshot.id, status="saved")


@router.get("/settings/llm", response_model=LlmSettings)
def get_llm_settings(db: Session = Depends(get_db)):
    tenant_id = get_settings().default_tenant_id
    setting = db.scalar(select(AppSetting).where(AppSetting.tenant_id == tenant_id, AppSetting.key == "llm"))
    return LlmSettings(**(setting.value_json if setting else {}))


@router.post("/settings/llm", response_model=LlmSettings)
def save_llm_settings(payload: LlmSettings, db: Session = Depends(get_db)):
    tenant_id = get_settings().default_tenant_id
    setting = db.scalar(select(AppSetting).where(AppSetting.tenant_id == tenant_id, AppSetting.key == "llm"))
    if setting:
        setting.value_json = payload.model_dump()
    else:
        db.add(AppSetting(tenant_id=tenant_id, key="llm", value_json=payload.model_dump()))
    db.commit()
    return payload


def get_source_blog(db: Session, source_page_id: UUID) -> Page:
    page = db.get(Page, source_page_id)
    if not page:
        raise HTTPException(status_code=404, detail="source page 不存在。")
    if page.page_type != "blog":
        raise HTTPException(status_code=400, detail="source page 必须是 blog。")
    return page


def latest_decisions(db: Session, source_page_id: UUID) -> list[LinkDecision]:
    decisions = db.scalars(select(LinkDecision).where(LinkDecision.source_page_id == source_page_id).order_by(LinkDecision.created_at.desc())).all()
    latest_by_anchor = {}
    for decision in decisions:
        latest_by_anchor.setdefault(decision.anchor_candidate_id, decision)
    return list(latest_by_anchor.values())
