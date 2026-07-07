from app.services.canonical import canonicalize_url


def test_remove_utm_params():
    url = canonicalize_url("https://Example.com/products/chair?utm_source=x&utm_medium=y&variant=1")

    assert url == "https://example.com/products/chair?variant=1"


def test_remove_hash():
    url = canonicalize_url("https://example.com/blogs/news/post#section")

    assert url == "https://example.com/blogs/news/post"


def test_shopify_collection_product_url_to_product_canonical():
    url = canonicalize_url("https://example.com/collections/chairs/products/cloud-chair/")

    assert url == "https://example.com/products/cloud-chair"
