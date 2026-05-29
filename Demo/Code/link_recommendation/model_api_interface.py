class ModelAPIClient:
    """Placeholder for model API calls used by recommendation workflows."""

    def __init__(self, model_name: str = "", base_url: str = "", api_key: str = "") -> None:
        self.model_name = model_name
        self.base_url = base_url
        self.api_key = api_key

    def generate_json(self, prompt: str) -> dict:
        """Return a JSON-compatible model response placeholder."""
        return {"prompt": prompt, "result": None}
