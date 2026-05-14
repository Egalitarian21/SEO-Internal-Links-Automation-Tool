class DemoShopifyClient:
    def publish(self, article_ids: list[str]) -> dict[str, str]:
        return {"status": "published", "article_count": str(len(article_ids))}

    def rollback(self, job_id: str) -> dict[str, str]:
        return {"status": "rolled_back", "job_id": job_id}


shopify_client = DemoShopifyClient()

