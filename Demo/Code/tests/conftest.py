from pathlib import Path

import pytest

from app.config import get_settings


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch, tmp_path: Path):
    data_root = tmp_path / "Data"
    log_root = tmp_path / "logs"
    monkeypatch.setenv("DATA_ROOT", str(data_root))
    monkeypatch.setenv("LOG_ROOT", str(log_root))
    monkeypatch.setenv("LLM_USE_MOCK", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()

