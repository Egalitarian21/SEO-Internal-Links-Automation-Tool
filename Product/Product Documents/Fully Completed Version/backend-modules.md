# Backend Modules

```text
backend/app/
|-- sitemap_importer.py       # Handles manually imported URLs
|-- web_crawler.py            # Crawls blog content based on URLs
|-- content_cleaner.py        # Cleans HTML and extracts body text
|-- wiki_card_generator.py    # Batch-generates Wiki cards with the LLM
|-- anchor_matcher.py         # Uses the LLM to select anchor text and match cards
|-- shopify_publisher.py      # Creates Shopify blogs
|-- review_service.py         # Review workflow
|-- models.py
|-- schemas.py
`-- routers/
    |-- imports.py
    |-- drafts.py
    |-- cards.py
    |-- suggestions.py
    `-- publish.py
```
