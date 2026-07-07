from pydantic import BaseModel


class LlmSettings(BaseModel):
    enabled: bool = False
    base_url: str = ""
    api_key: str = ""
    model: str = ""

