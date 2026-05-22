from app.schemas import IntakeRequest
from app.services.storage import StorageService
from app.services.url_intake import URLIntakeService


def test_intake_creates_dirs_and_dedupes_urls():
    service = URLIntakeService()
    result = service.intake(
        IntakeRequest(
            customer="BrandX Inc",
            urls=[
                "https://brandx.com/a",
                "https://brandx.com/a",
                "https://brandx.com/b",
            ],
        )
    )
    assert result.new_urls_added == 2
    assert result.total_urls_in_db == 2
    assert len(result.dirs_ready) == 3

    second = service.intake(
        IntakeRequest(
            customer="BrandX Inc",
            urls=["https://brandx.com/a", "https://brandx.com/c"],
        )
    )
    assert second.new_urls_added == 1
    assert second.duplicate_urls_skipped == 1
    assert second.total_urls_in_db == 3

    storage = StorageService()
    urls = storage.read_internal_urls("BrandX Inc")
    assert urls == ["https://brandx.com/a", "https://brandx.com/b", "https://brandx.com/c"]

