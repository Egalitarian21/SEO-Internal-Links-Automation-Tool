from pathlib import Path

import typer

from utils.text_utils import safe_name

app = typer.Typer(help="Internal Link Tool project skeleton")

PROJECT_ROOT = Path(__file__).resolve().parent
DEMO_ROOT = PROJECT_ROOT.parent
DATA_ROOT = DEMO_ROOT / "Data"

CODE_DIRECTORIES = [
    "config",
    "crawler",
    "preprocessing",
    "embedding",
    "link_recommendation",
    "utils",
]

BRAND_DIRECTORIES = [
    "raw/sitemap",
    "raw/html_pages",
    "raw/blogs",
    "normalized/pages",
    "normalized/blogs",
    "normalized/seo_checks",
    "model_inputs/pages",
    "model_inputs/blogs",
    "profiles/page_profiles",
    "profiles/blog_profiles",
    "embeddings/page_embeddings",
    "embeddings/blog_embeddings",
    "link_graph/internal_links",
    "link_graph/external_sources",
    "recommendations/internal_links",
    "recommendations/external_links",
    "recommendations/html_outputs",
]


def create_brand_structure(brand: str) -> list[Path]:
    """Create the standard Data/<brand>/ directory structure."""
    brand_root = DATA_ROOT / safe_name(brand)
    created: list[Path] = []
    for relative_path in BRAND_DIRECTORIES:
        path = brand_root / relative_path
        path.mkdir(parents=True, exist_ok=True)
        created.append(path)
    return created


def find_missing_structure(brand: str = "brand_name") -> list[Path]:
    """Return required project paths that are currently missing."""
    missing: list[Path] = []
    for relative_path in CODE_DIRECTORIES:
        path = PROJECT_ROOT / relative_path
        if not path.exists():
            missing.append(path)
    brand_root = DATA_ROOT / safe_name(brand)
    for relative_path in BRAND_DIRECTORIES:
        path = brand_root / relative_path
        if not path.exists():
            missing.append(path)
    return missing


@app.command("init-brand")
def init_brand(brand: str = typer.Option(..., "--brand", help="Brand directory name under Data.")) -> None:
    """Initialize the Data directory tree for a brand."""
    created = create_brand_structure(brand)
    typer.echo(f"Initialized Data/{safe_name(brand)} with {len(created)} directories.")


@app.command("check-structure")
def check_structure(brand: str = typer.Option("brand_name", "--brand", help="Brand directory to inspect.")) -> None:
    """Check required Code and Data directories."""
    missing = find_missing_structure(brand)
    if missing:
        typer.echo("Missing required paths:")
        for path in missing:
            typer.echo(f"- {path}")
        raise typer.Exit(code=1)
    typer.echo("Project structure OK.")


if __name__ == "__main__":
    app()
