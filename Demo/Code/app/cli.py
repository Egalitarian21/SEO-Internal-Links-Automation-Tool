import asyncio
import json
from pathlib import Path

import typer

from app.config import get_settings
from app.schemas import (
    GenerateRequest,
    IntakeRequest,
    RecommendRequest,
    RecommendResult,
    ReportRequest,
)
from app.services.excel_reporter import ExcelReporterService
from app.services.recommender import RecommenderService
from app.services.url_intake import URLIntakeService
from app.services.wiki_generator import WikiGeneratorService

app = typer.Typer(help="Internal-Link-Wiki MVP CLI")


@app.command("intake")
def intake(
    customer: str = typer.Option(..., "--customer"),
    urls_file: Path | None = typer.Option(None, "--urls-file"),
    blog_url: str | None = typer.Option(None, "--blog-url"),
    blog_md: Path | None = typer.Option(None, "--blog-md"),
) -> None:
    urls: list[str] = []
    if urls_file and urls_file.exists():
        urls = [line.strip() for line in urls_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    blog_markdown = ""
    if blog_md and blog_md.exists():
        blog_markdown = blog_md.read_text(encoding="utf-8")

    service = URLIntakeService()
    result = service.intake(
        IntakeRequest(
            customer=customer,
            urls=urls,
            blog_url=blog_url,
            blog_markdown=blog_markdown or None,
        )
    )
    typer.echo(result.model_dump_json(indent=2))


@app.command("generate")
def generate(
    customer: str = typer.Option(..., "--customer"),
    batch_size: int | None = typer.Option(None, "--batch-size"),
    only_missing: bool = typer.Option(True, "--only-missing/--all"),
) -> None:
    settings = get_settings()
    service = WikiGeneratorService()
    result = asyncio.run(
        service.generate(
            GenerateRequest(
                customer=customer,
                batch_size=batch_size or settings.default_batch_size,
                only_missing=only_missing,
            )
        )
    )
    typer.echo(result.model_dump_json(indent=2))


@app.command("recommend")
def recommend(
    customer: str = typer.Option(..., "--customer"),
    blog_url: str = typer.Option(..., "--blog-url"),
    blog_md: Path = typer.Option(..., "--blog-md"),
    blog_title: str | None = typer.Option(None, "--blog-title"),
    threshold: float | None = typer.Option(None, "--threshold"),
    max_recommendations: int | None = typer.Option(None, "--max"),
    output: Path | None = typer.Option(None, "--output"),
) -> None:
    settings = get_settings()
    markdown = blog_md.read_text(encoding="utf-8")
    service = RecommenderService()
    result = asyncio.run(
        service.recommend(
            RecommendRequest(
                customer=customer,
                blog_url=blog_url,
                blog_markdown=markdown,
                blog_title=blog_title,
                score_threshold=threshold if threshold is not None else settings.default_score_threshold,
                max_recommendations=(
                    max_recommendations if max_recommendations is not None else settings.default_max_recommendations
                ),
            )
        )
    )

    if output:
        output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        typer.echo(f"Saved: {output}")
    else:
        typer.echo(result.model_dump_json(indent=2))


@app.command("report")
def report(
    customer: str = typer.Option(..., "--customer"),
    result: Path = typer.Option(..., "--result"),
) -> None:
    payload = json.loads(result.read_text(encoding="utf-8"))
    recommend_result = RecommendResult.model_validate(payload)
    service = ExcelReporterService()
    report_result = service.write(
        ReportRequest(
            customer=customer,
            blog_url=recommend_result.blog_url,
            recommend_result=recommend_result,
        )
    )
    typer.echo(report_result.model_dump_json(indent=2))


@app.command("recommend-and-report")
def recommend_and_report(
    customer: str = typer.Option(..., "--customer"),
    blog_url: str = typer.Option(..., "--blog-url"),
    blog_md: Path = typer.Option(..., "--blog-md"),
    blog_title: str | None = typer.Option(None, "--blog-title"),
    threshold: float | None = typer.Option(None, "--threshold"),
    max_recommendations: int | None = typer.Option(None, "--max"),
) -> None:
    settings = get_settings()
    markdown = blog_md.read_text(encoding="utf-8")
    recommend_service = RecommenderService()
    recommend_result = asyncio.run(
        recommend_service.recommend(
            RecommendRequest(
                customer=customer,
                blog_url=blog_url,
                blog_markdown=markdown,
                blog_title=blog_title,
                score_threshold=threshold if threshold is not None else settings.default_score_threshold,
                max_recommendations=(
                    max_recommendations if max_recommendations is not None else settings.default_max_recommendations
                ),
            )
        )
    )
    reporter = ExcelReporterService()
    report_result = reporter.write(
        ReportRequest(
            customer=customer,
            blog_url=blog_url,
            recommend_result=recommend_result,
        )
    )
    typer.echo(
        json.dumps(
            {
                "recommend_result": recommend_result.model_dump(),
                "report_result": report_result.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    app()

