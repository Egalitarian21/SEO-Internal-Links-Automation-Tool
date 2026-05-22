from app.schemas import GenerateRequest, IntakeRequest
from app.services.url_intake import URLIntakeService
from app.services.wiki_generator import WikiGeneratorService


class FakeCrawler:
    async def crawl(self, url: str):
        return {
            "url": url,
            "title": f"Title {url.split('/')[-1]}",
            "description": "desc",
            "h_hierarchy": [{"level": 1, "text": "H1"}],
            "body_text": "body",
        }


class FakeLLM:
    async def generate_wiki_abstract(self, title, description, h_hierarchy, body_text):
        return f"Summary for {title}"


async def test_wiki_generator_only_missing():
    intake = URLIntakeService()
    intake.intake(
        IntakeRequest(
            customer="BrandX",
            urls=["https://brandx.com/a", "https://brandx.com/b"],
        )
    )

    service = WikiGeneratorService(crawler=FakeCrawler(), llm=FakeLLM())
    first = await service.generate(GenerateRequest(customer="BrandX", batch_size=10, only_missing=True))
    second = await service.generate(GenerateRequest(customer="BrandX", batch_size=10, only_missing=True))

    assert first.success == 2
    assert second.success == 0

