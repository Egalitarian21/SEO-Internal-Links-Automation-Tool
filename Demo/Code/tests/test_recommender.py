from app.schemas import RecommendRequest, WikiCard
from app.services.recommender import RecommenderService
from app.services.storage import StorageService


async def test_recommender_validates_anchor_rules():
    storage = StorageService()
    storage.ensure_customer_dirs("BrandX")
    storage.save_wiki_card(
        "BrandX",
        "Product Research Guide",
        WikiCard(
            customer="BrandX",
            url="https://brandx.com/research",
            Title="Product Research Guide",
            Description="desc",
            H_Hierarchy=[{"level": 1, "text": "Product Research Guide"}],
            Web_Abstract_AI_Generated="summary",
        ),
    )
    storage.save_wiki_card(
        "BrandX",
        "Supplier Comparison",
        WikiCard(
            customer="BrandX",
            url="https://brandx.com/suppliers",
            Title="Supplier Comparison",
            Description="desc",
            H_Hierarchy=[{"level": 1, "text": "Supplier Comparison"}],
            Web_Abstract_AI_Generated="summary",
        ),
    )

    blog = """# How to Find Suppliers

Opening paragraph that should not contain selected anchor.

When validating a niche, product research methods help reduce risk before paid ads.

Many beginners compare marketplaces before selecting reliable suppliers.
"""
    service = RecommenderService(storage=storage)
    result = await service.recommend(
        RecommendRequest(
            customer="BrandX",
            blog_url="https://brandx.com/blogs/find-suppliers",
            blog_markdown=blog,
            max_recommendations=2,
        )
    )
    assert len(result.recommendations) <= 2
    assert result.library_size == 2
    for rec in result.recommendations:
        assert rec.anchor_text in blog
        assert "Opening paragraph" not in rec.insert_paragraph

