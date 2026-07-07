from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from uuid import UUID

from app.db.base import Base
from app.db.models import LinkDecision
from app.db.session import get_db
from app.main import app
from app.services.seed import SAMPLE_ITEMS


def test_full_api_smoke_flow():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        assert client.get("/api/health").json() == {"status": "ok"}

        import_response = client.post("/api/pages/import", json={"items": SAMPLE_ITEMS})
        assert import_response.status_code == 200
        assert import_response.json()["created"] == 8

        pages = client.get("/api/pages", params={"page_type": "blog", "status": "published"}).json()["items"]
        source_page = next(item for item in pages if item["keyword"] == "glider recliner")

        parse_response = client.post(f"/api/articles/{source_page['id']}/parse")
        assert parse_response.status_code == 200
        assert parse_response.json()["block_count"] >= 5

        anchor_response = client.post(f"/api/internal-linking/{source_page['id']}/anchor-candidates/generate")
        assert anchor_response.status_code == 200
        anchors = anchor_response.json()["items"]
        assert len(anchors) >= 3

        rec_response = client.post(f"/api/internal-linking/{source_page['id']}/recommendations/generate")
        assert rec_response.status_code == 200
        assert rec_response.json()["created"] >= 6

        rec_groups = client.get(f"/api/internal-linking/{source_page['id']}/recommendations").json()["items"]
        decisions = []
        for group in rec_groups:
            if group["recommendations"]:
                decisions.append(
                    {
                        "anchor_candidate_id": group["anchor_candidate_id"],
                        "decision": "approve",
                        "selected_target_page_id": group["recommendations"][0]["target_page_id"],
                    }
                )

        decision_response = client.post(f"/api/internal-linking/{source_page['id']}/decisions", json={"decisions": decisions})
        assert decision_response.status_code == 200
        assert decision_response.json()["created"] == len(decisions)

        preview_response = client.post(f"/api/internal-linking/{source_page['id']}/preview")
        assert preview_response.status_code == 200
        preview = preview_response.json()
        assert preview["rule_check"]["passed"] is True
        assert "<a href=" in preview["preview_html"]

        write_response = client.post(f"/api/internal-linking/{source_page['id']}/local-write", json={"preview_id": preview["preview_id"]})
        assert write_response.status_code == 200
        snapshot_id = write_response.json()["snapshot_id"]

        snapshots_response = client.get("/api/snapshots", params={"source_page_id": source_page["id"]})
        assert snapshots_response.status_code == 200
        assert len(snapshots_response.json()["items"]) >= 1

        rollback_response = client.post(f"/api/snapshots/{snapshot_id}/rollback")
        assert rollback_response.status_code == 200
        assert rollback_response.json()["status"] == "rolled_back"
    finally:
        app.dependency_overrides.clear()


def test_decision_history_is_preserved_and_preview_uses_latest_decision():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    try:
        client.post("/api/pages/import", json={"items": SAMPLE_ITEMS})
        pages = client.get("/api/pages", params={"page_type": "blog", "status": "published"}).json()["items"]
        source_page = next(item for item in pages if item["keyword"] == "glider recliner")
        client.post(f"/api/articles/{source_page['id']}/parse")
        anchors = client.post(f"/api/internal-linking/{source_page['id']}/anchor-candidates/generate").json()["items"]
        client.post(f"/api/internal-linking/{source_page['id']}/recommendations/generate")
        rec_groups = client.get(f"/api/internal-linking/{source_page['id']}/recommendations").json()["items"]
        group = next(item for item in rec_groups if item["recommendations"])
        anchor_id = group["anchor_candidate_id"]
        first_target = group["recommendations"][0]["target_page_id"]
        manual_url = "https://example.com/manual/latest-target"

        first_decision = client.post(
            f"/api/internal-linking/{source_page['id']}/decisions",
            json={"decisions": [{"anchor_candidate_id": anchor_id, "decision": "approve", "selected_target_page_id": first_target}]},
        )
        assert first_decision.status_code == 200
        second_decision = client.post(
            f"/api/internal-linking/{source_page['id']}/decisions",
            json={"decisions": [{"anchor_candidate_id": anchor_id, "decision": "replace_target", "manual_target_url": manual_url}]},
        )
        assert second_decision.status_code == 200

        db = TestingSessionLocal()
        try:
            assert db.query(LinkDecision).filter(LinkDecision.anchor_candidate_id == UUID(anchor_id)).count() == 2
        finally:
            db.close()

        regenerate = client.post(f"/api/internal-linking/{source_page['id']}/anchor-candidates/generate")
        assert regenerate.status_code == 200
        db = TestingSessionLocal()
        try:
            assert db.query(LinkDecision).filter(LinkDecision.anchor_candidate_id == UUID(anchor_id)).count() == 2
        finally:
            db.close()

        preview = client.post(f"/api/internal-linking/{source_page['id']}/preview").json()
        assert manual_url in preview["preview_html"]
    finally:
        app.dependency_overrides.clear()
