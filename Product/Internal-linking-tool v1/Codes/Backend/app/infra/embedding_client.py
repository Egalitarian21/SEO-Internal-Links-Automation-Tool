class DemoEmbeddingClient:
    def score_similarity(self, source: str, target: str) -> int:
        overlap = len(set(source.lower().split()) & set(target.lower().split()))
        return min(95, 60 + overlap * 7)


embedding_client = DemoEmbeddingClient()

