import pytest

from app.errors import AppError
from app.utils.slug import sanitize_customer_name, slugify_text


def test_sanitize_customer_name_replaces_invalid_chars():
    assert sanitize_customer_name('Brand/Name:*?"<>|') == "Brand-Name-"


def test_sanitize_customer_name_supports_chinese_and_space():
    assert sanitize_customer_name("品牌 客户 A") == "品牌 客户 A"


def test_sanitize_customer_name_raises_on_empty():
    with pytest.raises(AppError):
        sanitize_customer_name("  ")


def test_slugify_text_limits_length():
    long_text = "A" * 120
    assert len(slugify_text(long_text, max_len=80)) <= 80

