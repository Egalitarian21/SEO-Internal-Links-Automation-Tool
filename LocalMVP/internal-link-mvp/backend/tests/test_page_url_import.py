import httpx
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import routes_pages
from app.db.base import Base
from app.db.models import ImportJob, ImportJobItem, Page, utc_now
from app.db.session import get_db
from app.main import app
from app.schemas.page import PageInput
from app.services.page_fetcher import FetchedPage, fetch_url_as_page_input, infer_page_type


def test_infer_page_type_from_shopify_paths():
    assert infer_page_type("https://example.com/blogs/news/how-to-choose") == "blog"
    assert infer_page_type("https://example.com/collections/chairs") == "collection"
    assert infer_page_type("https://example.com/products/chair") == "product"
    assert infer_page_type("https://example.com/collections/chairs/products/chair") == "product"
    assert infer_page_type("https://example.com/pages/about") is None


def test_fetch_url_as_page_input_parses_metadata_without_raw_html():
    html = """
    <html>
      <head>
        <title>Meta Title</title>
        <meta name="description" content="Meta description.">
      </head>
      <body>
        <h1>Main H1</h1>
        <main><p>Body text for excerpt fallback.</p></main>
      </body>
    </html>
    """

    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=html, request=request))
    with httpx.Client(transport=transport) as client:
        result = fetch_url_as_page_input("https://example.com/blogs/news/article", client=client)

    assert result.page is not None
    assert result.page.page_type == "blog"
    assert result.page.title == "Meta Title"
    assert result.page.meta_title == "Meta Title"
    assert result.page.meta_description == "Meta description."
    assert result.page.h1 == "Main H1"
    assert result.page.keyword == "Main H1"
    assert result.page.cluster_name is None
    assert result.page.raw_html is None


def test_import_urls_api_creates_updates_and_reports_failures(monkeypatch):
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def fake_run_import_url_job(job_id, upsert_page_func):
        db = TestingSessionLocal()
        try:
            job = db.get(ImportJob, job_id)
            job.status = "running"
            db.commit()
            items = db.query(ImportJobItem).filter(ImportJobItem.job_id == job_id, ImportJobItem.status == "queued").all()
            for item in items:
                if "missing-type" in item.url:
                    item.status = "failed"
                    item.reason = "无法从 URL 路径判断页面类型。"
                    job.failed += 1
                else:
                    page = PageInput(
                        page_type="blog",
                        url=item.url,
                        title="Fetched Title",
                        meta_title="Fetched Title",
                        meta_description="Fetched description.",
                        h1="Fetched H1",
                        excerpt="Fetched description.",
                        status="published",
                        keyword="Fetched H1",
                        raw_html=None,
                    )
                    result = upsert_page_func(page, db)
                    item.status = result
                    item.page_type = page.page_type
                    item.title = page.title
                    if result == "created":
                        job.created += 1
                    elif result == "updated":
                        job.updated += 1
                    else:
                        job.skipped += 1
                job.processed += 1
                item.updated_at = utc_now()
                job.updated_at = utc_now()
                db.commit()
            job.status = "completed"
            job.completed_at = utc_now()
            db.commit()
        finally:
            db.close()

    monkeypatch.setattr(routes_pages, "run_import_url_job", fake_run_import_url_job)
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        first = client.post(
            "/api/pages/import-urls",
            json={"urls": ["https://example.com/blogs/news/a", "https://example.com/pages/missing-type"]},
        )
        assert first.status_code == 200
        first_job = client.get(f"/api/pages/import-url-jobs/{first.json()['id']}")
        assert first_job.status_code == 200
        assert first_job.json()["created"] == 1
        assert first_job.json()["failed"] == 1
        assert first_job.json()["status"] == "completed"

        second = client.post("/api/pages/import-urls", json={"urls": ["https://example.com/blogs/news/a"]})
        assert second.status_code == 200
        second_job = client.get(f"/api/pages/import-url-jobs/{second.json()['id']}")
        assert second_job.status_code == 200
        assert second_job.json()["updated"] == 1

        db = TestingSessionLocal()
        try:
            pages = db.query(Page).all()
            assert len(pages) == 1
            assert pages[0].raw_html is None
            assert pages[0].keyword == "Fetched H1"
        finally:
            db.close()
    finally:
        app.dependency_overrides.clear()
