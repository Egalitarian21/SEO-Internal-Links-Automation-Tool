import json
from pathlib import Path
from typing import Any

import yaml


def read_text(path: str | Path) -> str:
    """Read UTF-8 text from disk."""
    return Path(path).read_text(encoding="utf-8")


def write_text(path: str | Path, content: str) -> Path:
    """Write UTF-8 text to disk."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def read_json(path: str | Path) -> Any:
    """Read JSON from disk."""
    return json.loads(read_text(path))


def write_json(path: str | Path, payload: Any) -> Path:
    """Write pretty JSON to disk."""
    return write_text(path, json.dumps(payload, ensure_ascii=False, indent=2))


def read_yaml(path: str | Path) -> Any:
    """Read YAML from disk."""
    return yaml.safe_load(read_text(path))


def write_yaml(path: str | Path, payload: Any) -> Path:
    """Write YAML to disk."""
    return write_text(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
