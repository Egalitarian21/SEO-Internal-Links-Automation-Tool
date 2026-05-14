class DemoLlmClient:
    def summarize_keywords(self, text: str) -> list[str]:
        words = [part.strip(".,") for part in text.lower().split()]
        unique_words = []
        for word in words:
            if len(word) > 5 and word not in unique_words:
                unique_words.append(word)
            if len(unique_words) == 3:
                break
        return unique_words or ["internal linking", "seo", "content"]


llm_client = DemoLlmClient()

