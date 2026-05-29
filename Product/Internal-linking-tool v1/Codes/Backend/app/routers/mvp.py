from __future__ import annotations

import csv
import json
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse
from xml.etree import ElementTree

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.core.config import settings


router = APIRouter()


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def db_path() -> Path:
    url = settings.database_url
    if url.startswith("sqlite:///"):
        raw_path = url.removeprefix("sqlite:///")
    else:
        raw_path = "./data/internal_links.sqlite"
    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


@contextmanager
def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        init_db(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            canonical_url TEXT,
            title TEXT,
            page_type TEXT CHECK (page_type IN ('blog','collection','product','other')) DEFAULT 'other',
            primary_topic TEXT,
            intent TEXT CHECK (intent IN ('informational','navigational','commercial','transactional')) DEFAULT 'informational',
            status TEXT CHECK (status IN ('pending','crawled','profiled','failed')) DEFAULT 'pending',
            is_indexable BOOLEAN DEFAULT 1,
            raw_html_path TEXT,
            profile_md_path TEXT,
            body_text TEXT,
            body_html TEXT,
            paragraphs_json TEXT DEFAULT '[]',
            error_message TEXT,
            last_crawled_at TEXT,
            last_profiled_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_pages_type ON pages(page_type);
        CREATE INDEX IF NOT EXISTS idx_pages_topic ON pages(primary_topic);
        CREATE INDEX IF NOT EXISTS idx_pages_status ON pages(status);

        CREATE TABLE IF NOT EXISTS page_profiles (
            page_id INTEGER PRIMARY KEY REFERENCES pages(id) ON DELETE CASCADE,
            l0_summary TEXT,
            parent_topic TEXT,
            core_entities TEXT,
            suggested_anchors TEXT,
            target_priority INTEGER CHECK (target_priority BETWEEN 1 AND 5) DEFAULT 3,
            link_strategy TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            target_url TEXT NOT NULL,
            anchor_text TEXT,
            paragraph TEXT,
            is_internal BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (source_url, target_url, anchor_text)
        );
        CREATE INDEX IF NOT EXISTS idx_links_source ON links(source_url);
        CREATE INDEX IF NOT EXISTS idx_links_target ON links(target_url);

        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT NOT NULL,
            source_type TEXT,
            target_url TEXT NOT NULL,
            target_type TEXT,
            anchor_text TEXT NOT NULL,
            insert_position TEXT NOT NULL,
            insert_paragraph TEXT,
            confidence REAL,
            reason TEXT,
            trace_json TEXT,
            status TEXT CHECK (status IN ('pending','approved','rejected','edited_approved')) DEFAULT 'pending',
            batch_id TEXT,
            llm_call_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_rec_source ON recommendations(source_url);
        CREATE INDEX IF NOT EXISTS idx_rec_status ON recommendations(status);
        CREATE INDEX IF NOT EXISTS idx_rec_batch ON recommendations(batch_id);

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id INTEGER NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
            decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','edited_approved')),
            reviewer TEXT,
            reviewer_note TEXT,
            rejection_reason TEXT,
            edited_anchor_text TEXT,
            edited_target_url TEXT,
            edited_insert_position TEXT,
            reviewed_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS import_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT CHECK (source_type IN ('sitemap','url_list','manual')),
            source_value TEXT,
            total_urls INTEGER DEFAULT 0,
            crawled_urls INTEGER DEFAULT 0,
            failed_urls INTEGER DEFAULT 0,
            profiled_urls INTEGER DEFAULT 0,
            status TEXT CHECK (status IN ('queued','running','completed','failed')) DEFAULT 'queued',
            error_message TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS llm_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purpose TEXT NOT NULL,
            model TEXT,
            prompt TEXT,
            response TEXT,
            tokens_in INTEGER,
            tokens_out INTEGER,
            duration_ms INTEGER,
            success BOOLEAN,
            error_message TEXT,
            related_entity TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def envelope(data: Any) -> dict[str, Any]:
    return {"ok": True, "data": data}


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse("https://" + url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Invalid URL")
    path = re.sub(r"/collections/[^/]+/products/", "/products/", parsed.path)
    path = re.sub(r"/+", "/", path).rstrip("/") or "/"
    return urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", "", ""))


def infer_page_type(url: str) -> str:
    path = urlparse(url).path.lower()
    if "/blogs/" in path or "/blog/" in path:
        return "blog"
    if "/collections/" in path:
        return "collection"
    if "/products/" in path:
        return "product"
    return "other"


def words(text: str) -> list[str]:
    return [item.lower() for item in re.findall(r"[a-zA-Z][a-zA-Z0-9-]{2,}|[\u4e00-\u9fff]{2,}", text)]


def top_terms(text: str, limit: int = 8) -> list[str]:
    stop = {"the", "and", "for", "with", "your", "this", "that", "from", "into", "about", "you", "are", "how"}
    counts: dict[str, int] = {}
    for word in words(text):
        if word in stop:
            continue
        counts[word] = counts.get(word, 0) + 1
    return [item for item, _ in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:limit]]


def title_from_url(url: str) -> str:
    slug = Path(urlparse(url).path.rstrip("/")).name or urlparse(url).netloc
    return re.sub(r"[-_]+", " ", slug).strip().title() or url


async def fetch_html(url: str) -> str:
    async with httpx.AsyncClient(
        timeout=settings.crawler_timeout,
        headers={"User-Agent": settings.crawler_user_agent},
        follow_redirects=True,
    ) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


def clean_html(url: str, html: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    for selector in ["script", "style", "nav", "footer", "header", "aside", "noscript"]:
        for node in soup.select(selector):
            node.decompose()
    title = (soup.title.string.strip() if soup.title and soup.title.string else "") or title_from_url(url)
    canonical_node = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical_url = normalize_url(urljoin(url, canonical_node.get("href"))) if canonical_node and canonical_node.get("href") else url
    robots = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    is_indexable = not (robots and "noindex" in str(robots.get("content", "")).lower())
    body = soup.find("main") or soup.find("article") or soup.body or soup
    paragraphs = [node.get_text(" ", strip=True) for node in body.find_all(["p", "li"]) if len(node.get_text(" ", strip=True)) >= 20]
    if not paragraphs:
        text = body.get_text(" ", strip=True)
        paragraphs = [chunk.strip() for chunk in re.split(r"(?<=[.!?。！？])\s+", text) if len(chunk.strip()) >= 20][:12]
    body_text = "\n\n".join(paragraphs)
    return {
        "title": title,
        "canonical_url": canonical_url,
        "is_indexable": int(is_indexable),
        "body_html": str(body),
        "body_text": body_text,
        "paragraphs": paragraphs,
    }


def fallback_page(url: str) -> dict[str, Any]:
    title = title_from_url(url)
    paragraphs = [
        f"{title} is an imported page for internal link planning.",
        "Internal link recommendations work best when the source paragraph names a concrete topic and a useful target page.",
        "Editors can enrich this page after the crawler has access to the live content and then regenerate recommendations.",
    ]
    return {
        "title": title,
        "canonical_url": url,
        "is_indexable": 1,
        "body_html": "".join(f"<p>{paragraph}</p>" for paragraph in paragraphs),
        "body_text": "\n\n".join(paragraphs),
        "paragraphs": paragraphs,
    }


def profile_from_page(page: dict[str, Any]) -> dict[str, Any]:
    text = f"{page.get('title') or ''}\n{page.get('body_text') or ''}"
    terms = top_terms(text)
    parent_topic = " ".join(terms[:2]) if terms else page.get("page_type", "content")
    anchors = []
    paragraphs = json.loads(page.get("paragraphs_json") or "[]")
    for paragraph in paragraphs:
        for term in terms:
            match = re.search(re.escape(term), paragraph, re.I)
            if match and term not in anchors:
                anchors.append(paragraph[match.start() : match.end()])
        if len(anchors) >= 6:
            break
    if not anchors:
        anchors = terms[:3] or [page.get("title") or "content"]
    priority = {"product": 5, "collection": 4, "blog": 3}.get(page.get("page_type"), 2)
    summary = (page.get("body_text") or page.get("title") or "")[:140]
    return {
        "l0_summary": summary,
        "parent_topic": parent_topic,
        "core_entities": terms[:8],
        "suggested_anchors": anchors[:10],
        "target_priority": priority,
        "link_strategy": f"Use this {page.get('page_type')} page as a target when source paragraphs mention {parent_topic}.",
    }


def write_profile_markdown(page: dict[str, Any], profile: dict[str, Any]) -> str:
    base = Path(settings.knowledge_base_path)
    if not base.is_absolute():
        base = Path.cwd() / base
    pages_dir = base / "wiki" / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", (page.get("title") or str(page["id"])).lower()).strip("-") or str(page["id"])
    path = pages_dir / f"{slug}.md"
    path.write_text(
        "\n".join(
            [
                f"# {page.get('title') or page.get('url')}",
                "",
                f"- URL: {page.get('url')}",
                f"- Type: {page.get('page_type')}",
                f"- Topic: {profile['parent_topic']}",
                f"- Summary: {profile['l0_summary']}",
                f"- Entities: {', '.join(profile['core_entities'])}",
                f"- Suggested anchors: {', '.join(profile['suggested_anchors'])}",
                "",
                profile["link_strategy"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    return str(path)


def extract_links(conn: sqlite3.Connection, source_url: str, body_html: str) -> None:
    source_host = urlparse(source_url).netloc
    soup = BeautifulSoup(body_html, "html.parser")
    for link in soup.find_all("a", href=True):
        target = normalize_url(urljoin(source_url, link["href"]))
        anchor = link.get_text(" ", strip=True)
        paragraph_node = link.find_parent(["p", "li"])
        paragraph = paragraph_node.get_text(" ", strip=True)[:500] if paragraph_node else ""
        conn.execute(
            """
            INSERT OR IGNORE INTO links (source_url, target_url, anchor_text, paragraph, is_internal)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_url, target, anchor, paragraph, int(urlparse(target).netloc == source_host)),
        )


def upsert_profile(conn: sqlite3.Connection, page_id: int) -> dict[str, Any]:
    page = row_to_dict(conn.execute("SELECT * FROM pages WHERE id=?", (page_id,)).fetchone())
    if not page:
        raise HTTPException(status_code=404, detail="PAGE_NOT_FOUND")
    profile = profile_from_page(page)
    now = utc_now()
    conn.execute(
        """
        INSERT INTO llm_calls
            (purpose, model, prompt, response, tokens_in, tokens_out, duration_ms, success, related_entity, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """,
        (
            "l1_profile",
            "deterministic-mvp",
            f"Generate profile for {page.get('url')}",
            json.dumps(profile, ensure_ascii=False),
            len((page.get("body_text") or "").split()),
            len(json.dumps(profile, ensure_ascii=False).split()),
            0,
            f"page:{page_id}",
            now,
        ),
    )
    conn.execute(
        """
        INSERT INTO page_profiles
            (page_id, l0_summary, parent_topic, core_entities, suggested_anchors, target_priority, link_strategy, raw_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(page_id) DO UPDATE SET
            l0_summary=excluded.l0_summary,
            parent_topic=excluded.parent_topic,
            core_entities=excluded.core_entities,
            suggested_anchors=excluded.suggested_anchors,
            target_priority=excluded.target_priority,
            link_strategy=excluded.link_strategy,
            raw_json=excluded.raw_json,
            updated_at=excluded.updated_at
        """,
        (
            page_id,
            profile["l0_summary"],
            profile["parent_topic"],
            json.dumps(profile["core_entities"], ensure_ascii=False),
            json.dumps(profile["suggested_anchors"], ensure_ascii=False),
            profile["target_priority"],
            profile["link_strategy"],
            json.dumps(profile, ensure_ascii=False),
            now,
        ),
    )
    md_path = write_profile_markdown(page, profile)
    conn.execute(
        "UPDATE pages SET status='profiled', primary_topic=?, profile_md_path=?, last_profiled_at=?, updated_at=? WHERE id=?",
        (profile["parent_topic"], md_path, now, now, page_id),
    )
    return profile


async def crawl_and_profile(conn: sqlite3.Connection, page_id: int) -> dict[str, Any]:
    page = row_to_dict(conn.execute("SELECT * FROM pages WHERE id=?", (page_id,)).fetchone())
    if not page:
        raise HTTPException(status_code=404, detail="PAGE_NOT_FOUND")
    try:
        html = await fetch_html(page["url"])
        cleaned = clean_html(page["url"], html)
        raw_dir = Path(settings.knowledge_base_path)
        if not raw_dir.is_absolute():
            raw_dir = Path.cwd() / raw_dir
        raw_dir = raw_dir / "raw" / "pages"
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"{page_id}.html"
        raw_path.write_text(html, encoding="utf-8", errors="ignore")
    except Exception as exc:
        cleaned = fallback_page(page["url"])
        raw_path = None
        conn.execute("UPDATE pages SET error_message=? WHERE id=?", (str(exc), page_id))
    now = utc_now()
    conn.execute(
        """
        UPDATE pages
        SET canonical_url=?, title=?, page_type=?, is_indexable=?, raw_html_path=?, body_text=?, body_html=?,
            paragraphs_json=?, status='crawled', last_crawled_at=?, updated_at=?
        WHERE id=?
        """,
        (
            cleaned["canonical_url"],
            cleaned["title"],
            infer_page_type(page["url"]),
            cleaned["is_indexable"],
            str(raw_path) if raw_path else None,
            cleaned["body_text"],
            cleaned["body_html"],
            json.dumps(cleaned["paragraphs"], ensure_ascii=False),
            now,
            now,
            page_id,
        ),
    )
    extract_links(conn, page["url"], cleaned["body_html"])
    profile = upsert_profile(conn, page_id)
    return {**cleaned, "profile": profile}


class UrlListRequest(BaseModel):
    urls: list[str] = Field(min_length=1)
    auto_process: bool = True


class SitemapRequest(BaseModel):
    sitemap_url: str
    auto_process: bool = True


class GenerateRequest(BaseModel):
    source_url: str
    top_n: int = Field(default=3, ge=1, le=8)


class BatchGenerateRequest(BaseModel):
    source_urls: list[str] = Field(min_length=1)
    top_n: int = Field(default=3, ge=1, le=8)


class ReviewRequest(BaseModel):
    decision: str
    reviewer: str = "user"
    reviewer_note: str | None = None
    rejection_reason: str | None = None
    edited_anchor_text: str | None = None
    edited_target_url: str | None = None
    edited_insert_position: str | None = None


async def import_urls(urls: list[str], source_type: str, source_value: str, auto_process: bool) -> dict[str, Any]:
    normalized: list[str] = []
    for url in urls:
        try:
            normalized.append(normalize_url(url))
        except ValueError:
            continue
    normalized = list(dict.fromkeys(normalized))
    with connect() as conn:
        task = conn.execute(
            "INSERT INTO import_tasks (source_type, source_value, total_urls, status, created_at) VALUES (?, ?, ?, 'running', ?)",
            (source_type, source_value, len(normalized), utc_now()),
        )
        task_id = int(task.lastrowid)
        new_count = 0
        duplicate_count = 0
        for url in normalized:
            result = conn.execute(
                "INSERT OR IGNORE INTO pages (url, page_type, status, created_at, updated_at) VALUES (?, ?, 'pending', ?, ?)",
                (url, infer_page_type(url), utc_now(), utc_now()),
            )
            if result.rowcount:
                new_count += 1
            else:
                duplicate_count += 1
        crawled = failed = profiled = 0
        if auto_process:
            page_rows = conn.execute(
                f"SELECT id FROM pages WHERE url IN ({','.join('?' for _ in normalized)})",
                normalized,
            ).fetchall()
            for row in page_rows:
                try:
                    await crawl_and_profile(conn, int(row["id"]))
                    crawled += 1
                    profiled += 1
                except Exception as exc:
                    failed += 1
                    conn.execute("UPDATE pages SET status='failed', error_message=? WHERE id=?", (str(exc), int(row["id"])))
        conn.execute(
            """
            UPDATE import_tasks
            SET crawled_urls=?, failed_urls=?, profiled_urls=?, status='completed', completed_at=?
            WHERE id=?
            """,
            (crawled, failed, profiled, utc_now(), task_id),
        )
        return {"task_id": task_id, "total": len(normalized), "new": new_count, "duplicates": duplicate_count}


@router.post("/imports/url-list")
async def import_url_list(request: UrlListRequest) -> dict[str, Any]:
    return envelope(await import_urls(request.urls, "url_list", "\n".join(request.urls), request.auto_process))


@router.post("/imports/sitemap")
async def import_sitemap(request: SitemapRequest) -> dict[str, Any]:
    sitemap_url = normalize_url(request.sitemap_url)
    try:
        xml_text = await fetch_html(sitemap_url)
        root = ElementTree.fromstring(xml_text)
        urls = [node.text.strip() for node in root.findall(".//{*}loc") if node.text]
    except Exception as exc:
        raise HTTPException(status_code=400, detail={"code": "INVALID_SITEMAP", "message": str(exc)}) from exc
    return envelope(await import_urls(urls, "sitemap", sitemap_url, request.auto_process))


@router.get("/imports/{task_id}")
def get_import_task(task_id: int) -> dict[str, Any]:
    with connect() as conn:
        task = row_to_dict(conn.execute("SELECT * FROM import_tasks WHERE id=?", (task_id,)).fetchone())
    if not task:
        raise HTTPException(status_code=404, detail="IMPORT_TASK_NOT_FOUND")
    return envelope(task)


@router.get("/pages")
def list_pages(
    status: str | None = None,
    page_type: str | None = None,
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    clauses = []
    params: list[Any] = []
    if status:
        clauses.append("status=?")
        params.append(status)
    if page_type:
        clauses.append("page_type=?")
        params.append(page_type)
    if q:
        clauses.append("(url LIKE ? OR title LIKE ? OR body_text LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM pages{where} ORDER BY id DESC LIMIT ? OFFSET ?", [*params, limit, offset]).fetchall()
        total = conn.execute(f"SELECT COUNT(*) AS count FROM pages{where}", params).fetchone()["count"]
    return envelope({"items": [dict(row) for row in rows], "total": total, "limit": limit, "offset": offset})


@router.get("/pages/{page_id}")
def get_page(page_id: int) -> dict[str, Any]:
    with connect() as conn:
        page = row_to_dict(conn.execute("SELECT * FROM pages WHERE id=?", (page_id,)).fetchone())
        profile = row_to_dict(conn.execute("SELECT * FROM page_profiles WHERE page_id=?", (page_id,)).fetchone())
        links = [dict(row) for row in conn.execute("SELECT * FROM links WHERE source_url=? ORDER BY id", (page["url"],)).fetchall()] if page else []
    if not page:
        raise HTTPException(status_code=404, detail="PAGE_NOT_FOUND")
    if profile:
        profile["core_entities"] = json.loads(profile.get("core_entities") or "[]")
        profile["suggested_anchors"] = json.loads(profile.get("suggested_anchors") or "[]")
    return envelope({"page": page, "profile": profile, "links": links})


@router.post("/pages/{page_id}/crawl")
async def crawl_page(page_id: int) -> dict[str, Any]:
    with connect() as conn:
        await crawl_and_profile(conn, page_id)
        page = row_to_dict(conn.execute("SELECT * FROM pages WHERE id=?", (page_id,)).fetchone())
    return envelope(page)


@router.post("/pages/{page_id}/profile")
def profile_page(page_id: int) -> dict[str, Any]:
    with connect() as conn:
        profile = upsert_profile(conn, page_id)
    return envelope(profile)


@router.post("/pages/batch-profile")
def batch_profile(payload: dict[str, list[int]]) -> dict[str, Any]:
    page_ids = payload.get("page_ids", [])
    with connect() as conn:
        profiles = [{"page_id": page_id, **upsert_profile(conn, page_id)} for page_id in page_ids]
    return envelope({"items": profiles, "count": len(profiles)})


def recall_candidates(conn: sqlite3.Connection, source: dict[str, Any], top_k: int = 30) -> list[dict[str, Any]]:
    source_profile = conn.execute("SELECT * FROM page_profiles WHERE page_id=?", (source["id"],)).fetchone()
    source_entities = set(json.loads(source_profile["core_entities"] or "[]")) if source_profile else set()
    rows = conn.execute(
        """
        SELECT p.*, pp.l0_summary, pp.parent_topic, pp.core_entities, pp.target_priority
        FROM pages p JOIN page_profiles pp ON pp.page_id=p.id
        WHERE p.url != ? AND p.is_indexable=1 AND p.status='profiled'
        """,
        (source["url"],),
    ).fetchall()
    candidates = []
    for row in rows:
        item = dict(row)
        entities = set(json.loads(item.get("core_entities") or "[]"))
        entity_score = len(source_entities & entities) / max(1, len(source_entities | entities))
        topic_score = 1.0 if source_profile and item.get("parent_topic") == source_profile["parent_topic"] else 0.0
        business_score = (item.get("target_priority") or 3) / 5
        score = topic_score * 0.5 + entity_score * 0.3 + business_score * 0.2
        if source["page_type"] == "blog" and item.get("page_type") == "product":
            score *= 0.7
        candidates.append(
            {
                "page_id": item["id"],
                "url": item["url"],
                "page_type": item["page_type"],
                "title": item["title"],
                "l0_summary": item["l0_summary"],
                "recall_reason": "topic_match" if topic_score else "entity_overlap" if entity_score else "business_priority",
                "recall_score": round(score, 4),
            }
        )
    return sorted(candidates, key=lambda item: item["recall_score"], reverse=True)[:top_k]


def choose_anchor(source: dict[str, Any], target: dict[str, Any]) -> tuple[str, int, str] | None:
    paragraphs = json.loads(source.get("paragraphs_json") or "[]")
    target_terms = [target.get("title") or ""]
    for index, paragraph in enumerate(paragraphs):
        if index == 0:
            continue
        lower = paragraph.lower()
        for term in target_terms:
            term = term.strip().lower()
            if len(term) < 4:
                continue
            match = re.search(re.escape(term), lower)
            if match:
                return paragraph[match.start() : match.end()], index, paragraph
    for index, paragraph in enumerate(paragraphs[1:], start=1):
        significant = top_terms(paragraph, 8)
        for first, second in zip(significant, significant[1:]):
            phrase_match = re.search(rf"\b{re.escape(first)}\W+{re.escape(second)}\b", paragraph, re.I)
            if phrase_match:
                return paragraph[phrase_match.start() : phrase_match.end()], index, paragraph
        token_match = re.search(r"\b([A-Za-z][A-Za-z0-9-]{2,}\W+[A-Za-z][A-Za-z0-9-]{2,})\b", paragraph)
        if token_match:
            return paragraph[token_match.start() : token_match.end()].strip(), index, paragraph
    return None


def generate_for_source(conn: sqlite3.Connection, source_url: str, top_n: int, batch_id: str | None = None) -> list[dict[str, Any]]:
    source_url = normalize_url(source_url)
    source = row_to_dict(conn.execute("SELECT * FROM pages WHERE url=?", (source_url,)).fetchone())
    if not source:
        raise HTTPException(status_code=404, detail="PAGE_NOT_FOUND")
    if source["status"] != "profiled":
        raise HTTPException(status_code=400, detail="PAGE_NOT_PROFILED")
    candidates = recall_candidates(conn, source)
    filtered = []
    passed = []
    seen_targets: set[str] = set()
    for candidate in candidates:
        exists = conn.execute(
            "SELECT 1 FROM links WHERE source_url=? AND target_url=? LIMIT 1",
            (source["url"], candidate["url"]),
        ).fetchone()
        if exists:
            filtered.append({**candidate, "filter_reason": "existing_link"})
            continue
        if candidate["url"] in seen_targets:
            continue
        seen_targets.add(candidate["url"])
        passed.append(candidate)
        if len(passed) >= min(top_n, settings.recommendation_limit_per_page):
            break
    created = []
    for candidate in passed:
        anchor = choose_anchor(source, candidate)
        if not anchor:
            continue
        anchor_text, paragraph_index, paragraph = anchor
        if anchor_text not in paragraph:
            continue
        trace = {"candidates": candidates, "filtered": filtered, "selected": candidate}
        llm_call = conn.execute(
            """
            INSERT INTO llm_calls
                (purpose, model, prompt, response, tokens_in, tokens_out, duration_ms, success, related_entity, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                "recommendation",
                "deterministic-mvp",
                f"Recommend links from {source['url']} to {candidate['url']}",
                json.dumps({"target_url": candidate["url"], "anchor_text": anchor_text}, ensure_ascii=False),
                len((source.get("body_text") or "").split()),
                len(anchor_text.split()) + 5,
                0,
                f"page:{source['id']}",
                utc_now(),
            ),
        )
        cursor = conn.execute(
            """
            INSERT INTO recommendations
                (source_url, source_type, target_url, target_type, anchor_text, insert_position,
                 insert_paragraph, confidence, reason, trace_json, status, batch_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            (
                source["url"],
                source["page_type"],
                candidate["url"],
                candidate["page_type"],
                anchor_text,
                f"Paragraph {paragraph_index}",
                paragraph,
                min(0.95, max(0.55, candidate["recall_score"])),
                f"{candidate['recall_reason']} with deterministic anchor validation",
                json.dumps(trace, ensure_ascii=False),
                batch_id,
                utc_now(),
            ),
        )
        conn.execute("UPDATE recommendations SET llm_call_id=? WHERE id=?", (llm_call.lastrowid, cursor.lastrowid))
        created.append(row_to_dict(conn.execute("SELECT * FROM recommendations WHERE id=?", (cursor.lastrowid,)).fetchone()))
    return [item for item in created if item]


@router.post("/recommendations/generate")
def generate_recommendations(request: GenerateRequest) -> dict[str, Any]:
    with connect() as conn:
        items = generate_for_source(conn, request.source_url, request.top_n)
    return envelope(items)


@router.post("/recommendations/batch")
def batch_recommendations(request: BatchGenerateRequest) -> dict[str, Any]:
    batch_id = f"batch_{uuid.uuid4().hex[:10]}"
    created = []
    with connect() as conn:
        for source_url in request.source_urls:
            created.extend(generate_for_source(conn, source_url, request.top_n, batch_id=batch_id))
    return envelope({"batch_id": batch_id, "created": len(created), "items": created})


@router.get("/recommendations")
def list_recommendations(
    status: str | None = None,
    source_url: str | None = None,
    batch_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    clauses = []
    params: list[Any] = []
    if status:
        clauses.append("status=?")
        params.append(status)
    if source_url:
        clauses.append("source_url=?")
        params.append(normalize_url(source_url))
    if batch_id:
        clauses.append("batch_id=?")
        params.append(batch_id)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM recommendations{where} ORDER BY id DESC LIMIT ? OFFSET ?", [*params, limit, offset]).fetchall()
        total = conn.execute(f"SELECT COUNT(*) AS count FROM recommendations{where}", params).fetchone()["count"]
    return envelope({"items": [dict(row) for row in rows], "total": total, "limit": limit, "offset": offset})


@router.get("/recommendations/{recommendation_id}")
def get_recommendation(recommendation_id: int) -> dict[str, Any]:
    with connect() as conn:
        rec = row_to_dict(conn.execute("SELECT * FROM recommendations WHERE id=?", (recommendation_id,)).fetchone())
    if not rec:
        raise HTTPException(status_code=404, detail="RECOMMENDATION_NOT_FOUND")
    rec["trace"] = json.loads(rec.get("trace_json") or "{}")
    return envelope(rec)


@router.post("/recommendations/{recommendation_id}/review")
def review_recommendation(recommendation_id: int, request: ReviewRequest) -> dict[str, Any]:
    if request.decision not in {"approved", "rejected", "edited_approved"}:
        raise HTTPException(status_code=400, detail="INVALID_DECISION")
    if request.decision == "rejected" and not request.rejection_reason:
        raise HTTPException(status_code=400, detail="REJECTION_REASON_REQUIRED")
    if request.decision == "edited_approved" and not any([request.edited_anchor_text, request.edited_target_url, request.edited_insert_position]):
        raise HTTPException(status_code=400, detail="EDIT_REQUIRED")
    with connect() as conn:
        rec = conn.execute("SELECT * FROM recommendations WHERE id=?", (recommendation_id,)).fetchone()
        if not rec:
            raise HTTPException(status_code=404, detail="RECOMMENDATION_NOT_FOUND")
        conn.execute("UPDATE recommendations SET status=? WHERE id=?", (request.decision, recommendation_id))
        cursor = conn.execute(
            """
            INSERT INTO reviews
                (recommendation_id, decision, reviewer, reviewer_note, rejection_reason,
                 edited_anchor_text, edited_target_url, edited_insert_position, reviewed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recommendation_id,
                request.decision,
                request.reviewer,
                request.reviewer_note,
                request.rejection_reason,
                request.edited_anchor_text,
                request.edited_target_url,
                request.edited_insert_position,
                utc_now(),
            ),
        )
        review = row_to_dict(conn.execute("SELECT * FROM reviews WHERE id=?", (cursor.lastrowid,)).fetchone())
    return envelope(review)


@router.get("/reviews/stats")
def review_stats() -> dict[str, Any]:
    with connect() as conn:
        counts = {row["status"]: row["count"] for row in conn.execute("SELECT status, COUNT(*) AS count FROM recommendations GROUP BY status")}
    approved = counts.get("approved", 0) + counts.get("edited_approved", 0)
    reviewed = approved + counts.get("rejected", 0)
    return envelope(
        {
            "pending": counts.get("pending", 0),
            "approved": counts.get("approved", 0),
            "rejected": counts.get("rejected", 0),
            "edited": counts.get("edited_approved", 0),
            "approval_rate": round(approved / reviewed, 4) if reviewed else 0,
        }
    )


@router.get("/reviews")
def list_reviews(decision: str | None = None) -> dict[str, Any]:
    with connect() as conn:
        if decision:
            rows = conn.execute("SELECT * FROM reviews WHERE decision=? ORDER BY id DESC", (decision,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM reviews ORDER BY id DESC").fetchall()
    return envelope([dict(row) for row in rows])


@router.get("/exports/recommendations.csv")
def export_recommendations_csv(status: str = "approved") -> Response:
    statuses = ["approved", "edited_approved"] if status == "approved" else [status]
    placeholders = ",".join("?" for _ in statuses)
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT r.*, rv.decision, rv.reviewed_at, rv.edited_anchor_text, rv.edited_target_url, rv.edited_insert_position
            FROM recommendations r
            LEFT JOIN reviews rv ON rv.recommendation_id=r.id
            WHERE r.status IN ({placeholders})
            ORDER BY r.id
            """,
            statuses,
        ).fetchall()
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["source_url", "target_url", "anchor_text", "insert_position", "decision", "reviewed_at"])
    writer.writeheader()
    for row in rows:
        item = dict(row)
        writer.writerow(
            {
                "source_url": item["source_url"],
                "target_url": item.get("edited_target_url") or item["target_url"],
                "anchor_text": item.get("edited_anchor_text") or item["anchor_text"],
                "insert_position": item.get("edited_insert_position") or item["insert_position"],
                "decision": item.get("decision") or item["status"],
                "reviewed_at": item.get("reviewed_at") or "",
            }
        )
    return Response(output.getvalue(), media_type="text/csv; charset=utf-8")


@router.get("/exports/recommendations.json")
def export_recommendations_json(status: str = "approved") -> dict[str, Any]:
    statuses = ["approved", "edited_approved"] if status == "approved" else [status]
    placeholders = ",".join("?" for _ in statuses)
    with connect() as conn:
        rows = conn.execute(f"SELECT * FROM recommendations WHERE status IN ({placeholders}) ORDER BY id", statuses).fetchall()
    return envelope([dict(row) for row in rows])


@router.get("/health")
def health() -> dict[str, Any]:
    with connect() as conn:
        conn.execute("SELECT 1")
    return envelope({"db": "ok", "llm": "not_configured_for_deterministic_mvp", "time": utc_now()})


@router.get("/stats")
def stats() -> dict[str, Any]:
    with connect() as conn:
        pages = conn.execute("SELECT COUNT(*) AS count FROM pages").fetchone()["count"]
        profiled = conn.execute("SELECT COUNT(*) AS count FROM pages WHERE status='profiled'").fetchone()["count"]
        recs = conn.execute("SELECT COUNT(*) AS count FROM recommendations").fetchone()["count"]
        approved = conn.execute("SELECT COUNT(*) AS count FROM recommendations WHERE status IN ('approved','edited_approved')").fetchone()["count"]
    return envelope(
        {
            "pages": pages,
            "profiled_pages": profiled,
            "profile_rate": round(profiled / pages, 4) if pages else 0,
            "recommendations": recs,
            "approved_recommendations": approved,
            "approval_rate": round(approved / recs, 4) if recs else 0,
        }
    )
