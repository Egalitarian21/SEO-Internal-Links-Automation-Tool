import importlib
import subprocess
import sys
from pathlib import Path

import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_ROOT = PROJECT_ROOT.parent


def test_required_code_directories_exist():
    for relative_path in main.CODE_DIRECTORIES:
        assert (PROJECT_ROOT / relative_path).is_dir()


def test_placeholder_brand_structure_exists():
    for relative_path in main.BRAND_DIRECTORIES:
        assert (DEMO_ROOT / "Data" / "brand_name" / relative_path).is_dir()


def test_all_skeleton_modules_import():
    module_names = [
        "crawler.sitemap_parser",
        "crawler.html_fetcher",
        "crawler.url_queue_manager",
        "preprocessing.html_cleaner",
        "preprocessing.text_extractor",
        "preprocessing.technical_seo_checker",
        "preprocessing.blog_parser",
        "embedding.embedding_generator",
        "embedding.embedding_matcher",
        "link_recommendation.anchor_candidate_generator",
        "link_recommendation.internal_link_selector",
        "link_recommendation.external_link_selector",
        "link_recommendation.model_api_interface",
        "link_recommendation.recommendation_engine",
        "utils.logger",
        "utils.db_connector",
        "utils.file_manager",
        "utils.text_utils",
    ]
    for module_name in module_names:
        importlib.import_module(module_name)


def test_main_help_runs():
    result = subprocess.run(
        [sys.executable, "main.py", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "check-structure" in result.stdout


def test_init_brand_creates_full_structure(tmp_path, monkeypatch):
    data_root = tmp_path / "Data"
    monkeypatch.setattr(main, "DATA_ROOT", data_root)
    created = main.create_brand_structure("test_brand")
    assert len(created) == len(main.BRAND_DIRECTORIES)
    for relative_path in main.BRAND_DIRECTORIES:
        assert (data_root / "test_brand" / relative_path).is_dir()


def test_check_structure_reports_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DATA_ROOT", tmp_path / "Data")
    missing = main.find_missing_structure("missing_brand")
    assert missing
