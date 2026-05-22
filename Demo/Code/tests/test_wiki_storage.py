from app.schemas import WikiCard
from app.services.storage import StorageService


def test_save_wiki_card_handles_title_collision():
    storage = StorageService()
    storage.ensure_customer_dirs("BrandX")
    card = WikiCard(
        customer="BrandX",
        url="https://brandx.com/a",
        Title="How to do SEO",
        Description="desc",
        H_Hierarchy=[{"level": 1, "text": "How to do SEO"}],
        Web_Abstract_AI_Generated="summary",
    )
    first = storage.save_wiki_card("BrandX", card.Title, card)
    second = storage.save_wiki_card("BrandX", card.Title, card)
    assert first.name.startswith("Wiki-how-to-do-seo")
    assert second.name.startswith("Wiki-how-to-do-seo-2")

