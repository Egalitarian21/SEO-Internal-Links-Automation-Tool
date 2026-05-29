from pathlib import Path


def parse_blog_file(path: str | Path) -> dict[str, str]:
    """Load an imported blog file and return a normalized text payload."""
    blog_path = Path(path)
    content = blog_path.read_text(encoding="utf-8")
    title = ""
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            break
    return {"title": title, "content": content}
