# Internal-Link-Wiki MVP (CLI First)

## Quick Start

```bash
cd Code
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
copy .env.example .env
```

## CLI Commands

```bash
python -m app.cli intake --customer "BrandX-Inc" --urls-file .\urls.txt
python -m app.cli generate --customer "BrandX-Inc" --batch-size 10
python -m app.cli recommend --customer "BrandX-Inc" --blog-url "https://brandx.com/blogs/foo" --blog-md .\foo.md
python -m app.cli report --customer "BrandX-Inc" --result .\recommend-result.json
python -m app.cli recommend-and-report --customer "BrandX-Inc" --blog-url "https://brandx.com/blogs/foo" --blog-md .\foo.md --threshold 0.6 --max 8
```

## Notes

- This version is CLI-first and intentionally keeps API routers for the next iteration.
- Excel output follows the 7-column MVP schema.
- If private LLM endpoint is unavailable, set `LLM_USE_MOCK=true`.
