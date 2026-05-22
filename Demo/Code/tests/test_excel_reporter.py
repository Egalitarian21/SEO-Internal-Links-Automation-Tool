import pytest

pytest.importorskip("openpyxl")

from app.schemas import RecommendResult, Recommendation, ReportRequest
from app.services.excel_reporter import ExcelReporterService


def test_excel_reporter_writes_7_columns():
    recommend_result = RecommendResult(
        customer="BrandX",
        blog_url="https://brandx.com/blog",
        blog_title="Sample Blog",
        candidates_filtered=2,
        recommendations=[
            Recommendation(
                target_url="https://brandx.com/target-1",
                target_title="Target 1",
                anchor_text="product research",
                insert_paragraph="Use product research before launch.",
                relevance_score=0.81,
                reason="Strong semantic match.",
            )
        ],
        discarded=[],
        library_size=10,
        elapsed_seconds=0.12,
    )
    service = ExcelReporterService()
    report = service.write(
        ReportRequest(
            customer="BrandX",
            blog_url="https://brandx.com/blog",
            recommend_result=recommend_result,
        )
    )
    assert report.file_name.endswith(".xlsx")
    assert report.rows_written == 1
    assert report.file_size_bytes > 0
