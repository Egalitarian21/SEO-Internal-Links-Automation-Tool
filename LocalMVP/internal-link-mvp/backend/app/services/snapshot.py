from app.services.canonical import content_hash


def apply_local_write(page, preview, snapshot_model, audit_model, tenant_id):
    before_html = page.raw_html or ""
    after_html = preview.preview_html
    page.raw_html = after_html
    page.content_hash = content_hash(after_html)
    snapshot = snapshot_model(
        tenant_id=tenant_id,
        source_page_id=page.id,
        snapshot_type="local_write",
        before_html=before_html,
        after_html=after_html,
        preview_id=preview.id,
    )
    audit = audit_model(
        tenant_id=tenant_id,
        action="local_write",
        entity_type="pages",
        entity_id=page.id,
        before_json={"raw_html": before_html},
        after_json={"raw_html": after_html, "preview_id": str(preview.id)},
    )
    return snapshot, audit
